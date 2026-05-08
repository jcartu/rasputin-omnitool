from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

import yaml


def _run(cmd: list[str], timeout: int = 30) -> dict:
    try:
        result = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": result.stdout.strip()[-4000:],
            "stderr": result.stderr.strip()[-4000:],
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        return {"ok": False, "returncode": None, "stdout": (exc.stdout or "")[-4000:], "stderr": f"timeout after {timeout}s"}


def _check_command(name: str, command: list[str]) -> dict:
    result = _run(command)
    return {"name": name, "status": "pass" if result["ok"] else "fail", "details": result}


def _mcp_configured(name: str, config_path: Path | None = None) -> bool:
    config_path = config_path or Path.home() / ".hermes" / "config.yaml"
    if not config_path.exists():
        return False
    try:
        data = yaml.safe_load(config_path.read_text()) or {}
    except Exception:
        return False
    return name in (data.get("mcp_servers") or {})


def _overall(checks: Iterable[dict]) -> str:
    statuses = [c["status"] for c in checks]
    if any(s == "fail" for s in statuses):
        return "fail"
    if any(s == "warn" for s in statuses):
        return "warn"
    return "pass"


def run_smoke_checks(output_dir: str | Path, run_external: bool = True) -> dict:
    """Run a safe local readiness smoke check for Manus-like capabilities.

    `run_external=False` avoids commands that can download packages or start MCP
    subprocesses, making it suitable for unit tests.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    checks = [
        _check_command("python", ["python", "--version"]),
        _check_command("node", ["node", "--version"]),
        _check_command("npm", ["npm", "--version"]),
        _check_command("hermes", ["hermes", "--version"]),
        _check_command("docker", ["docker", "--version"]),
    ]

    configured = _mcp_configured("playwright")
    checks.append({
        "name": "playwright_mcp_config",
        "status": "pass" if configured else "warn",
        "details": {"configured": configured, "config_path": str(Path.home() / ".hermes" / "config.yaml")},
    })

    if run_external and configured:
        result = _run(["hermes", "mcp", "test", "playwright"], timeout=180)
        checks.append({
            "name": "playwright_mcp_connectivity",
            "status": "pass" if result["ok"] and "Tools discovered" in result["stdout"] else "fail",
            "details": result,
        })

    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": _overall(checks),
        "checks": checks,
        "paths": {
            "cwd": str(Path.cwd()),
            "hermes": shutil.which("hermes"),
            "docker": shutil.which("docker"),
            "node": shutil.which("node"),
        },
    }
    (output_dir / "become-manus-smoke.json").write_text(json.dumps(report, indent=2) + "\n")
    return report
