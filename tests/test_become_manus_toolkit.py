import json
import subprocess
from pathlib import Path

import pytest


def test_candidate_matrix_contains_core_manus_capabilities():
    from become_manus.capability_matrix import CAPABILITIES, candidate_summary

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


def test_smoke_report_schema_uses_safe_checks(tmp_path, monkeypatch):
    from become_manus.smoke import run_smoke_checks

    report = run_smoke_checks(output_dir=tmp_path, run_external=False)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    check_names = {check["name"] for check in report["checks"]}
    assert {"python", "node", "npm", "hermes", "docker", "playwright_mcp_config"}.issubset(check_names)
    written = tmp_path / "become-manus-smoke.json"
    assert written.exists()
    loaded = json.loads(written.read_text())
    assert loaded["schema_version"] == 1


def test_deliverable_demo_generates_expected_artifacts(tmp_path):
    from become_manus.deliverables import create_demo_deliverables, validate_artifacts

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


def test_cli_entrypoints_help():
    result = subprocess.run(
        ["python", "-m", "become_manus", "--help"],
        cwd=Path(__file__).resolve().parents[1],
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert result.returncode == 0
    assert "smoke" in result.stdout
    assert "demo" in result.stdout
    assert "license-review" in result.stdout
    assert "browser-e2e" in result.stdout
    assert "sandbox-bakeoff" in result.stdout
    assert "deep-research-bakeoff" in result.stdout
    assert "research-pipeline-e2e" in result.stdout
    assert "sandbox-smoke" in result.stdout
    assert "webapp-smoke" in result.stdout
    assert "runtime-e2e" in result.stdout
    assert "sandbox-hosting" in result.stdout
    assert "manual-license-review" in result.stdout


def test_runtime_e2e_report_schema_without_external_installs(tmp_path):
    from become_manus.runtime_e2e import run_runtime_e2e

    summary_path = tmp_path / "runtime-e2e-report.md"
    report = run_runtime_e2e(tmp_path / "runtime-e2e", summary_path=summary_path, run_external=False)
    assert report["schema_version"] == 1
    assert report["status"] == "blocker"
    assert report["summary"]["capability_complete_count"] == 0
    assert {item["name"] for item in report["e2e_reports"]} == {
        "docling_fixture_parse",
        "crawl4ai_fixture_crawl",
        "sandbox_runtime_smoke",
    }
    assert all(item["capability_complete"] is False for item in report["e2e_reports"])
    assert Path(report["artifacts"]["summary_markdown"]).exists()
    assert Path(report["artifacts"]["summary_json"]).exists()
    assert Path(report["artifacts"]["docling_report_json"]).exists()
    assert Path(report["artifacts"]["crawl4ai_report_json"]).exists()
    assert Path(report["artifacts"]["sandbox_report_json"]).exists()


def test_browser_e2e_schema_without_external_network(tmp_path):
    from become_manus.browser_e2e import run_browser_e2e

    report = run_browser_e2e(tmp_path, run_external=False)
    assert report["schema_version"] == 1
    assert report["status"] == "skip"
    assert (tmp_path / "browser-e2e.json").exists()


def test_bakeoff_schema_without_external_network(tmp_path):
    from become_manus.bakeoff import run_deep_research_bakeoff, run_sandbox_bakeoff

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
    from become_manus.bakeoff import parse_npm_view_json, parse_pip_index_versions

    pip_payload = parse_pip_index_versions("crawl4ai (0.8.6)\nAvailable versions: 0.8.6, 0.8.5, 0.8.0")
    assert pip_payload["latest"] == "0.8.6"
    assert pip_payload["available_version_count"] == 3

    npm_payload = parse_npm_view_json('{"version":"1.0.15","license":"ISC","repository.url":"git+https://github.com/agent-infra/sandbox-sdk.git"}')
    assert npm_payload["version"] == "1.0.15"
    assert npm_payload["license"] == "ISC"
    assert npm_payload["repository_url"].endswith("sandbox-sdk.git")


def test_research_pipeline_fixture_e2e_schema(tmp_path):
    from become_manus.research_pipeline import run_research_pipeline_e2e

    report = run_research_pipeline_e2e(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] == "pass"
    assert report["summary"]["citation_count"] >= 2
    assert report["summary"]["parsed_document_count"] >= 2
    assert Path(report["artifacts"]["report_md"]).exists()
    assert Path(report["artifacts"]["report_json"]).exists()


def test_sandbox_smoke_non_destructive_e2e_schema(tmp_path):
    from become_manus.sandbox_smoke import run_sandbox_smoke

    report = run_sandbox_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] == "pass"
    assert report["summary"]["host_mutation_detected"] is False
    assert report["summary"]["subprocess_returncode"] == 0
    assert Path(report["artifacts"]["transcript_json"]).exists()


def test_webapp_smoke_generates_and_serves_static_app(tmp_path):
    from become_manus.webapp_smoke import run_webapp_smoke

    report = run_webapp_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] == "pass"
    assert report["summary"]["http_status"] == 200
    assert "Become Manus" in report["summary"]["page_title"]
    assert Path(report["artifacts"]["app_dir"]).exists()
    assert Path(report["artifacts"]["report_json"]).exists()


def test_coding_agents_smoke_schema(tmp_path):
    from become_manus.coding_agents_smoke import run_coding_agents_smoke

    report = run_coding_agents_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "coding_agents"
    assert "aider_available" in report["summary"]
    assert "openhands_metadata_ok" in report["summary"]
    assert (tmp_path / "coding-agents-smoke.json").exists()
    assert report["safety"]["global_python_mutation"] == "none_intended"


def test_workflow_smoke_schema(tmp_path):
    from become_manus.workflow_smoke import run_workflow_smoke

    report = run_workflow_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "workflow_integrations"
    assert "mcp_servers_repo_ok" in report["summary"]
    assert "mcp_servers_list_ok" in report["summary"]
    assert "composio_github_ok" in report["summary"]
    assert (tmp_path / "workflow-smoke.json").exists()
    assert report["safety"]["global_python_mutation"] == "none_intended"


def test_mobile_smoke_schema(tmp_path):
    from become_manus.mobile_smoke import run_mobile_smoke

    report = run_mobile_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "mobile_publishing"
    assert "expo_cli_available" in report["summary"] or "expo_cli_version" in report["summary"]
    assert "capacitor_cli_version" in report["summary"]
    assert (tmp_path / "mobile-smoke.json").exists()
    assert report["safety"]["global_python_mutation"] == "none_intended"


def test_analytics_smoke_schema(tmp_path):
    from become_manus.analytics_smoke import run_analytics_smoke

    report = run_analytics_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "analytics"
    assert "docker_version" in report["summary"]
    assert "umami_github_ok" in report["summary"]
    assert "posthog_github_ok" in report["summary"]
    assert (tmp_path / "analytics-smoke.json").exists()
    assert report["safety"]["global_python_mutation"] == "none_intended"


def test_mail_smoke_schema(tmp_path, monkeypatch):
    from become_manus.mail_smoke import run_mail_smoke

    report = run_mail_smoke(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "mail_agent"
    assert "himalaya_available" in report["summary"]
    assert "hermes_email_configured" in report["summary"]
    assert (tmp_path / "mail-smoke.json").exists()
    assert report["safety"]["global_python_mutation"] == "none_intended"


def test_license_review_classifies_repo_license_risk():
    from become_manus.license_review import LicenseReviewRecord, classify_license_risk, summarize_license_review

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
    from become_manus.license_review import LicenseReviewRecord, write_license_review

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
    assert "# Become Manus License Review" in markdown
    assert "microsoft/playwright-mcp" in markdown
    assert "approved_candidate" in markdown
    assert summary["summary"]["total"] == 2
    assert summary["summary"]["legal_review_required_count"] == 0


def test_sandbox_hosting_schema(tmp_path):
    from become_manus.sandbox_hosting import run_sandbox_hosting

    report = run_sandbox_hosting(tmp_path)
    assert report["schema_version"] == 1
    assert report["status"] in {"pass", "warn", "fail"}
    assert report["capability"] == "sandbox_hosting_e2e"
    assert "checks" in report
    assert isinstance(report["checks"], list)
    assert "container_name" in report["summary"]
    assert "http_status" in report["summary"]
    assert (tmp_path / "sandbox-hosting.json").exists()


def test_manual_license_review_writes_outputs(tmp_path):
    from become_manus.manual_license_review import write_manual_license_review

    outputs = write_manual_license_review(tmp_path)
    markdown = Path(outputs["markdown_path"]).read_text()
    loaded = json.loads(Path(outputs["json_path"]).read_text())
    assert "# Become Manus — Manual License Review" in markdown
    assert "OpenHands" in markdown
    assert "Activepieces" in markdown
    assert "PostHog" in markdown
    assert loaded["summary"]["total"] >= 3
    assert "approved_count" in loaded["summary"]
    assert "conditional_count" in loaded["summary"]
    assert "review_required_count" in loaded["summary"]
