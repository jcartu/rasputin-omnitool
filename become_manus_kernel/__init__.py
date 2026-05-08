"""become_manus_kernel — OSS capability catalog, license review, and library smoke."""

__version__ = "0.1.0"

from become_manus_kernel.catalog import all_candidates, candidate_summary, CAPABILITIES
from become_manus_kernel.licenses import fetch_default_license_review, write_license_review
from become_manus_kernel.licenses_manual import write_manual_license_review
from become_manus_kernel.bakeoff import (
    run_sandbox_bakeoff,
    run_deep_research_bakeoff,
    BakeoffCandidate,
)
from become_manus_kernel.deliverables import create_demo_deliverables, validate_artifacts
from become_manus_kernel.library_smoke import (
    run_docling_fixture_parse_e2e,
    run_crawl4ai_fixture_crawl_e2e,
)

__all__ = [
    "__version__",
    "all_candidates",
    "candidate_summary",
    "CAPABILITIES",
    "fetch_default_license_review",
    "write_license_review",
    "write_manual_license_review",
    "run_sandbox_bakeoff",
    "run_deep_research_bakeoff",
    "BakeoffCandidate",
    "create_demo_deliverables",
    "validate_artifacts",
    "run_docling_fixture_parse_e2e",
    "run_crawl4ai_fixture_crawl_e2e",
]
