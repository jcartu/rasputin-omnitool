import json
import subprocess
from pathlib import Path


def test_public_api_exports_version_and_core_functions():
    import rasputin_omnitool as kernel

    assert kernel.__version__ == "0.3.0"
    assert callable(kernel.all_candidates)
    assert callable(kernel.write_license_review)
    assert callable(kernel.write_manual_license_review)
    assert callable(kernel.run_sandbox_bakeoff)
    assert callable(kernel.run_deep_research_bakeoff)
    assert callable(kernel.create_demo_deliverables)
    assert callable(kernel.run_docling_fixture_parse_e2e)
    assert callable(kernel.run_crawl4ai_fixture_crawl_e2e)


def test_candidate_catalog_contains_core_manus_capabilities():
    from rasputin_omnitool.catalog import CAPABILITIES, candidate_summary

    required = {
        "agent_computer",
        "browser_operator",
        "wide_research",
        "deep_research",
        "webapp_builder",
        "slides",
        "data_analysis",
        "workflow_integrations",
        "mail_agent",
        "api_platform",
    }
    assert required.issubset(CAPABILITIES)
    summary = candidate_summary()
    assert summary["capability_count"] >= len(required)
    assert summary["candidate_count"] >= 25
    assert "Playwright MCP" in summary["preferred_candidates"]


def test_deliverable_demo_generates_expected_artifacts(tmp_path):
    from rasputin_omnitool.deliverables import create_demo_deliverables, validate_artifacts

    manifest = create_demo_deliverables(tmp_path)
    names = {item["name"] for item in manifest["artifacts"]}
    assert {
        "source_data_csv",
        "analysis_markdown",
        "chart_png",
        "executive_summary_html",
        "executive_summary_pdf",
        "workbook_xlsx",
        "presentation_pptx",
    }.issubset(names)
    validation = validate_artifacts(manifest)
    assert validation["status"] == "pass"
    assert all(item["exists"] and item["size_bytes"] > 0 for item in validation["artifacts"])


def test_cli_entrypoints_help_lists_five_subcommands():
    result = subprocess.run(
        ["python", "-m", "rasputin_omnitool", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0
    expected = {"matrix", "license-review", "manual-license-review", "bakeoff", "library-smoke"}
    # Join wrapped usage lines (argparse splits long usage across lines)
    all_lines = result.stdout.splitlines()
    usage_parts = []
    usage_found = False
    for line in all_lines:
        if line.startswith("usage:"):
            usage_found = True
            usage_parts.append(line)
        elif usage_found and line.strip() and not line.startswith("positional") and not line.startswith("options:"):
            usage_parts.append(line)
        elif usage_found and (line.startswith("positional") or line.startswith("options:")):
            break
    usage_block = " ".join(usage_parts)
    command_group = usage_block.split("{")[1].split("}")[0]
    assert set(command_group.split(",")) == expected
    for command in expected:
        assert command in result.stdout
    for removed in ("demo", "browser-e2e", "sandbox-bakeoff", "deep-research-bakeoff", "webapp-smoke", "runtime-e2e", "sandbox-hosting"):
        assert removed not in result.stdout


def test_library_smoke_schemas_without_external_installs(tmp_path):
    from rasputin_omnitool.library_smoke import run_crawl4ai_fixture_crawl_e2e, run_docling_fixture_parse_e2e

    docling = run_docling_fixture_parse_e2e(tmp_path / "docling", run_external=False)
    crawl4ai = run_crawl4ai_fixture_crawl_e2e(tmp_path / "crawl4ai", run_external=False)

    for report in (docling, crawl4ai):
        assert report["schema_version"] == 1
        assert report["status"] == "blocker"
        assert report["capability_complete"] is False
        assert report["summary"]["attempted_install"] is False
        assert Path(report["artifacts"]["report_json"]).exists()
        assert Path(report["artifacts"]["report_markdown"]).exists()
    assert docling["name"] == "docling_fixture_parse"
    assert crawl4ai["name"] == "crawl4ai_fixture_crawl"


def test_bakeoff_schema_without_external_network(tmp_path):
    from rasputin_omnitool.bakeoff import run_deep_research_bakeoff, run_sandbox_bakeoff

    sandbox = run_sandbox_bakeoff(tmp_path, run_external=False)
    deep_research = run_deep_research_bakeoff(tmp_path, run_external=False)

    assert sandbox["summary"]["schema_version"] == 1
    assert deep_research["summary"]["schema_version"] == 1
    assert {record["candidate"]["name"] for record in sandbox["records"]} == {"agent-infra/sandbox", "microsandbox"}
    assert {record["candidate"]["name"] for record in deep_research["records"]} == {"Crawl4AI", "Docling"}
    assert (tmp_path / "sandbox-bakeoff.json").exists()
    assert (tmp_path / "sandbox-bakeoff.md").exists()
    assert (tmp_path / "deep-research-bakeoff.json").exists()
    assert (tmp_path / "deep-research-bakeoff.md").exists()
    for report in (sandbox, deep_research):
        assert report["safety_policy"]["host_mutation"] == "none_intended"
        assert "package install" in report["safety_policy"]["forbidden_in_this_phase"]
        assert report["summary"]["capability_complete_count"] == 0
        assert all(not record["readiness"]["capability_complete"] for record in report["records"])


def test_bakeoff_parsers_extract_package_metadata():
    from rasputin_omnitool.bakeoff import parse_npm_view_json, parse_pip_index_versions

    pip_payload = parse_pip_index_versions("crawl4ai (0.8.6)\nAvailable versions: 0.8.6, 0.8.5, 0.8.0")
    assert pip_payload["latest"] == "0.8.6"
    assert pip_payload["available_version_count"] == 3

    npm_payload = parse_npm_view_json('{"version":"1.0.15","license":"ISC","repository.url":"git+https://github.com/agent-infra/sandbox-sdk.git"}')
    assert npm_payload["version"] == "1.0.15"
    assert npm_payload["license"] == "ISC"
    assert npm_payload["repository_url"].endswith("sandbox-sdk.git")


def test_license_review_classifies_repo_license_risk():
    from rasputin_omnitool.licenses import LicenseReviewRecord, classify_license_risk, summarize_license_review

    permissive = LicenseReviewRecord(
        name="Playwright MCP",
        repo="microsoft/playwright-mcp",
        url="https://github.com/microsoft/playwright-mcp",
        license_spdx="Apache-2.0",
        license_name="Apache License 2.0",
        license_source="github_api",
        capability="browser_operator",
    )
    agpl = LicenseReviewRecord(
        name="Example AGPL",
        repo="example/agpl",
        url="https://github.com/example/agpl",
        license_spdx="AGPL-3.0",
        license_name="GNU Affero General Public License v3.0",
        license_source="github_api",
        capability="sandbox",
    )
    unknown = LicenseReviewRecord(
        name="Unknown",
        repo="example/unknown",
        url="https://github.com/example/unknown",
        license_spdx="NOASSERTION",
        license_name="unknown",
        license_source="github_api",
        capability="sandbox",
    )

    assert classify_license_risk(permissive)["status"] == "approved_candidate"
    assert classify_license_risk(agpl)["status"] == "legal_review_required"
    assert classify_license_risk(agpl)["integration"] == "optional_service_only"
    assert classify_license_risk(unknown)["status"] == "legal_review_required"
    summary = summarize_license_review([permissive, agpl, unknown])
    assert summary["total"] == 3
    assert summary["approved_candidate_count"] == 1
    assert summary["legal_review_required_count"] == 2


def test_license_review_writes_markdown_and_json(tmp_path):
    from rasputin_omnitool.licenses import LicenseReviewRecord, write_license_review

    records = [
        LicenseReviewRecord(
            name="Playwright MCP",
            repo="microsoft/playwright-mcp",
            url="https://github.com/microsoft/playwright-mcp",
            license_spdx="Apache-2.0",
            license_name="Apache License 2.0",
            license_source="github_api",
            capability="browser_operator",
            latest_commit="abc123",
            fetched_at="2026-04-28T00:00:00+00:00",
        ),
        LicenseReviewRecord(
            name="OpenHands",
            repo="All-Hands-AI/OpenHands",
            url="https://github.com/All-Hands-AI/OpenHands",
            license_spdx="MIT",
            license_name="MIT License",
            license_source="github_api",
            capability="coding_agents",
            latest_commit="def456",
            fetched_at="2026-04-28T00:00:00+00:00",
        ),
    ]

    outputs = write_license_review(records, tmp_path)
    markdown = Path(outputs["markdown_path"]).read_text()
    summary = json.loads(Path(outputs["json_path"]).read_text())
    assert "# Rasputin Omnitool License Review" in markdown
    assert "microsoft/playwright-mcp" in markdown
    assert "approved_candidate" in markdown
    assert summary["summary"]["total"] == 2
    assert summary["summary"]["legal_review_required_count"] == 0


def test_manual_license_review_writes_outputs(tmp_path):
    from rasputin_omnitool.licenses_manual import write_manual_license_review

    outputs = write_manual_license_review(tmp_path)
    markdown = Path(outputs["markdown_path"]).read_text()
    loaded = json.loads(Path(outputs["json_path"]).read_text())
    assert "# Rasputin Omnitool — Manual License Review" in markdown
    assert "OpenHands" in markdown
    assert "Activepieces" in markdown
    assert "PostHog" in markdown
    assert loaded["summary"]["total"] >= 3
    assert "approved_count" in loaded["summary"]
    assert "conditional_count" in loaded["summary"]
    assert "review_required_count" in loaded["summary"]
