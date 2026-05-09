from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

SCHEMA_VERSION = 1
COMMAND_TIMEOUT_SECONDS = 45


@dataclass(frozen=True)
class BakeoffCandidate:
    name: str
    capability: str
    repo: str
    url: str
    license: str
    role: str
    package_manager: str | None = None
    package_name: str | None = None
    import_names: tuple[str, ...] = ()
    cli_names: tuple[str, ...] = ()
    readiness_goal: str = "metadata_and_installability_only"
    host_mutation_risk: str = "none_for_metadata_checks"
    e2e_scope: str = "not_run"
    notes: str = ""


SANDBOX_CANDIDATES: tuple[BakeoffCandidate, ...] = (
    BakeoffCandidate(
        name="agent-infra/sandbox",
        capability="agent_computer",
        repo="agent-infra/sandbox",
        url="https://github.com/agent-infra/sandbox",
        license="Apache-2.0",
        role="all-in-one Docker-style agent computer/sandbox runtime",
        package_manager="npm",
        package_name="@agent-infra/sandbox",
        readiness_goal="repo_and_sdk_metadata_ready_for_safe_followup",
        host_mutation_risk="full runtime likely requires Docker/containers; this bakeoff does not start containers or mutate the host",
        e2e_scope="deferred_until_isolated_container_smoke",
        notes="Evaluated with GitHub API and npm package metadata only.",
    ),
    BakeoffCandidate(
        name="microsandbox",
        capability="agent_computer",
        repo="zerocore-ai/microsandbox",
        url="https://github.com/zerocore-ai/microsandbox",
        license="Apache-2.0",
        role="local-first programmable code sandboxes",
        package_manager="pypi",
        package_name="microsandbox",
        import_names=("microsandbox",),
        cli_names=("microsandbox",),
        readiness_goal="repo_and_pypi_metadata_ready_for_safe_followup",
        host_mutation_risk="full runtime may start sandbox services/containers; this bakeoff only checks metadata/import/CLI availability",
        e2e_scope="deferred_until_isolated_non_destructive_smoke",
        notes="PyPI index/import/CLI checks are lightweight and do not install the package.",
    ),
)


DEEP_RESEARCH_CANDIDATES: tuple[BakeoffCandidate, ...] = (
    BakeoffCandidate(
        name="Crawl4AI",
        capability="deep_research",
        repo="unclecode/crawl4ai",
        url="https://github.com/unclecode/crawl4ai",
        license="Apache-2.0",
        role="LLM-friendly web crawler/extractor",
        package_manager="pypi",
        package_name="crawl4ai",
        import_names=("crawl4ai",),
        cli_names=("crawl4ai-setup", "crawl4ai-doctor"),
        readiness_goal="repo_and_pypi_metadata_ready_for_safe_followup",
        host_mutation_risk="install may download browser/runtime assets; this bakeoff avoids installs and browser setup",
        e2e_scope="deferred_until_crawl_smoke_with_fixture_url",
        notes="Import/CLI checks are best-effort against the current environment only.",
    ),
    BakeoffCandidate(
        name="Docling",
        capability="deep_research",
        repo="docling-project/docling",
        url="https://github.com/docling-project/docling",
        license="MIT",
        role="PDF/Office/document parsing and conversion",
        package_manager="pypi",
        package_name="docling",
        import_names=("docling",),
        cli_names=("docling",),
        readiness_goal="repo_and_pypi_metadata_ready_for_safe_followup",
        host_mutation_risk="install can be dependency-heavy; this bakeoff avoids installing or mutating global Python state",
        e2e_scope="deferred_until_fixture_document_parse_smoke",
        notes="PyPI metadata and local import/CLI presence are checked without installation.",
    ),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(text: str | bytes | None, limit: int = 4000) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def run_command(command: Sequence[str], *, timeout: int = COMMAND_TIMEOUT_SECONDS) -> dict:
    """Run a bounded metadata command and return a redaction-friendly payload."""
    try:
        result = subprocess.run(list(command), text=True, capture_output=True, timeout=timeout)
        return {
            "command": list(command),
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": _trim(result.stdout),
            "stderr": _trim(result.stderr),
            "timeout_seconds": timeout,
        }
    except FileNotFoundError as exc:
        return {
            "command": list(command),
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": str(exc),
            "timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": list(command),
            "ok": False,
            "returncode": None,
            "stdout": _trim(exc.stdout),
            "stderr": f"timeout after {timeout}s; {_trim(exc.stderr)}".strip(),
            "timeout_seconds": timeout,
        }


def fetch_github_repo_metadata(repo: str) -> dict:
    url = f"https://api.github.com/repos/{repo}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Hermes-Becoming-Manus-Bakeoff",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        license_info = data.get("license") or {}
        return {
            "status": "pass" if not data.get("archived") else "warn",
            "ok": True,
            "api_url": url,
            "full_name": data.get("full_name"),
            "html_url": data.get("html_url"),
            "description": data.get("description"),
            "stars": data.get("stargazers_count"),
            "forks": data.get("forks_count"),
            "open_issues": data.get("open_issues_count"),
            "default_branch": data.get("default_branch"),
            "pushed_at": data.get("pushed_at"),
            "updated_at": data.get("updated_at"),
            "archived": data.get("archived"),
            "license_spdx": license_info.get("spdx_id") or "NOASSERTION",
            "license_name": license_info.get("name") or "unknown",
            "topics": data.get("topics") or [],
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "status": "fail",
            "ok": False,
            "api_url": url,
            "error": f"{type(exc).__name__}: {exc}",
        }


def parse_pip_index_versions(stdout: str) -> dict:
    """Parse `pip index versions <package>` output without depending on pip internals."""
    latest = None
    first_line = next((line.strip() for line in stdout.splitlines() if line.strip()), "")
    match = re.search(r"\(([^)]+)\)", first_line)
    if match:
        latest = match.group(1).strip()
    versions: list[str] = []
    versions_match = re.search(r"Available versions:\s*(.+)", stdout, flags=re.IGNORECASE | re.DOTALL)
    if versions_match:
        raw_versions = versions_match.group(1).replace("\n", " ")
        versions = [item.strip().rstrip(",") for item in raw_versions.split(",") if item.strip()]
    return {"latest": latest, "available_versions_sample": versions[:10], "available_version_count": len(versions)}


def parse_npm_view_json(stdout: str) -> dict:
    try:
        data = json.loads(stdout or "{}")
    except json.JSONDecodeError:
        return {"raw": stdout, "parse_error": "invalid_json"}
    if isinstance(data, str):
        return {"version": data}
    if not isinstance(data, dict):
        return {"raw": data}
    repository = data.get("repository")
    if isinstance(repository, dict):
        repository_url = repository.get("url")
    else:
        repository_url = data.get("repository.url")
    return {
        "version": data.get("version"),
        "license": data.get("license"),
        "repository_url": repository_url,
    }


def check_pypi_index(package: str) -> dict:
    attempts = []
    primary = run_command([sys.executable, "-m", "pip", "index", "versions", package])
    attempts.append(primary)
    chosen = primary
    missing_embedded_pip = (not primary["ok"]) and "No module named pip" in f"{primary.get('stdout', '')}\n{primary.get('stderr', '')}"
    if missing_embedded_pip and shutil.which("pip"):
        fallback = run_command([shutil.which("pip") or "pip", "index", "versions", package])
        attempts.append(fallback)
        chosen = fallback
    parsed = parse_pip_index_versions(chosen.get("stdout", "")) if chosen["ok"] else {}
    return {
        "name": "pypi_index",
        "status": "pass" if chosen["ok"] and parsed.get("latest") else "fail",
        "package": package,
        "attempts": attempts,
        "latest": parsed.get("latest"),
        "available_versions_sample": parsed.get("available_versions_sample", []),
        "available_version_count": parsed.get("available_version_count", 0),
        "note": "Used current Python's pip first; fell back to pip executable only when current Python has no pip.",
    }


def check_npm_view(package: str) -> dict:
    npm = shutil.which("npm")
    if not npm:
        return {"name": "npm_view", "status": "fail", "package": package, "details": "npm not found"}
    result = run_command([npm, "view", package, "version", "license", "repository.url", "--json"])
    parsed = parse_npm_view_json(result.get("stdout", "")) if result["ok"] else {}
    return {
        "name": "npm_view",
        "status": "pass" if result["ok"] and parsed.get("version") else "fail",
        "package": package,
        "details": result,
        "version": parsed.get("version"),
        "license": parsed.get("license"),
        "repository_url": parsed.get("repository_url"),
        "parse_error": parsed.get("parse_error"),
    }


def check_imports(import_names: Sequence[str]) -> list[dict]:
    checks: list[dict] = []
    for import_name in import_names:
        try:
            spec = importlib.util.find_spec(import_name)
        except (ImportError, AttributeError, ValueError) as exc:
            checks.append({"name": "python_import_spec", "target": import_name, "status": "warn", "found": False, "error": f"{type(exc).__name__}: {exc}"})
            continue
        checks.append({
            "name": "python_import_spec",
            "target": import_name,
            "status": "pass" if spec is not None else "warn",
            "found": spec is not None,
            "origin": getattr(spec, "origin", None) if spec else None,
        })
    return checks


def check_cli_presence(cli_names: Sequence[str]) -> list[dict]:
    return [
        {"name": "cli_presence", "target": cli_name, "status": "pass" if shutil.which(cli_name) else "warn", "path": shutil.which(cli_name)}
        for cli_name in cli_names
    ]


def _package_check(candidate: BakeoffCandidate) -> dict | None:
    if not candidate.package_manager or not candidate.package_name:
        return None
    if candidate.package_manager == "pypi":
        return check_pypi_index(candidate.package_name)
    if candidate.package_manager == "npm":
        return check_npm_view(candidate.package_name)
    return {"name": "package_metadata", "status": "warn", "details": f"unsupported package manager: {candidate.package_manager}"}


def _no_external_package_check(candidate: BakeoffCandidate) -> dict | None:
    if not candidate.package_manager or not candidate.package_name:
        return None
    return {
        "name": f"{candidate.package_manager}_metadata",
        "status": "skip",
        "package": candidate.package_name,
        "details": "external metadata command skipped",
    }


def evaluate_candidate(candidate: BakeoffCandidate, *, run_external: bool = True) -> dict:
    github = fetch_github_repo_metadata(candidate.repo) if run_external else {
        "status": "skip",
        "ok": None,
        "api_url": f"https://api.github.com/repos/{candidate.repo}",
        "details": "external GitHub API check skipped",
    }
    package_check = _package_check(candidate) if run_external else _no_external_package_check(candidate)
    checks = [{"name": "github_repo_metadata", **github}]
    if package_check:
        checks.append(package_check)
    checks.extend(check_imports(candidate.import_names))
    checks.extend(check_cli_presence(candidate.cli_names))

    critical_statuses = [check["status"] for check in checks if check["name"] in {"github_repo_metadata", "pypi_index", "npm_view"}]
    optional_statuses = [check["status"] for check in checks if check["name"] not in {"github_repo_metadata", "pypi_index", "npm_view"}]
    if any(status == "fail" for status in critical_statuses):
        status = "fail"
    elif any(status in {"warn", "skip"} for status in critical_statuses + optional_statuses):
        status = "warn"
    else:
        status = "pass"

    return {
        "candidate": asdict(candidate),
        "status": status,
        "readiness": {
            "metadata_ready": status in {"pass", "warn"} and not any(s == "fail" for s in critical_statuses),
            "local_import_available": any(check.get("name") == "python_import_spec" and check.get("status") == "pass" for check in checks),
            "local_cli_available": any(check.get("name") == "cli_presence" and check.get("status") == "pass" for check in checks),
            "capability_complete": False,
            "capability_claim": "not_complete_metadata_only_no_e2e_smoke_run",
            "next_e2e_needed": candidate.e2e_scope,
        },
        "checks": checks,
    }


def summarize_records(records: Iterable[dict]) -> dict:
    records = list(records)
    status_counts = {"pass": 0, "warn": 0, "fail": 0, "skip": 0}
    for record in records:
        status_counts[record["status"]] = status_counts.get(record["status"], 0) + 1
    if status_counts.get("fail", 0):
        status = "fail"
    elif status_counts.get("warn", 0) or status_counts.get("skip", 0):
        status = "warn"
    else:
        status = "pass"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "status": status,
        "candidate_count": len(records),
        "status_counts": status_counts,
        "capability_complete_count": sum(1 for record in records if record["readiness"].get("capability_complete")),
        "metadata_ready_count": sum(1 for record in records if record["readiness"].get("metadata_ready")),
    }


def _markdown_table_row(record: dict) -> str:
    candidate = record["candidate"]
    package = candidate.get("package_name") or "n/a"
    package_manager = candidate.get("package_manager") or "n/a"
    version = "n/a"
    repo_stars = "n/a"
    for check in record["checks"]:
        if check.get("name") in {"pypi_index", "npm_view"} and check.get("version"):
            version = str(check.get("version"))
        if check.get("name") == "pypi_index" and check.get("latest"):
            version = str(check.get("latest"))
        if check.get("name") == "github_repo_metadata" and check.get("stars") is not None:
            repo_stars = str(check.get("stars"))
    local_import = "yes" if record["readiness"].get("local_import_available") else "no"
    local_cli = "yes" if record["readiness"].get("local_cli_available") else "no"
    return (
        f"| {candidate['name']} | {record['status']} | {package_manager} | {package} | {version} | "
        f"{repo_stars} | {local_import} | {local_cli} | {record['readiness']['capability_claim']} |"
    )


def write_bakeoff_report(kind: str, title: str, records: Sequence[dict], output_dir: str | Path, *, run_external: bool) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = summarize_records(records)
    payload = {
        "summary": summary,
        "kind": kind,
        "run_external": run_external,
        "safety_policy": {
            "host_mutation": "none_intended",
            "forbidden_in_this_phase": ["docker run", "package install", "service start", "credential use"],
            "completion_rule": "capability_complete remains false until an E2E/smoke artifact passes",
        },
        "records": list(records),
    }
    json_path = output_dir / f"{kind}.json"
    markdown_path = output_dir / f"{kind}.md"
    json_path.write_text(json.dumps(payload, indent=2) + "\n")

    lines = [
        f"# {title}",
        "",
        f"Generated: `{summary['generated_at']}`",
        f"Status: `{summary['status']}`",
        f"Candidates: `{summary['candidate_count']}`",
        "",
        "## Safety scope",
        "",
        "This bakeoff is metadata/installability readiness only. It does **not** install packages, run containers, start services, mutate host configuration, or use credentials.",
        "No capability is marked complete here; `capability_complete` stays `false` until a later E2E/smoke proof writes a passing artifact.",
        "",
        "## Summary table",
        "",
        "| Candidate | Status | Package manager | Package | Latest/version | GitHub stars | Local import | Local CLI | Capability claim |",
        "|---|---:|---|---|---|---:|---:|---:|---|",
    ]
    lines.extend(_markdown_table_row(record) for record in records)
    lines.extend([
        "",
        "## Candidate notes and blockers",
        "",
    ])
    for record in records:
        candidate = record["candidate"]
        lines.extend([
            f"### {candidate['name']}",
            "",
            f"- Repo: `{candidate['repo']}`",
            f"- Role: {candidate['role']}",
            f"- Host mutation risk for future E2E: {candidate['host_mutation_risk']}",
            f"- Next E2E needed: `{record['readiness']['next_e2e_needed']}`",
            f"- Notes: {candidate.get('notes') or 'n/a'}",
            "- Checks:",
        ])
        for check in record["checks"]:
            label = check.get("target") or check.get("package") or check.get("full_name") or check.get("api_url") or check.get("name")
            extra = ""
            if check.get("latest"):
                extra = f" latest={check['latest']}"
            elif check.get("version"):
                extra = f" version={check['version']}"
            elif check.get("path"):
                extra = f" path={check['path']}"
            lines.append(f"  - `{check.get('name')}` {label}: `{check.get('status')}`{extra}")
        lines.append("")
    markdown_path.write_text("\n".join(lines).rstrip() + "\n")
    payload["artifacts"] = {"json_path": str(json_path), "markdown_path": str(markdown_path)}
    json_path.write_text(json.dumps(payload, indent=2) + "\n")
    return payload


def run_bakeoff(kind: str, candidates: Sequence[BakeoffCandidate], output_dir: str | Path, *, run_external: bool = True) -> dict:
    records = [evaluate_candidate(candidate, run_external=run_external) for candidate in candidates]
    title = "Rasputin Omnitool Sandbox Bakeoff" if kind == "sandbox-bakeoff" else "Rasputin Omnitool Deep Research Bakeoff"
    return write_bakeoff_report(kind, title, records, output_dir, run_external=run_external)


def run_sandbox_bakeoff(output_dir: str | Path = "outputs/rasputin-omnitool", *, run_external: bool = True) -> dict:
    return run_bakeoff("sandbox-bakeoff", SANDBOX_CANDIDATES, output_dir, run_external=run_external)


def run_deep_research_bakeoff(output_dir: str | Path = "outputs/rasputin-omnitool", *, run_external: bool = True) -> dict:
    return run_bakeoff("deep-research-bakeoff", DEEP_RESEARCH_CANDIDATES, output_dir, run_external=run_external)
