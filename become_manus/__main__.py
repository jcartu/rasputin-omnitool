from __future__ import annotations

import argparse
import json
from pathlib import Path

from .bakeoff import run_deep_research_bakeoff, run_sandbox_bakeoff
from .browser_e2e import run_browser_e2e
from .capability_matrix import all_candidates, candidate_summary
from .deliverables import create_demo_deliverables, validate_artifacts
from .license_review import fetch_default_license_review, write_license_review
from .manual_license_review import write_manual_license_review
from .runtime_e2e import run_runtime_e2e
from .sandbox_hosting import run_sandbox_hosting
from .smoke import run_smoke_checks
from .webapp_smoke import run_webapp_smoke


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m become_manus", description="Hermes Become Manus integration harness")
    sub = parser.add_subparsers(dest="command", required=False)

    smoke = sub.add_parser("smoke", help="run local Manus-parity readiness smoke checks")
    smoke.add_argument("--output-dir", default="outputs/become-manus/smoke")
    smoke.add_argument("--no-external", action="store_true", help="skip commands that may download/start external MCP servers")

    demo = sub.add_parser("demo", help="generate demo report/chart/pdf/xlsx/pptx artifacts")
    demo.add_argument("--output-dir", default="outputs/become-manus/demo")

    matrix = sub.add_parser("matrix", help="print OSS candidate matrix JSON")
    matrix.add_argument("--output", default=None)

    license_review = sub.add_parser("license-review", help="fetch GitHub license metadata for top candidates")
    license_review.add_argument("--output-dir", default="outputs/become-manus")

    browser = sub.add_parser("browser-e2e", help="run a Playwright browser screenshot E2E")
    browser.add_argument("--output-dir", default="outputs/become-manus/browser-e2e")
    browser.add_argument("--url", default="https://example.com")
    browser.add_argument("--no-external", action="store_true")

    sandbox = sub.add_parser("sandbox-bakeoff", help="metadata/installability bakeoff for safe sandbox candidates")
    sandbox.add_argument("--output-dir", default="outputs/become-manus")
    sandbox.add_argument("--no-external", action="store_true", help="skip GitHub/npm/PyPI metadata commands")

    deep_research = sub.add_parser("deep-research-bakeoff", help="metadata/installability bakeoff for Crawl4AI and Docling")
    deep_research.add_argument("--output-dir", default="outputs/become-manus")
    deep_research.add_argument("--no-external", action="store_true", help="skip GitHub/PyPI metadata commands")

    webapp_smoke = sub.add_parser("webapp-smoke", help="generate and serve a local static webapp smoke test")
    webapp_smoke.add_argument("--output-dir", default="outputs/become-manus/webapp-smoke")

    runtime_e2e = sub.add_parser("runtime-e2e", help="run isolated actual runtime E2E attempts for Docling/Crawl4AI and sandbox blockers")
    runtime_e2e.add_argument("--output-dir", default="outputs/become-manus/runtime-e2e")
    runtime_e2e.add_argument("--summary-path", default="outputs/become-manus/runtime-e2e-report.md")
    runtime_e2e.add_argument("--no-external", action="store_true", help="write schema/blocker reports without package installs")
    runtime_e2e.add_argument("--install-timeout", type=int, default=600, help="per-package install timeout in seconds")

    sandbox_hosting = sub.add_parser("sandbox-hosting", help="verify site deployment and serving in Docker sandbox")
    sandbox_hosting.add_argument("--output-dir", default="outputs/become-manus/sandbox-hosting")

    manual_license = sub.add_parser("manual-license-review", help="write manual license review for dual-licensed projects")
    manual_license.add_argument("--output-dir", default="outputs/become-manus")

    args = parser.parse_args(argv)

    if args.command == "smoke":
        report = run_smoke_checks(args.output_dir, run_external=not args.no_external)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in {"pass", "warn"} else 1

    if args.command == "demo":
        manifest = create_demo_deliverables(args.output_dir)
        validation = validate_artifacts(manifest)
        print(json.dumps({"manifest": manifest, "validation": validation}, indent=2))
        return 0 if validation["status"] == "pass" else 1

    if args.command == "matrix":
        payload = {"summary": candidate_summary(), "candidates": all_candidates()}
        text = json.dumps(payload, indent=2) + "\n"
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text)
        print(text)
        return 0

    if args.command == "license-review":
        records = fetch_default_license_review()
        outputs = write_license_review(records, args.output_dir)
        print(json.dumps(outputs, indent=2))
        return 0 if outputs["summary"]["total"] else 1

    if args.command == "browser-e2e":
        report = run_browser_e2e(args.output_dir, url=args.url, run_external=not args.no_external)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in {"pass", "skip"} else 1

    if args.command == "sandbox-bakeoff":
        report = run_sandbox_bakeoff(args.output_dir, run_external=not args.no_external)
        print(json.dumps(report, indent=2))
        return 0 if report["summary"]["status"] in {"pass", "warn"} else 1

    if args.command == "deep-research-bakeoff":
        report = run_deep_research_bakeoff(args.output_dir, run_external=not args.no_external)
        print(json.dumps(report, indent=2))
        return 0 if report["summary"]["status"] in {"pass", "warn"} else 1

    if args.command == "webapp-smoke":
        report = run_webapp_smoke(args.output_dir)
        print(json.dumps(report, indent=2))
        return 0 if report["status"] == "pass" else 1

    if args.command == "runtime-e2e":
        report = run_runtime_e2e(
            args.output_dir,
            summary_path=args.summary_path,
            run_external=not args.no_external,
            install_timeout=args.install_timeout,
        )
        print(json.dumps(report, indent=2))
        return 0 if report["status"] in {"pass", "blocker", "warn"} else 1

    if args.command == "sandbox-hosting":
        report = run_sandbox_hosting(args.output_dir)
        print(json.dumps(report, indent=2, default=str))
        return 0 if report["status"] in {"pass", "warn"} else 1

    if args.command == "manual-license-review":
        outputs = write_manual_license_review(args.output_dir)
        print(json.dumps(outputs, indent=2, default=str))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
