from __future__ import annotations

import base64
import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .capability_matrix import CAPABILITIES

PERMISSIVE_LICENSES = {
    "MIT",
    "Apache-2.0",
    "BSD-2-Clause",
    "BSD-3-Clause",
    "ISC",
    "MPL-2.0",
}
REVIEW_LICENSE_MARKERS = {
    "AGPL",
    "GPL",
    "SSPL",
    "BUSL",
    "Elastic-2.0",
    "NOASSERTION",
    "unknown",
    "verify",
    "source-available",
    "enterprise/",
    "packages/ee",
}
DEFAULT_REPOS = {
    "microsoft/playwright-mcp": ("Playwright MCP", "browser_operator"),
    "browser-use/browser-use": ("browser-use", "browser_operator"),
    "agent-infra/sandbox": ("agent-infra/sandbox", "agent_computer"),
    "zerocore-ai/microsandbox": ("microsandbox", "agent_computer"),
    "All-Hands-AI/OpenHands": ("OpenHands", "coding_agents"),
    "Aider-AI/aider": ("aider", "coding_agents"),
    "stackblitz-labs/bolt.diy": ("bolt.diy", "webapp_builder"),
    "unclecode/crawl4ai": ("Crawl4AI", "deep_research"),
    "docling-project/docling": ("Docling", "deep_research"),
    "activepieces/activepieces": ("Activepieces", "workflow_integrations"),
    # verify-licensed candidates from capability_matrix
    "alibaba/OpenSandbox": ("OpenSandbox", "agent_computer"),
    "onlook-dev/onlook": ("Onlook", "design_view"),
    "PostHog/posthog": ("PostHog", "analytics"),
}


@dataclass(frozen=True)
class LicenseReviewRecord:
    name: str
    repo: str
    url: str
    license_spdx: str
    license_name: str
    license_source: str
    capability: str
    latest_commit: str | None = None
    fetched_at: str | None = None
    homepage: str | None = None
    stars: int | None = None
    archived: bool | None = None
    default_branch: str | None = None
    license_path: str | None = None
    license_excerpt: str | None = None
    notes: str | None = None
    error: str | None = None

    def to_dict(self) -> dict:
        payload = asdict(self)
        payload["risk"] = classify_license_risk(self)
        return payload


def classify_license_risk(record: LicenseReviewRecord) -> dict:
    spdx = (record.license_spdx or "NOASSERTION").strip()
    name = (record.license_name or "unknown").strip()
    haystack = f"{spdx} {name}".lower()
    if spdx in PERMISSIVE_LICENSES:
        return {
            "status": "approved_candidate",
            "integration": "safe_to_evaluate_and_vendor_or_integrate",
            "reason": f"SPDX license {spdx} is permissive/OSS-compatible for evaluation.",
        }
    if any(marker.lower() in haystack for marker in REVIEW_LICENSE_MARKERS):
        return {
            "status": "legal_review_required",
            "integration": "optional_service_only",
            "reason": f"License '{spdx}'/'{name}' is copyleft, source-available, unknown, or manually flagged.",
        }
    return {
        "status": "legal_review_required",
        "integration": "manual_review_before_integration",
        "reason": f"License '{spdx}'/'{name}' is not in the approved permissive allow-list.",
    }


def summarize_license_review(records: Iterable[LicenseReviewRecord]) -> dict:
    records = list(records)
    reviewed = [classify_license_risk(r) for r in records]
    approved = sum(1 for r in reviewed if r["status"] == "approved_candidate")
    legal = sum(1 for r in reviewed if r["status"] == "legal_review_required")
    return {
        "schema_version": 1,
        "total": len(records),
        "approved_candidate_count": approved,
        "legal_review_required_count": legal,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def _github_json(repo: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "Hermes-Becoming-Manus-License-Review"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_github_license_record(repo: str, *, name: str | None = None, capability: str | None = None) -> LicenseReviewRecord:
    fetched_at = datetime.now(timezone.utc).isoformat()
    inferred_name, inferred_capability = DEFAULT_REPOS.get(repo, (repo, "unknown"))
    try:
        data = _github_json(repo)
        license_info = data.get("license") or {}
        spdx = license_info.get("spdx_id") or "NOASSERTION"
        license_name = license_info.get("name") or "unknown"
        return LicenseReviewRecord(
            name=name or inferred_name,
            repo=repo,
            url=data.get("html_url") or f"https://github.com/{repo}",
            license_spdx=spdx,
            license_name=license_name,
            license_source="github_api",
            capability=capability or inferred_capability,
            latest_commit=(data.get("pushed_at") or data.get("updated_at")),
            fetched_at=fetched_at,
            homepage=data.get("homepage") or None,
            stars=data.get("stargazers_count"),
            archived=data.get("archived"),
        )
    except Exception as exc:  # network/API failures should become explicit review blockers
        return LicenseReviewRecord(
            name=name or inferred_name,
            repo=repo,
            url=f"https://github.com/{repo}",
            license_spdx="NOASSERTION",
            license_name="unknown",
            license_source="github_api_error",
            capability=capability or inferred_capability,
            fetched_at=fetched_at,
            error=f"{type(exc).__name__}: {exc}",
        )


def fetch_default_license_review() -> list[LicenseReviewRecord]:
    return [fetch_github_license_record(repo, name=name, capability=capability) for repo, (name, capability) in DEFAULT_REPOS.items()]


def write_license_review(records: Iterable[LicenseReviewRecord], output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    records = list(records)
    summary = summarize_license_review(records)
    json_payload = {"summary": summary, "records": [r.to_dict() for r in records]}
    json_path = output_dir / "license-review.json"
    json_path.write_text(json.dumps(json_payload, indent=2) + "\n")

    lines = [
        "# Become Manus License Review",
        "",
        f"Generated: `{summary['generated_at']}`",
        "",
        "## Summary",
        "",
        f"- Total reviewed: {summary['total']}",
        f"- Approved candidates: {summary['approved_candidate_count']}",
        f"- Legal review required: {summary['legal_review_required_count']}",
        "",
        "## Records",
        "",
        "| Candidate | Repo | Capability | License | Risk | Integration | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for record in records:
        risk = classify_license_risk(record)
        notes = risk["reason"]
        if record.error:
            notes += f" Error: {record.error}"
        lines.append(
            f"| {record.name} | [{record.repo}]({record.url}) | {record.capability} | "
            f"{record.license_spdx} ({record.license_name}) | {risk['status']} | {risk['integration']} | {notes} |"
        )
    lines.extend([
        "",
        "## Policy",
        "",
        "Permissive licenses are approved for evaluation/integration. AGPL/GPL/source-available/unknown licenses remain optional-service-only or blocked pending legal review.",
    ])
    markdown_path = output_dir / "license-review.md"
    markdown_path.write_text("\n".join(lines) + "\n")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path), "summary": summary}
