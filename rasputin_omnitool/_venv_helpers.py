from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

SCHEMA_VERSION = 1
DEFAULT_INSTALL_TIMEOUT_SECONDS = 600
DEFAULT_RUN_TIMEOUT_SECONDS = 180


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(text: str | bytes | None, limit: int = 8000) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _isolated_env(output_dir: Path) -> dict[str, str]:
    """Return an environment that keeps package/runtime caches under output_dir."""
    cache_dir = output_dir / "cache"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_CACHE_DIR": str(output_dir / "pip-cache"),
            "XDG_CACHE_HOME": str(cache_dir),
            "HOME": str(output_dir / "home"),
            "HF_HOME": str(cache_dir / "huggingface"),
            "TRANSFORMERS_CACHE": str(cache_dir / "huggingface" / "transformers"),
            "DOCLING_CACHE_DIR": str(cache_dir / "docling"),
            "CRAWL4AI_HOME": str(output_dir / "crawl4ai-home"),
            "PLAYWRIGHT_BROWSERS_PATH": str(output_dir / "playwright-browsers"),
            "NPM_CONFIG_CACHE": str(output_dir / "npm-cache"),
        }
    )
    for path in [
        cache_dir,
        Path(env["PIP_CACHE_DIR"]),
        Path(env["HOME"]),
        Path(env["HF_HOME"]),
        Path(env["CRAWL4AI_HOME"]),
        Path(env["PLAYWRIGHT_BROWSERS_PATH"]),
        Path(env["NPM_CONFIG_CACHE"]),
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return env


def _run_command(
    command: Sequence[str | Path],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_RUN_TIMEOUT_SECONDS,
) -> dict:
    command_list = [str(item) for item in command]
    try:
        result = subprocess.run(
            command_list,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": command_list,
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": _trim(result.stdout),
            "stderr": _trim(result.stderr),
            "timeout_seconds": timeout,
        }
    except FileNotFoundError as exc:
        return {
            "command": command_list,
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"FileNotFoundError: {exc}",
            "timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command_list,
            "ok": False,
            "returncode": None,
            "stdout": _trim(exc.stdout),
            "stderr": f"timeout after {timeout}s; {_trim(exc.stderr)}".strip(),
            "timeout_seconds": timeout,
        }


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_disposable_venv(output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    venv_dir = output_dir / ".venv"
    python_path = _venv_python(venv_dir)
    commands: list[dict] = []
    env = _isolated_env(output_dir)
    if not python_path.exists():
        commands.append(_run_command([sys.executable, "-m", "venv", str(venv_dir)], env=env, timeout=180))
    if python_path.exists():
        pip_check = _run_command([python_path, "-m", "pip", "--version"], env=env, timeout=60)
        commands.append(pip_check)
        if not pip_check["ok"]:
            commands.append(_run_command([python_path, "-m", "ensurepip", "--upgrade"], env=env, timeout=180))
            commands.append(_run_command([python_path, "-m", "pip", "--version"], env=env, timeout=60))
    ok = python_path.exists() and bool(commands) and commands[-1].get("ok")
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "status": "pass" if ok else "fail",
        "venv_dir": str(venv_dir),
        "python": str(python_path),
        "commands": commands,
    }


def _import_check(venv_python: Path, import_name: str, env: dict[str, str]) -> dict:
    return _run_command(
        [venv_python, "-c", f"import {import_name}; print(getattr({import_name}, '__version__', 'import-ok'))"],
        env=env,
        timeout=60,
    )


def _install_package_if_needed(
    *,
    venv_python: Path,
    output_dir: Path,
    package: str,
    import_name: str,
    timeout: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> tuple[bool, list[dict]]:
    env = _isolated_env(output_dir)
    commands: list[dict] = []
    before = _import_check(venv_python, import_name, env)
    commands.append(before)
    if before["ok"]:
        return True, commands
    install = _run_command(
        [venv_python, "-m", "pip", "install", "--no-input", "--no-cache-dir", package],
        env=env,
        timeout=timeout,
    )
    commands.append(install)
    if not install["ok"]:
        return False, commands
    after = _import_check(venv_python, import_name, env)
    commands.append(after)
    return after["ok"], commands
