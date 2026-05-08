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


def run_analytics_smoke(output_dir: str | Path) -> dict:
    """Smoke test for analytics: Umami docker pull + PostHog docker image metadata."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report: dict = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": "analytics_smoke",
        "capability": "analytics",
        "status": "pass",
        "scope": "Check if Umami and PostHog docker images are available, fetch project metadata",
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
            "cache_isolation": "docker image inspects are read-only; docker pull downloads to local image store",
        },
    }

    all_ok = True

    # 1. Check docker availability
    docker_ver = _run_command(["docker", "--version"], timeout=10)
    report["commands"].append(docker_ver)
    report["summary"]["docker_version"] = docker_ver.get("stdout", "").strip()[:200]
    report["summary"]["docker_available"] = docker_ver["ok"]
    if not docker_ver["ok"]:
        report["blockers"].append(
            {
                "reason": "Docker is not available. Install Docker Engine.",
                "next_command": "sudo pacman -S docker && sudo systemctl start docker",
                "risk": "System package install.",
            }
        )
        report["status"] = "warn"
        all_ok = False

    # 2. Check docker daemon is running
    if docker_ver["ok"]:
        docker_info = _run_command(["docker", "info"], timeout=15)
        report["commands"].append(docker_info)
        report["summary"]["docker_daemon_running"] = docker_info["ok"]

        # 3. Inspect Umami image (try without pulling first)
        umami_inspect = _run_command(
            ["docker", "inspect", "ghcr.io/umami-software/umami:latest"],
            timeout=15,
        )
        report["commands"].append(umami_inspect)
        report["summary"]["umami_image_local"] = umami_inspect["ok"]

        if not umami_inspect["ok"]:
            # Try to pull
            umami_pull = _run_command(
                ["docker", "pull", "ghcr.io/umami-software/umami:latest"],
                timeout=120,
            )
            report["commands"].append(umami_pull)
            report["summary"]["umami_pull_ok"] = umami_pull["ok"]
            report["summary"]["umami_pull_output"] = umami_pull.get("stdout", "")[:500]

            if not umami_pull["ok"]:
                all_ok = False
                report["blockers"].append(
                    {
                        "reason": "Failed to pull Umami Docker image.",
                        "next_command": "docker pull ghcr.io/umami-software/umami:latest",
                        "risk": "Downloads ~100MB Docker image.",
                    }
                )
        else:
            report["summary"]["umami_image_local"] = True

        # 4. Inspect PostHog image
        posthog_inspect = _run_command(
            ["docker", "inspect", "posthog/posthog:latest"],
            timeout=15,
        )
        report["commands"].append(posthog_inspect)
        report["summary"]["posthog_image_local"] = posthog_inspect["ok"]

        if not posthog_inspect["ok"]:
            posthog_pull = _run_command(
                ["docker", "pull", "posthog/posthog:latest"],
                timeout=120,
            )
            report["commands"].append(posthog_pull)
            report["summary"]["posthog_pull_ok"] = posthog_pull["ok"]
            report["summary"]["posthog_pull_output"] = posthog_pull.get("stdout", "")[:500]

            if not posthog_pull["ok"]:
                all_ok = False
                report["blockers"].append(
                    {
                        "reason": "Failed to pull PostHog Docker image.",
                        "next_command": "docker pull posthog/posthog:latest",
                        "risk": "Downloads large Docker image.",
                    }
                )
        else:
            report["summary"]["posthog_image_local"] = True

        # 5. Get image sizes if available
        for img_name, label in [
            ("ghcr.io/umami-software/umami:latest", "umami"),
            ("posthog/posthog:latest", "posthog"),
        ]:
            inspect_cmd = _run_command(
                ["docker", "image", "inspect", img_name, "--format", "{{.Size}}"],
                timeout=10,
            )
            report["commands"].append(inspect_cmd)
            if inspect_cmd["ok"]:
                try:
                    size_bytes = int(inspect_cmd["stdout"].strip())
                    report["summary"][f"{label}_image_size_mb"] = round(size_bytes / (1024 * 1024), 1)
                except (ValueError, TypeError):
                    pass

    # 6. Fetch Umami GitHub metadata
    umami_github = _fetch_github_repo_info("umami-software/umami")
    report["summary"]["umami_github"] = {k: v for k, v in umami_github.items() if k not in ("ok",)}
    report["summary"]["umami_github_ok"] = umami_github.get("ok", False)

    # 7. Fetch PostHog GitHub metadata
    posthog_github = _fetch_github_repo_info("PostHog/posthog")
    report["summary"]["posthog_github"] = {k: v for k, v in posthog_github.items() if k not in ("ok",)}
    report["summary"]["posthog_github_ok"] = posthog_github.get("ok", False)

    # 8. Fetch Plausible GitHub metadata (from capability matrix)
    plausible_github = _fetch_github_repo_info("plausible/analytics")
    report["summary"]["plausible_github"] = {k: v for k, v in plausible_github.items() if k not in ("ok",)}
    report["summary"]["plausible_github_ok"] = plausible_github.get("ok", False)

    report["status"] = "pass" if all_ok else "warn"
    report["capability_complete"] = all_ok

    json_path = output_dir / "analytics-smoke.json"
    report["artifacts"]["report_json"] = str(json_path)
    _write_json(json_path, report)

    return report


def main() -> int:
    import sys

    output_dir = sys.argv[1] if len(sys.argv) > 1 else "outputs/become-manus/analytics"
    report = run_analytics_smoke(output_dir)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["status"] in {"pass", "warn"} else 1
