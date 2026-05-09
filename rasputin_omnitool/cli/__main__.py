from __future__ import annotations

import argparse
import json
from pathlib import Path

from rasputin_omnitool.bakeoff import run_deep_research_bakeoff, run_sandbox_bakeoff
from rasputin_omnitool.catalog import all_candidates, candidate_summary
from rasputin_omnitool.library_smoke import run_crawl4ai_fixture_crawl_e2e, run_docling_fixture_parse_e2e
from rasputin_omnitool.licenses import fetch_default_license_review, write_license_review
from rasputin_omnitool.licenses_manual import write_manual_license_review


def _status_code(report: dict) -> int:
    return 0 if report.get("summary", {}).get("status") in {"pass", "warn"} else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m rasputin_omnitool",
        description="Rasputin Omnitool kernel: catalog, license review, bakeoff, and library smoke",
    )
    sub = parser.add_subparsers(dest="command", required=False)

    matrix = sub.add_parser("matrix", help="print OSS candidate catalog JSON")
    matrix.add_argument("--output", default=None)

    license_review = sub.add_parser("license-review", help="fetch GitHub license metadata for top candidates")
    license_review.add_argument("--output-dir", default="outputs/rasputin-omnitool")

    manual_license = sub.add_parser("manual-license-review", help="write manual license review for dual-licensed projects")
    manual_license.add_argument("--output-dir", default="outputs/rasputin-omnitool")

    bakeoff = sub.add_parser("bakeoff", help="run sandbox and deep-research candidate bakeoffs")
    bakeoff.add_argument("--output-dir", default="outputs/rasputin-omnitool")
    bakeoff.add_argument("--no-external", action="store_true", help="skip GitHub/npm/PyPI metadata commands")

    library_smoke = sub.add_parser("library-smoke", help="run Docling and Crawl4AI isolated library smoke checks")
    library_smoke.add_argument("--output-dir", default="outputs/rasputin-omnitool/library-smoke")
    library_smoke.add_argument("--no-external", action="store_true", help="write schema/blocker reports without package installs")
    library_smoke.add_argument("--install-timeout", type=int, default=600, help="per-package install timeout in seconds")

    args = parser.parse_args(argv)

    if args.command == "matrix":
        payload = {"summary": candidate_summary(), "candidates": all_candidates()}
        text = json.dumps(payload, indent=2) + "\n"
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(text, encoding="utf-8")
        print(text, end="")
        return 0

    if args.command == "license-review":
        records = fetch_default_license_review()
        outputs = write_license_review(records, args.output_dir)
        print(json.dumps(outputs, indent=2))
        return 0 if outputs["summary"]["total"] else 1

    if args.command == "manual-license-review":
        outputs = write_manual_license_review(args.output_dir)
        print(json.dumps(outputs, indent=2, default=str))
        return 0

    if args.command == "bakeoff":
        sandbox = run_sandbox_bakeoff(args.output_dir, run_external=not args.no_external)
        deep_research = run_deep_research_bakeoff(args.output_dir, run_external=not args.no_external)
        payload = {"sandbox": sandbox, "deep_research": deep_research}
        print(json.dumps(payload, indent=2))
        return 0 if _status_code(sandbox) == 0 and _status_code(deep_research) == 0 else 1

    if args.command == "library-smoke":
        output_dir = Path(args.output_dir)
        docling = run_docling_fixture_parse_e2e(
            output_dir / "docling",
            run_external=not args.no_external,
            install_timeout=args.install_timeout,
        )
        crawl4ai = run_crawl4ai_fixture_crawl_e2e(
            output_dir / "crawl4ai",
            run_external=not args.no_external,
            install_timeout=args.install_timeout,
        )
        payload = {"docling": docling, "crawl4ai": crawl4ai}
        print(json.dumps(payload, indent=2))
        return 0 if all(report["status"] in {"pass", "blocker"} for report in payload.values()) else 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
