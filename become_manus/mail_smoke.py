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


def _check_hermes_email_config() -> dict:
    """Check if Hermes email gateway configuration exists."""
    result: dict = {"ok": False, "config_path": None, "details": {}}
    config_candidates = [
        Path.home() / ".hermes" / "config.yaml",
        Path.home() / ".hermes" / "email.yaml",
        Path.home() / ".hermes" / "gateway" / "email.yaml",
        Path("/etc/hermes/config.yaml"),
    ]
    for cfg in config_candidates:
        if cfg.exists():
            result["ok"] = True
            result["config_path"] = str(cfg)
            try:
                content = cfg.read_text()[:2000]
                result["details"]["file_exists"] = True
                result["details"]["size_bytes"] = len(content)
                # Check for email-related keys without exposing credentials
                has_smtp = "smtp" in content.lower()
                has_imap = "imap" in content.lower()
                has_email = "email" in content.lower() or "mail" in content.lower()
                result["details"]["has_smtp_config"] = has_smtp
                result["details"]["has_imap_config"] = has_imap
                result["details"]["has_email_config"] = has_email
            except Exception as exc:
                result["details"]["read_error"] = str(exc)
            break
    return result


def run_mail_smoke(output_dir: str | Path) -> dict:
    """Smoke test for mail agent: Himalaya CLI + Hermes email gateway config."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": "mail_smoke",
        "capability": "mail_agent",
        "status": "pass",
        "scope": "Check Himalaya CLI availability and test Hermes email gateway configuration",
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
            "cache_isolation": "read-only checks; no email sent or received",
        },
    }

    all_ok = True

    # 1. Check himalaya --version
    himalaya_ver = _run_command(["himalaya", "--version"], timeout=10)
    report["commands"].append(himalaya_ver)
    report["summary"]["himalaya_version"] = himalaya_ver.get("stdout", "").strip()[:200]
    report["summary"]["himalaya_available"] = himalaya_ver["ok"]
    if not himalaya_ver["ok"]:
        # Try cargo install as next step
        report["blockers"].append(
            {
                "reason": "Himalaya CLI not found. Install via `cargo install himalaya` or your package manager.",
                "next_command": "cargo install himalaya",
                "risk": "Rust compilation required; may take several minutes.",
            }
        )
        all_ok = False

    # 2. Check himalaya list accounts (non-destructive)
    if himalaya_ver["ok"]:
        himalaya_list = _run_command(["himalaya", "account", "list"], timeout=10)
        report["commands"].append(himalaya_list)
        report["summary"]["himalaya_accounts_configured"] = himalaya_list["ok"]
        report["summary"]["himalaya_accounts_output"] = himalaya_list.get("stdout", "").strip()[:500]
        if not himalaya_list["ok"]:
            # No accounts configured is not a failure, just informational
            report["summary"]["himalaya_accounts_configured"] = "no_accounts"

    # 3. Check Hermes email gateway config
    hermes_email = _check_hermes_email_config()
    report["summary"]["hermes_email_config"] = hermes_email
    report["summary"]["hermes_email_configured"] = hermes_email.get("ok", False)
    if not hermes_email["ok"]:
        report["blockers"].append(
            {
                "reason": "No Hermes email gateway configuration found.",
                "next_command": "Configure email settings in ~/.hermes/config.yaml or use Hermes built-in email capability.",
                "risk": "None; configuration step.",
            }
        )
        # This is not a hard failure since Hermes built-in email is the preferred option
        report["summary"]["hermes_email_configured"] = "not_configured_but_optional"

    # 4. Check for common SMTP/IMAP utilities
    for cmd_name, cmd_args in [
        ("openssl_s_client", ["openssl", "s_client", "-version"]),
        ("curl_smtp", ["curl", "--version"]),
    ]:
        tool_check = _run_command(cmd_args, timeout=10)
        report["commands"].append(tool_check)
        report["summary"][f"{cmd_name}_available"] = tool_check["ok"]

    # 5. Fetch Himalaya GitHub metadata
    himalaya_github = _fetch_github_repo_info("pimalaya/himalaya")
    report["summary"]["himalaya_github"] = {k: v for k, v in himalaya_github.items() if k not in ("ok",)}
    report["summary"]["himalaya_github_ok"] = himalaya_github.get("ok", False)

    report["status"] = "pass" if all_ok else "warn"
    report["capability_complete"] = all_ok

    json_path = output_dir / "mail-smoke.json"
    report["artifacts"]["report_json"] = str(json_path)
    _write_json(json_path, report)

    return report


def main() -> int:
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/become-manus/mail"
    report = run_mail_smoke(output_dir)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["status"] in {"pass", "warn"} else 1
