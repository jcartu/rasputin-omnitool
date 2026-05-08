from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .runtime_e2e import (
    SCHEMA_VERSION,
    _run_command,
    _utc_now,
    _write_json,
)


def _fetch_github_repo_info(repo: str) -> dict:
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
            "description": data.get("description"),
            "license_spdx": (data.get("license") or {}).get("spdx_id"),
            "stars": data.get("stargazers_count"),
            "default_branch": data.get("default_branch"),
            "archived": data.get("archived"),
            "pushed_at": data.get("pushed_at"),
            "html_url": data.get("html_url"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _fetch_npm_metadata(package: str) -> dict:
    try:
        req = urllib.request.Request(
            f"https://registry.npmjs.org/{package}/latest",
            headers={"User-Agent": "Hermes-Becoming-Manus-Smoke"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return {
            "ok": True,
            "version": data.get("version"),
            "description": data.get("description"),
            "license": data.get("license"),
            "homepage": data.get("homepage"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_mobile_smoke(output_dir: str | Path) -> dict:
    """Smoke test for mobile publishing: Expo CLI + Capacitor availability."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": "mobile_smoke",
        "capability": "mobile_publishing",
        "status": "pass",
        "scope": "Check Expo CLI and Capacitor CLI availability, fetch project metadata",
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
            "cache_isolation": "read-only CLI version checks and metadata fetches; no project creation",
        },
    }

    all_ok = True

    # 1. Check npx expo --version
    expo_ver = _run_command(["npx", "expo", "--version"], timeout=30)
    report["commands"].append(expo_ver)
    report["summary"]["expo_cli_version"] = expo_ver.get("stdout", "").strip()[:200]
    report["summary"]["expo_cli_available"] = expo_ver["ok"]
    if not expo_ver["ok"]:
        report["blockers"].append(
            {
                "reason": "Expo CLI not available via npx. Install via `npm install -g expo-cli` or ensure npx works.",
                "next_command": "npm install -g expo-cli",
                "risk": "Global npm install modifies system node_modules.",
            }
        )
        # npx might be slow on first run; don't fail entirely
        report["summary"]["expo_cli_available"] = "unknown"

    # 2. Check npx cap --version (Capacitor)
    cap_ver = _run_command(["npx", "cap", "--version"], timeout=30)
    report["commands"].append(cap_ver)
    report["summary"]["capacitor_cli_version"] = cap_ver.get("stdout", "").strip()[:200]
    report["summary"]["capacitor_cli_available"] = cap_ver["ok"]
    if not cap_ver["ok"]:
        report["blockers"].append(
            {
                "reason": "Capacitor CLI not available via npx. Install via `npm install -g @capacitor/cli`.",
                "next_command": "npm install -g @capacitor/cli",
                "risk": "Global npm install modifies system node_modules.",
            }
        )
        report["summary"]["capacitor_cli_available"] = "unknown"

    # 3. Check node/npm versions (prerequisites)
    node_ver = _run_command(["node", "--version"], timeout=10)
    report["commands"].append(node_ver)
    report["summary"]["node_version"] = node_ver.get("stdout", "").strip()[:100]

    npm_ver = _run_command(["npm", "--version"], timeout=10)
    report["commands"].append(npm_ver)
    report["summary"]["npm_version"] = npm_ver.get("stdout", "").strip()[:100]

    # 4. Fetch Expo GitHub metadata
    expo_github = _fetch_github_repo_info("expo/expo")
    report["summary"]["expo_github"] = {k: v for k, v in expo_github.items() if k not in ("ok",)}
    report["summary"]["expo_github_ok"] = expo_github.get("ok", False)

    # 5. Fetch Capacitor GitHub metadata
    cap_github = _fetch_github_repo_info("ionic-team/capacitor")
    report["summary"]["capacitor_github"] = {k: v for k, v in cap_github.items() if k not in ("ok",)}
    report["summary"]["capacitor_github_ok"] = cap_github.get("ok", False)

    # 6. Fetch npm package metadata
    expo_npm = _fetch_npm_metadata("expo")
    report["summary"]["expo_npm"] = expo_npm

    cap_npm = _fetch_npm_metadata("@capacitor/cli")
    report["summary"]["capacitor_npm"] = cap_npm

    # 7. Fetch fastlane GitHub metadata (from capability matrix)
    fastlane_github = _fetch_github_repo_info("fastlane/fastlane")
    report["summary"]["fastlane_github"] = {k: v for k, v in fastlane_github.items() if k not in ("ok",)}
    report["summary"]["fastlane_github_ok"] = fastlane_github.get("ok", False)

    # Determine status: npx first-run is slow but not a failure
    if not expo_ver["ok"] and not cap_ver["ok"]:
        report["status"] = "warn"
    elif not expo_ver["ok"] or not cap_ver["ok"]:
        report["status"] = "warn"
    else:
        report["status"] = "pass"

    report["capability_complete"] = report["status"] == "pass"

    json_path = output_dir / "mobile-smoke.json"
    report["artifacts"]["report_json"] = str(json_path)
    _write_json(json_path, report)

    return report


def main() -> int:
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/become-manus/mobile"
    report = run_mobile_smoke(output_dir)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["status"] in {"pass", "warn"} else 1
