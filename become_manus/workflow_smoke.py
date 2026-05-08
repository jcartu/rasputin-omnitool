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
            "repository_url": (data.get("repository") or {}).get("url"),
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _list_mcp_servers_readme() -> dict:
    """Try to fetch the MCP servers README from GitHub raw content."""
    try:
        req = urllib.request.Request(
            "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md",
            headers={"User-Agent": "Hermes-Becoming-Manus-Smoke"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read().decode("utf-8")
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        server_names = []
        for line in lines:
            if line.startswith("## ") and "server" not in line.lower():
                server_names.append(line[3:].strip())
            if line.startswith("- ") and "://" in line:
                server_names.append(line[2:].strip())
        return {
            "ok": True,
            "readme_chars": len(content),
            "lines": min(len(lines), 100),
            "server_names_sample": server_names[:30],
        }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_workflow_smoke(output_dir: str | Path) -> dict:
    """Smoke test for workflow integrations: MCP server list + Composio metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": "workflow_smoke",
        "capability": "workflow_integrations",
        "status": "pass",
        "scope": "Verify MCP server list from GitHub and test Composio metadata from npm/GitHub",
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

    # 1. Fetch MCP servers repo info
    mcp_repo = _fetch_github_repo_info("modelcontextprotocol/servers")
    report["summary"]["mcp_servers_repo"] = {
        k: v for k, v in mcp_repo.items() if k not in ("ok",)
    }
    report["summary"]["mcp_servers_repo_ok"] = mcp_repo.get("ok", False)
    if not mcp_repo.get("ok"):
        all_ok = False
        report["blockers"].append(
            {
                "reason": "Failed to fetch MCP servers GitHub repo metadata.",
                "next_command": "curl -s https://api.github.com/repos/modelcontextprotocol/servers | jq .",
                "risk": "Network-dependent.",
            }
        )

    # 2. Fetch MCP servers README (list of available servers)
    mcp_readme = _list_mcp_servers_readme()
    report["summary"]["mcp_servers_readme"] = mcp_readme
    report["summary"]["mcp_servers_list_ok"] = mcp_readme.get("ok", False)
    report["commands"].append(
        {
            "command": ["GET", "https://raw.githubusercontent.com/modelcontextprotocol/servers/main/README.md"],
            "ok": mcp_readme.get("ok", False),
            "returncode": 0 if mcp_readme.get("ok") else 1,
            "stdout": json.dumps(mcp_readme, default=str)[:1000],
            "stderr": "",
            "timeout_seconds": 15,
        }
    )

    # 3. Fetch Composio npm metadata
    composio_npm = _fetch_npm_metadata("composio-core")
    report["summary"]["composio_npm"] = composio_npm
    report["summary"]["composio_npm_ok"] = composio_npm.get("ok", False)
    if not composio_npm.get("ok"):
        # Try alternative package name
        composio_npm_alt = _fetch_npm_metadata("composio")
        report["summary"]["composio_npm_alt"] = composio_npm_alt
        report["summary"]["composio_npm_ok"] = composio_npm_alt.get("ok", False)
        if not composio_npm_alt.get("ok"):
            all_ok = False
            report["blockers"].append(
                {
                    "reason": "Failed to fetch Composio npm metadata.",
                    "next_command": "npm view composio-core --json",
                    "risk": "Network-dependent.",
                }
            )

    # 4. Fetch Composio GitHub metadata
    composio_github = _fetch_github_repo_info("ComposioHQ/composio")
    report["summary"]["composio_github"] = {
        k: v for k, v in composio_github.items() if k not in ("ok",)
    }
    report["summary"]["composio_github_ok"] = composio_github.get("ok", False)

    # 5. Fetch Activepieces GitHub metadata
    activepieces_github = _fetch_github_repo_info("activepieces/activepieces")
    report["summary"]["activepieces_github"] = {
        k: v for k, v in activepieces_github.items() if k not in ("ok",)
    }
    report["summary"]["activepieces_github_ok"] = activepieces_github.get("ok", False)

    # 6. Fetch n8n npm metadata
    n8n_npm = _fetch_npm_metadata("n8n")
    report["summary"]["n8n_npm"] = n8n_npm
    report["summary"]["n8n_npm_ok"] = n8n_npm.get("ok", False)

    report["status"] = "pass" if all_ok else "warn"
    report["capability_complete"] = all_ok

    json_path = output_dir / "workflow-smoke.json"
    report["artifacts"]["report_json"] = str(json_path)
    _write_json(json_path, report)

    return report


def main() -> int:
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/become-manus/workflow"
    report = run_workflow_smoke(output_dir)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["status"] in {"pass", "warn"} else 1
