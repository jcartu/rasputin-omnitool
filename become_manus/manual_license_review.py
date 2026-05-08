"""Manual license review for projects with non-standard or dual-licensing.

Sources: GitHub LICENSE files, official docs, and community reports (May 2026).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class ManualLicenseReview:
    name: str
    repo: str
    url: str
    capability: str
    core_license: str
    core_license_type: str  # "permissive", "copyleft", "source-available", "dual-license"
    commercial_use: str
    key_obligations: list[str] = field(default_factory=list)
    enterprise_license: str = ""
    enterprise_restricted: bool = False
    recent_changes: str = ""
    spdx_recommendation: str = ""
    recommendation: str = ""  # "approved", "conditional", "review_required"
    reviewed_at: str = ""


MANUAL_REVIEWS: list[ManualLicenseReview] = [
    ManualLicenseReview(
        name="OpenHands",
        repo="All-Hands-AI/OpenHands",
        url="https://github.com/All-Hands-AI/OpenHands",
        capability="coding_agents",
        core_license="MIT License",
        core_license_type="dual-license",
        commercial_use="Allowed for core (MIT)",
        key_obligations=[
            "Include MIT copyright notice in core usage",
            "Enterprise/ directory uses PolyForm Free Trial 1.0.0 — 30-day trial only, requires commercial license beyond",
            "Do not distribute enterprise features without license",
        ],
        enterprise_license="PolyForm Free Trial 1.0.0",
        enterprise_restricted=True,
        recent_changes="Enterprise license updated Apr 14 2026 (commit 4cdf88d). Main LICENSE clarified dual-license structure Sep 2 2025.",
        spdx_recommendation="MIT (core); PolyForm-Free-Trial-1.0.0 (enterprise/)",
        recommendation="conditional",
        reviewed_at="2026-05-08T00:00:00+00:00",
    ),
    ManualLicenseReview(
        name="Activepieces",
        repo="activepieces/activepieces",
        url="https://github.com/activepieces/activepieces",
        capability="workflow_integrations",
        core_license="MIT License",
        core_license_type="dual-license",
        commercial_use="Allowed for community edition (MIT)",
        key_obligations=[
            "Include MIT copyright notice",
            "Enterprise features (packages/ee/, packages/server/api/src/app/ee) require commercial license",
            "Do not redistribute enterprise features",
        ],
        enterprise_license="Activepieces Enterprise License (proprietary)",
        enterprise_restricted=True,
        recent_changes="LICENSE last updated Feb 15 2024. No license type changes since inception — always MIT + commercial dual license.",
        spdx_recommendation="MIT (community); LicenseRef-Activepieces-Enterprise (ee/)",
        recommendation="conditional",
        reviewed_at="2026-05-08T00:00:00+00:00",
    ),
    ManualLicenseReview(
        name="PostHog",
        repo="PostHog/posthog",
        url="https://github.com/PostHog/posthog",
        capability="analytics",
        core_license="PostHog License (custom)",
        core_license_type="source-available",
        commercial_use="Allowed for self-hosted; competing SaaS restricted",
        key_obligations=[
            "Custom license — not OSI-approved open source",
            "Third-party components retain their original licenses",
            "Enterprise features (ee/) use separate PostHog Enterprise License",
            "Restrictions on offering competing hosted services",
        ],
        enterprise_license="PostHog Enterprise License (proprietary)",
        enterprise_restricted=True,
        recent_changes="Custom license is a departure from standard OSI licenses. Historical shifts between license models observed.",
        spdx_recommendation="LicenseRef-PostHog (main); LicenseRef-PostHog-Enterprise (ee/)",
        recommendation="review_required",
        reviewed_at="2026-05-08T00:00:00+00:00",
    ),
    ManualLicenseReview(
        name="bolt.diy",
        repo="stackblitz-labs/bolt.diy",
        url="https://github.com/stackblitz-labs/bolt.diy",
        capability="webapp_builder",
        core_license="MIT License",
        core_license_type="permissive",
        commercial_use="Allowed (MIT), but WebContainer API requires commercial license for production for-profit use",
        key_obligations=[
            "Include MIT copyright notice",
            "WebContainers (StackBlitz tech) — free for prototypes/POCs, commercial license for production",
            "No additional copyleft or network-use obligations in core codebase",
        ],
        enterprise_license="",
        enterprise_restricted=False,
        recent_changes="Originally by Cole Medin, now community-driven. Active development with many contributors.",
        spdx_recommendation="MIT (core); WebContainer API license separate",
        recommendation="conditional",
        reviewed_at="2026-05-08T00:00:00+00:00",
    ),
]


def write_manual_license_review(output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate Markdown
    md_lines: list[str] = [
        "# Become Manus — Manual License Review",
        "",
        f"Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "Manual review for projects with dual-licensing, source-available, or non-standard licenses.",
        "",
        "## Summary",
        "",
    ]

    approved = [r for r in MANUAL_REVIEWS if r.recommendation == "approved"]
    conditional = [r for r in MANUAL_REVIEWS if r.recommendation == "conditional"]
    required = [r for r in MANUAL_REVIEWS if r.recommendation == "review_required"]

    md_lines.append(f"- **Approved**: {len(approved)}")
    md_lines.append(f"- **Conditional** (approved with caveats): {len(conditional)}")
    md_lines.append(f"- **Review Required**: {len(required)}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    for review in MANUAL_REVIEWS:
        md_lines.append(f"## {review.name}")
        md_lines.append("")
        md_lines.append(f"- **Repo**: [{review.repo}]({review.url})")
        md_lines.append(f"- **Capability**: {review.capability}")
        md_lines.append(f"- **Core License**: {review.core_license} ({review.core_license_type})")
        md_lines.append(f"- **Commercial Use**: {review.commercial_use}")
        if review.enterprise_license:
            md_lines.append(f"- **Enterprise License**: {review.enterprise_license}")
            md_lines.append(f"- **Enterprise Restricted**: {'Yes' if review.enterprise_restricted else 'No'}")
        md_lines.append(f"- **SPDX**: {review.spdx_recommendation}")
        md_lines.append(f"- **Recommendation**: {review.recommendation}")
        if review.recent_changes:
            md_lines.append(f"- **Recent Changes**: {review.recent_changes}")
        md_lines.append("")
        md_lines.append("### Key Obligations")
        for obligation in review.key_obligations:
            md_lines.append(f"- {obligation}")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    md_path = output_dir / "manual-license-review.md"
    md_path.write_text("\n".join(md_lines), encoding="utf-8")

    # Generate JSON
    json_data = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": len(MANUAL_REVIEWS),
            "approved_count": len(approved),
            "conditional_count": len(conditional),
            "review_required_count": len(required),
        },
        "reviews": [asdict(r) for r in MANUAL_REVIEWS],
    }
    json_path = output_dir / "manual-license-review.json"
    json_path.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")

    return {"markdown_path": str(md_path), "json_path": str(json_path), "summary": json_data["summary"]}
