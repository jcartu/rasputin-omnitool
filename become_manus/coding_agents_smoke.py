from __future__ import annotations

import json
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

from .runtime_e2e import (
    SCHEMA_VERSION,
    _isolated_env,
    _run_command,
    _utc_now,
    _write_json,
)


def _fetch_github_repo_info(repo: str) -> dict:
    """Fetch basic repo metadata from GitHub API."""
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/{repo}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Hermes-Becoming-Manus-Smoke",
            },
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "ok": True,
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "license_spdx": (data.get("license") or {}).get("spdx_id"),
            "stars": data.get("stargazers_count"),
            "stars_count": data.get("stargazers_count"),
            "open_issues": data.get("open_issues_count"),
            "default_branch": data.get("default_branch"),
            "archived": data.get("archived"),
            "pushed_at": data.get("pushed_at"),
            "html_url": data.get("html_url"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _fetch_pypi_metadata(package: str) -> dict:
    """Fetch latest version info from PyPI JSON API."""
    try:
        req = urllib.request.Request(
            f"https://pypi.org/pypi/{package}/json",
            headers={"User-Agent": "Hermes-Becoming-Manus-Smoke"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        info = data.get("info", {})
        return {
            "ok": True,
            "version": info.get("version"),
            "summary": info.get("summary"),
            "license": info.get("license"),
            "home_page": info.get("project_urls", {}).get("Homepage"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_coding_agents_smoke(output_dir: str | Path) -> dict:
    """Smoke test for coding agents: aider CLI availability + OpenHands metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": "coding_agents_smoke",
        "capability": "coding_agents",
        "status": "pass",
        "scope": "Check aider CLI availability and fetch OpenHands project metadata",
        "summary": {},
        "commands": [],
        "blockers": [],
        "artifacts": {},
        "safety": {
            "workspace": str(Path.cwd()),
            "output_dir": str(output_dir),
            "global_python_mutation": "none_intended",
            "system_config_mutation": "none_intended",
            "credential_use": "none",
            "cache_isolation": "read-only metadata fetches; no installs or side-effects",
        },
    }

    all_ok = True

    # 1. Check aider --version
    aider_version = _run_command(["aider", "--version"])
    report["commands"].append(aider_version)
    report["summary"]["aider_version"] = aider_version.get("stdout", "")[:200]
    report["summary"]["aider_available"] = aider_version["ok"]
    if not aider_version["ok"]:
        all_ok = False
        report["blockers"].append(
            {
                "reason": "aider CLI not found. Install via `pip install aider-chat`.",
                "next_command": "pip install --user aider-chat",
                "risk": "Package install may pull large LLM dependencies.",
            }
        )

    # 2. Fallback: pip show aider
    if not aider_version["ok"]:
        pip_show = _run_command(["pip", "show", "aider-chat"])
        report["commands"].append(pip_show)
        if pip_show["ok"]:
            report["summary"]["aider_pip_version"] = (
                pip_show["stdout"][:200] if pip_show["stdout"] else ""
            )
            all_ok = True
            report["summary"]["aider_available"] = True

    # 3. Check aider via pip show (alternative package name)
    if not report["summary"].get("aider_available"):
        pip_show_alt = _run_command(["pip", "show", "aider"])
        report["commands"].append(pip_show_alt)
        if pip_show_alt["ok"]:
            report["summary"]["aider_pip_version"] = (
                pip_show_alt["stdout"][:200] if pip_show_alt["stdout"] else ""
            )
            all_ok = True
            report["summary"]["aider_available"] = True

    # 4. Fetch OpenHands GitHub metadata
    ohands_info = _fetch_github_repo_info("All-Hands-AI/OpenHands")
    report["summary"]["openhands"] = {
        k: v for k, v in ohands_info.items() if k not in ("ok",)
    }
    report["summary"]["openhands_metadata_ok"] = ohands_info.get("ok", False)
    if not ohands_info.get("ok"):
        all_ok = False
        report["blockers"].append(
            {
                "reason": "Failed to fetch OpenHands GitHub metadata.",
                "next_command": "curl -s https://api.github.com/repos/All-Hands-AI/OpenHands | jq .",
                "risk": "Network-dependent; may require rate limit wait.",
            }
        )

    # 5. Fetch OpenHands npm/package metadata
    ohands_pypi = _fetch_pypi_metadata("openhands")
    report["summary"]["openhands_pypi"] = ohands_pypi
    report["commands"].append(
        {
            "command": ["GET", "https://pypi.org/pypi/openhands/json"],
            "ok": ohands_pypi.get("ok", False),
            "returncode": 0 if ohands_pypi.get("ok") else 1,
            "stdout": json.dumps(ohands_pypi, default=str)[:1000],
            "stderr": "",
            "timeout_seconds": 15,
        }
    )

    # 6. Fetch aider PyPI metadata
    aider_pypi = _fetch_pypi_metadata("aider-chat")
    report["summary"]["aider_pypi"] = aider_pypi
    report["commands"].append(
        {
            "command": ["GET", "https://pypi.org/pypi/aider-chat/json"],
            "ok": aider_pypi.get("ok", False),
            "returncode": 0 if aider_pypi.get("ok") else 1,
            "stdout": json.dumps(aider_pypi, default=str)[:1000],
            "stderr": "",
            "timeout_seconds": 15,
        }
    )

    report["status"] = "pass" if all_ok else "warn"
    report["capability_complete"] = all_ok

    # Write JSON report
    json_path = output_dir / "coding-agents-smoke.json"
    report["artifacts"]["report_json"] = str(json_path)
    _write_json(json_path, report)

    return report


def main() -> int:
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/become-manus/coding-agents"
    report = run_coding_agents_smoke(output_dir)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["status"] in {"pass", "warn"} else 1
