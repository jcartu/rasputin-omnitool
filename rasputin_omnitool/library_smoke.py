from __future__ import annotations

import json
import sys
import textwrap
import zipfile
from pathlib import Path

from rasputin_omnitool._venv_helpers import (
    DEFAULT_INSTALL_TIMEOUT_SECONDS,
    DEFAULT_RUN_TIMEOUT_SECONDS,
    SCHEMA_VERSION,
    _install_package_if_needed,
    _isolated_env,
    _run_command,
    _utc_now,
    ensure_disposable_venv,
)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_report_markdown(path: Path, title: str, report: dict) -> None:
    blockers = report.get("blockers") or []
    commands = report.get("commands") or []
    lines = [
        f"# {title}",
        "",
        f"Generated: `{report.get('generated_at')}`",
        f"Status: `{report.get('status')}`",
        f"Capability complete: `{report.get('capability_complete')}`",
        "",
        "## Scope",
        "",
        report.get("scope", "n/a"),
        "",
        "## Summary",
        "",
    ]
    for key, value in (report.get("summary") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    if blockers:
        lines.extend(["", "## Blockers / next command", ""])
        for blocker in blockers:
            lines.append(f"- {blocker.get('reason', blocker)}")
            if blocker.get("next_command"):
                lines.append(f"  - Next command: `{blocker['next_command']}`")
            if blocker.get("risk"):
                lines.append(f"  - Risk: {blocker['risk']}")
    if commands:
        lines.extend(["", "## Commands", ""])
        for command in commands:
            ok = command.get("ok")
            rc = command.get("returncode")
            rendered = " ".join(command.get("command") or [])
            lines.append(f"- `{rendered}` -> ok=`{ok}` returncode=`{rc}` timeout=`{command.get('timeout_seconds')}`")
            stderr = command.get("stderr") or ""
            if stderr:
                safe_stderr = stderr[:500].replace("`", "'")
                lines.append(f"  - stderr tail: `{safe_stderr}`")
    lines.extend(["", "## Artifacts", ""])
    for key, value in (report.get("artifacts") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _write_docx_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    document_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    <w:p><w:r><w:t>Rasputin Omnitool Docling Fixture</w:t></w:r></w:p>
    <w:p><w:r><w:t>Docling should parse this local DOCX fixture without external credentials.</w:t></w:r></w:p>
    <w:p><w:r><w:t>The document mentions Crawl4AI, Playwright MCP, sandbox runtimes, and durable reports.</w:t></w:r></w:p>
    <w:sectPr/>
  </w:body>
</w:document>
"""
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
</Types>
""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>
""",
        "word/document.xml": document_xml,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def _write_html_fixture(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """<!doctype html>
<html><head><meta charset="utf-8"><title>Rasputin Omnitool Runtime E2E Fixture</title></head>
<body>
<h1>Rasputin Omnitool Runtime E2E Fixture</h1>
<p>Docling and Crawl4AI should be able to process this local static page.</p>
<p>The fixture contains citations for Playwright MCP, Docling, Crawl4AI, and microsandbox.</p>
<a href="https://github.com/docling-project/docling">Docling</a>
<a href="https://github.com/unclecode/crawl4ai">Crawl4AI</a>
</body></html>
""",
        encoding="utf-8",
    )


def _base_runtime_report(name: str, output_dir: Path, *, status: str, scope: str) -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "name": name,
        "status": status,
        "scope": scope,
        "capability_complete": False,
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
            "cache_isolation": "PIP/XDG/HOME/HF/Playwright/npm caches point under the runtime-e2e output directory",
        },
    }


def _write_single_runtime_report(output_dir: Path, report: dict, title: str, stem: str) -> dict:
    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"
    report["artifacts"]["report_json"] = str(json_path)
    report["artifacts"]["report_markdown"] = str(md_path)
    _write_json(json_path, report)
    _write_report_markdown(md_path, title, report)
    _write_json(json_path, report)
    return report


def run_docling_fixture_parse_e2e(
    output_dir: str | Path,
    *,
    venv_python: str | Path | None = None,
    run_external: bool = True,
    install_timeout: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = _base_runtime_report(
        "docling_fixture_parse",
        output_dir,
        status="blocker",
        scope="actual Docling package install/import plus local DOCX/HTML fixture parse in disposable venv",
    )
    report["candidate"] = "Docling"
    report["capability"] = "deep_research_document_parsing"
    fixture_dir = output_dir / "fixtures" / "docling"
    docx_path = fixture_dir / "become-manus-docling-fixture.docx"
    html_path = fixture_dir / "become-manus-docling-fixture.html"
    markdown_path = output_dir / "docling-extracted.md"
    parse_payload_path = output_dir / "docling-parse-payload.json"
    script_path = output_dir / "scripts" / "docling_fixture_parse.py"
    _write_docx_fixture(docx_path)
    _write_html_fixture(html_path)
    report["artifacts"].update(
        {
            "fixture_docx": str(docx_path),
            "fixture_html": str(html_path),
            "extracted_markdown": str(markdown_path),
            "parse_payload_json": str(parse_payload_path),
            "parse_script": str(script_path),
        }
    )
    if not run_external:
        report["summary"] = {"attempted_install": False, "attempted_parse": False, "reason": "external install disabled"}
        report["blockers"].append(
            {
                "reason": "Schema-only run skipped Docling installation and parsing.",
                "next_command": f"{Path(sys.executable)} -m rasputin_omnitool library-smoke --output-dir {output_dir}",
                "risk": "Installs Docling inside the disposable runtime-e2e venv and may download package/model artifacts into the output-local cache.",
            }
        )
        return _write_single_runtime_report(output_dir, report, "Docling Fixture Parse E2E", "docling-fixture-parse")

    if venv_python is None:
        venv = ensure_disposable_venv(output_dir)
        report["commands"].extend(venv.get("commands", []))
        if venv["status"] != "pass":
            report["summary"] = {"attempted_install": False, "attempted_parse": False, "reason": "venv creation failed"}
            report["blockers"].append({"reason": "Disposable venv creation failed; see command output."})
            return _write_single_runtime_report(output_dir, report, "Docling Fixture Parse E2E", "docling-fixture-parse")
        venv_python = venv["python"]
    venv_python_path = Path(venv_python)
    ok, install_commands = _install_package_if_needed(
        venv_python=venv_python_path,
        output_dir=output_dir,
        package="docling",
        import_name="docling",
        timeout=install_timeout,
    )
    report["commands"].extend(install_commands)
    if not ok:
        report["summary"] = {"attempted_install": True, "install_ok": False, "attempted_parse": False}
        report["blockers"].append(
            {
                "reason": "Docling package installation or import failed inside the disposable venv.",
                "next_command": f"{venv_python_path} -m pip install --no-input --no-cache-dir docling",
                "risk": "Package install may be dependency-heavy; keep PIP_CACHE_DIR/HOME/XDG_CACHE_HOME pointed at runtime-e2e to avoid global cache mutation.",
            }
        )
        return _write_single_runtime_report(output_dir, report, "Docling Fixture Parse E2E", "docling-fixture-parse")

    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        textwrap.dedent(
            """
            import json
            import sys
            import traceback
            from pathlib import Path

            from docling.document_converter import DocumentConverter

            sources = [Path(sys.argv[1]), Path(sys.argv[2])]
            markdown_path = Path(sys.argv[3])
            payload_path = Path(sys.argv[4])
            errors = []
            best = None
            converter = DocumentConverter()
            for source in sources:
                try:
                    result = converter.convert(source)
                    markdown = result.document.export_to_markdown()
                    contains = {
                        "rasputin_omnitool": "Rasputin Omnitool" in markdown,
                        "docling": "Docling" in markdown,
                    }
                    current = {
                        "source": str(source),
                        "markdown_chars": len(markdown),
                        "contains": contains,
                        "markdown": markdown,
                    }
                    if all(contains.values()) and len(markdown) > 20:
                        best = current
                        break
                    if best is None:
                        best = current
                except Exception as exc:
                    errors.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
            ok = bool(best and all(best["contains"].values()) and best["markdown_chars"] > 20)
            if best:
                markdown_path.write_text(best["markdown"], encoding="utf-8")
            payload = {
                "ok": ok,
                "best_source": best["source"] if best else None,
                "markdown_chars": best["markdown_chars"] if best else 0,
                "contains": best["contains"] if best else {},
                "errors": errors,
            }
            payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
            print(json.dumps(payload, sort_keys=True))
            raise SystemExit(0 if ok else 2)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    parse = _run_command(
        [venv_python_path, script_path, docx_path, html_path, markdown_path, parse_payload_path],
        env=_isolated_env(output_dir),
        timeout=DEFAULT_RUN_TIMEOUT_SECONDS,
    )
    report["commands"].append(parse)
    payload = {}
    if parse_payload_path.exists():
        try:
            payload = json.loads(parse_payload_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload = {"ok": False, "error": f"JSONDecodeError: {exc}"}
    status = "pass" if parse["ok"] and payload.get("ok") else "blocker"
    report["status"] = status
    report["capability_complete"] = status == "pass"
    report["summary"] = {
        "attempted_install": True,
        "install_ok": True,
        "attempted_parse": True,
        "parse_ok": bool(payload.get("ok")),
        "best_source": payload.get("best_source"),
        "markdown_chars": payload.get("markdown_chars", 0),
    }
    if status != "pass":
        report["blockers"].append(
            {
                "reason": "Docling installed, but local fixture parsing did not produce the expected markers.",
                "next_command": f"{venv_python_path} {script_path} {docx_path} {html_path} {markdown_path} {parse_payload_path}",
                "risk": "Read the parse payload first; failures may reflect unsupported minimal DOCX/HTML fixture or additional Docling runtime assets.",
            }
        )
    return _write_single_runtime_report(output_dir, report, "Docling Fixture Parse E2E", "docling-fixture-parse")


def run_crawl4ai_fixture_crawl_e2e(
    output_dir: str | Path,
    *,
    venv_python: str | Path | None = None,
    run_external: bool = True,
    install_timeout: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = _base_runtime_report(
        "crawl4ai_fixture_crawl",
        output_dir,
        status="blocker",
        scope="actual Crawl4AI package install/import plus local static-page crawl with Playwright browser cache isolated under runtime-e2e",
    )
    report["candidate"] = "Crawl4AI"
    report["capability"] = "deep_research_static_page_crawl"
    fixture_dir = output_dir / "fixtures" / "crawl4ai"
    html_path = fixture_dir / "index.html"
    markdown_path = output_dir / "crawl4ai-extracted.md"
    crawl_payload_path = output_dir / "crawl4ai-crawl-payload.json"
    script_path = output_dir / "scripts" / "crawl4ai_fixture_crawl.py"
    _write_html_fixture(html_path)
    report["artifacts"].update(
        {
            "fixture_html": str(html_path),
            "extracted_markdown": str(markdown_path),
            "crawl_payload_json": str(crawl_payload_path),
            "crawl_script": str(script_path),
            "playwright_browsers_path": str(output_dir / "playwright-browsers"),
        }
    )
    if not run_external:
        report["summary"] = {"attempted_install": False, "attempted_crawl": False, "reason": "external install disabled"}
        report["blockers"].append(
            {
                "reason": "Schema-only run skipped Crawl4AI installation and static-page crawling.",
                "next_command": f"{Path(sys.executable)} -m rasputin_omnitool library-smoke --output-dir {output_dir}",
                "risk": "Installs Crawl4AI in the disposable venv. Browser binaries must remain under PLAYWRIGHT_BROWSERS_PATH inside runtime-e2e; do not run global playwright install.",
            }
        )
        return _write_single_runtime_report(output_dir, report, "Crawl4AI Fixture Crawl E2E", "crawl4ai-fixture-crawl")

    if venv_python is None:
        venv = ensure_disposable_venv(output_dir)
        report["commands"].extend(venv.get("commands", []))
        if venv["status"] != "pass":
            report["summary"] = {"attempted_install": False, "attempted_crawl": False, "reason": "venv creation failed"}
            report["blockers"].append({"reason": "Disposable venv creation failed; see command output."})
            return _write_single_runtime_report(output_dir, report, "Crawl4AI Fixture Crawl E2E", "crawl4ai-fixture-crawl")
        venv_python = venv["python"]
    venv_python_path = Path(venv_python)
    ok, install_commands = _install_package_if_needed(
        venv_python=venv_python_path,
        output_dir=output_dir,
        package="crawl4ai",
        import_name="crawl4ai",
        timeout=install_timeout,
    )
    report["commands"].extend(install_commands)
    if not ok:
        report["summary"] = {"attempted_install": True, "install_ok": False, "attempted_crawl": False}
        report["blockers"].append(
            {
                "reason": "Crawl4AI package installation or import failed inside the disposable venv.",
                "next_command": f"{venv_python_path} -m pip install --no-input --no-cache-dir crawl4ai",
                "risk": "Package install may be dependency-heavy; keep PIP_CACHE_DIR/HOME/XDG_CACHE_HOME pointed at runtime-e2e to avoid global cache mutation.",
            }
        )
        return _write_single_runtime_report(output_dir, report, "Crawl4AI Fixture Crawl E2E", "crawl4ai-fixture-crawl")

    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(
        textwrap.dedent(
            """
            import asyncio
            import contextlib
            import json
            import sys
            import threading
            import traceback
            from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
            from pathlib import Path

            fixture_dir = Path(sys.argv[1])
            markdown_path = Path(sys.argv[2])
            payload_path = Path(sys.argv[3])

            class QuietHandler(SimpleHTTPRequestHandler):
                def __init__(self, *args, **kwargs):
                    super().__init__(*args, directory=str(fixture_dir), **kwargs)
                def log_message(self, format, *args):
                    pass

            def extract_markdown(result):
                markdown = getattr(result, "markdown", "")
                if hasattr(markdown, "raw_markdown"):
                    return markdown.raw_markdown or ""
                if markdown is None:
                    return ""
                return str(markdown)

            async def crawl(url):
                from crawl4ai import AsyncWebCrawler
                try:
                    from crawl4ai import BrowserConfig
                except Exception:
                    BrowserConfig = None
                try:
                    from crawl4ai import CrawlerRunConfig, CacheMode
                except Exception:
                    CrawlerRunConfig = None
                    CacheMode = None

                errors = []
                crawler_factories = []
                if BrowserConfig is not None:
                    try:
                        browser_config = BrowserConfig(headless=True, verbose=False)
                    except TypeError:
                        browser_config = BrowserConfig(headless=True)
                    crawler_factories.extend([
                        lambda: AsyncWebCrawler(config=browser_config),
                        lambda: AsyncWebCrawler(browser_config=browser_config),
                    ])
                crawler_factories.extend([
                    lambda: AsyncWebCrawler(headless=True, verbose=False),
                    lambda: AsyncWebCrawler(),
                ])
                run_configs = [None]
                if CrawlerRunConfig is not None:
                    try:
                        cache_mode = CacheMode.BYPASS if CacheMode is not None else None
                        run_configs.insert(0, CrawlerRunConfig(cache_mode=cache_mode))
                    except Exception:
                        pass

                for make_crawler in crawler_factories:
                    try:
                        async with make_crawler() as crawler:
                            for run_config in run_configs:
                                try:
                                    if run_config is not None:
                                        result = await crawler.arun(url=url, config=run_config)
                                    else:
                                        result = await crawler.arun(url=url)
                                    markdown = extract_markdown(result)
                                    success = bool(getattr(result, "success", True))
                                    contains = {
                                        "rasputin_omnitool": "Rasputin Omnitool" in markdown,
                                        "crawl4ai": "Crawl4AI" in markdown,
                                    }
                                    return {
                                        "ok": success and all(contains.values()) and len(markdown) > 20,
                                        "success": success,
                                        "url": url,
                                        "markdown_chars": len(markdown),
                                        "contains": contains,
                                        "error_message": getattr(result, "error_message", None),
                                        "markdown": markdown,
                                        "attempt_errors": errors,
                                    }
                                except Exception as exc:
                                    errors.append({"phase": "arun", "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
                    except Exception as exc:
                        errors.append({"phase": "crawler_context", "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
                return {"ok": False, "url": url, "markdown_chars": 0, "contains": {}, "attempt_errors": errors}

            server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
            try:
                payload = asyncio.run(crawl(url))
            except Exception as exc:
                payload = {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]}
            finally:
                with contextlib.suppress(Exception):
                    server.shutdown()
                with contextlib.suppress(Exception):
                    server.server_close()
            if payload.get("markdown"):
                markdown_path.write_text(payload["markdown"], encoding="utf-8")
                payload.pop("markdown", None)
            payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\\n", encoding="utf-8")
            print(json.dumps(payload, sort_keys=True))
            raise SystemExit(0 if payload.get("ok") else 2)
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )
    crawl = _run_command(
        [venv_python_path, script_path, fixture_dir, markdown_path, crawl_payload_path],
        env=_isolated_env(output_dir),
        timeout=DEFAULT_RUN_TIMEOUT_SECONDS,
    )
    report["commands"].append(crawl)
    payload = {}
    if crawl_payload_path.exists():
        try:
            payload = json.loads(crawl_payload_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            payload = {"ok": False, "error": f"JSONDecodeError: {exc}"}
    status = "pass" if crawl["ok"] and payload.get("ok") else "blocker"
    report["status"] = status
    report["capability_complete"] = status == "pass"
    report["summary"] = {
        "attempted_install": True,
        "install_ok": True,
        "attempted_crawl": True,
        "crawl_ok": bool(payload.get("ok")),
        "url": payload.get("url"),
        "markdown_chars": payload.get("markdown_chars", 0),
        "playwright_browsers_path": str(output_dir / "playwright-browsers"),
    }
    if status != "pass":
        report["blockers"].append(
            {
                "reason": "Crawl4AI installed, but the static-page crawl did not complete in the isolated browser/cache environment.",
                "next_command": f"PLAYWRIGHT_BROWSERS_PATH={output_dir / 'playwright-browsers'} {venv_python_path} -m playwright install chromium",
                "risk": "Downloads Chromium browser assets. This is safe only if PLAYWRIGHT_BROWSERS_PATH remains under runtime-e2e; a global playwright install would mutate the user/system browser cache.",
            }
        )
        report["blockers"].append(
            {
                "reason": "After local browser assets exist, re-run the Crawl4AI fixture script.",
                "next_command": f"{venv_python_path} {script_path} {fixture_dir} {markdown_path} {crawl_payload_path}",
                "risk": "Starts a local loopback HTTP server and a headless browser process; should remain non-destructive but can consume CPU/memory.",
            }
        )
    return _write_single_runtime_report(output_dir, report, "Crawl4AI Fixture Crawl E2E", "crawl4ai-fixture-crawl")
