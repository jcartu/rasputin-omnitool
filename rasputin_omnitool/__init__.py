"""rasputin_omnitool — OSS capability catalog, license review, and library smoke."""

__version__ = "0.4.0"

from rasputin_omnitool.catalog import all_candidates, candidate_summary, CAPABILITIES
from rasputin_omnitool.licenses import fetch_default_license_review, write_license_review
from rasputin_omnitool.licenses_manual import write_manual_license_review
from rasputin_omnitool.bakeoff import (
    run_sandbox_bakeoff,
    run_deep_research_bakeoff,
    BakeoffCandidate,
)
from rasputin_omnitool.deliverables import create_demo_deliverables, validate_artifacts
from rasputin_omnitool.library_smoke import (
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
