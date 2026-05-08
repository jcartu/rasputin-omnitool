from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

SCHEMA_VERSION = 1
DEFAULT_INSTALL_TIMEOUT_SECONDS = 600
DEFAULT_RUN_TIMEOUT_SECONDS = 180


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _trim(text: str | bytes | None, limit: int = 8000) -> str:
    if text is None:
        return ""
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _isolated_env(output_dir: Path) -> dict[str, str]:
    """Return an environment that keeps package/runtime caches under output_dir."""
    cache_dir = output_dir / "cache"
    env = os.environ.copy()
    env.update(
        {
            "PYTHONNOUSERSITE": "1",
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_CACHE_DIR": str(output_dir / "pip-cache"),
            "XDG_CACHE_HOME": str(cache_dir),
            "HOME": str(output_dir / "home"),
            "HF_HOME": str(cache_dir / "huggingface"),
            "TRANSFORMERS_CACHE": str(cache_dir / "huggingface" / "transformers"),
            "DOCLING_CACHE_DIR": str(cache_dir / "docling"),
            "CRAWL4AI_HOME": str(output_dir / "crawl4ai-home"),
            "PLAYWRIGHT_BROWSERS_PATH": str(output_dir / "playwright-browsers"),
            "NPM_CONFIG_CACHE": str(output_dir / "npm-cache"),
        }
    )
    for path in [
        cache_dir,
        Path(env["PIP_CACHE_DIR"]),
        Path(env["HOME"]),
        Path(env["HF_HOME"]),
        Path(env["CRAWL4AI_HOME"]),
        Path(env["PLAYWRIGHT_BROWSERS_PATH"]),
        Path(env["NPM_CONFIG_CACHE"]),
    ]:
        path.mkdir(parents=True, exist_ok=True)
    return env


def _run_command(
    command: Sequence[str | Path],
    *,
    cwd: str | Path | None = None,
    env: dict[str, str] | None = None,
    timeout: int = DEFAULT_RUN_TIMEOUT_SECONDS,
) -> dict:
    command_list = [str(item) for item in command]
    try:
        result = subprocess.run(
            command_list,
            cwd=str(cwd) if cwd is not None else None,
            env=env,
            text=True,
            capture_output=True,
            timeout=timeout,
        )
        return {
            "command": command_list,
            "ok": result.returncode == 0,
            "returncode": result.returncode,
            "stdout": _trim(result.stdout),
            "stderr": _trim(result.stderr),
            "timeout_seconds": timeout,
        }
    except FileNotFoundError as exc:
        return {
            "command": command_list,
            "ok": False,
            "returncode": None,
            "stdout": "",
            "stderr": f"FileNotFoundError: {exc}",
            "timeout_seconds": timeout,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "command": command_list,
            "ok": False,
            "returncode": None,
            "stdout": _trim(exc.stdout),
            "stderr": f"timeout after {timeout}s; {_trim(exc.stderr)}".strip(),
            "timeout_seconds": timeout,
        }


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
    <w:p><w:r><w:t>Become Manus Docling Fixture</w:t></w:r></w:p>
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
<html><head><meta charset="utf-8"><title>Become Manus Runtime E2E Fixture</title></head>
<body>
<h1>Become Manus Runtime E2E Fixture</h1>
<p>Docling and Crawl4AI should be able to process this local static page.</p>
<p>The fixture contains citations for Playwright MCP, Docling, Crawl4AI, and microsandbox.</p>
<a href="https://github.com/docling-project/docling">Docling</a>
<a href="https://github.com/unclecode/crawl4ai">Crawl4AI</a>
</body></html>
""",
        encoding="utf-8",
    )


def _venv_python(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def ensure_disposable_venv(output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    venv_dir = output_dir / ".venv"
    python_path = _venv_python(venv_dir)
    commands: list[dict] = []
    env = _isolated_env(output_dir)
    if not python_path.exists():
        commands.append(_run_command([sys.executable, "-m", "venv", str(venv_dir)], env=env, timeout=180))
    if python_path.exists():
        pip_check = _run_command([python_path, "-m", "pip", "--version"], env=env, timeout=60)
        commands.append(pip_check)
        if not pip_check["ok"]:
            commands.append(_run_command([python_path, "-m", "ensurepip", "--upgrade"], env=env, timeout=180))
            commands.append(_run_command([python_path, "-m", "pip", "--version"], env=env, timeout=60))
    ok = python_path.exists() and bool(commands) and commands[-1].get("ok")
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "status": "pass" if ok else "fail",
        "venv_dir": str(venv_dir),
        "python": str(python_path),
        "commands": commands,
    }


def _import_check(venv_python: Path, import_name: str, env: dict[str, str]) -> dict:
    return _run_command(
        [venv_python, "-c", f"import {import_name}; print(getattr({import_name}, '__version__', 'import-ok'))"],
        env=env,
        timeout=60,
    )


def _install_package_if_needed(
    *,
    venv_python: Path,
    output_dir: Path,
    package: str,
    import_name: str,
    timeout: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> tuple[bool, list[dict]]:
    env = _isolated_env(output_dir)
    commands: list[dict] = []
    before = _import_check(venv_python, import_name, env)
    commands.append(before)
    if before["ok"]:
        return True, commands
    install = _run_command(
        [venv_python, "-m", "pip", "install", "--no-input", "--no-cache-dir", package],
        env=env,
        timeout=timeout,
    )
    commands.append(install)
    if not install["ok"]:
        return False, commands
    after = _import_check(venv_python, import_name, env)
    commands.append(after)
    return after["ok"], commands


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
                "next_command": f"{Path(sys.executable)} -m become_manus runtime-e2e --output-dir {output_dir} --summary-path {output_dir.parent / 'runtime-e2e-report.md'}",
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
                        "become_manus": "Become Manus" in markdown,
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
                "next_command": f"{Path(sys.executable)} -m become_manus runtime-e2e --output-dir {output_dir} --summary-path {output_dir.parent / 'runtime-e2e-report.md'}",
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
                                        "become_manus": "Become Manus" in markdown,
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


def run_sandbox_runtime_smoke_blocker(output_dir: str | Path, *, run_external: bool = True) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    report = _base_runtime_report(
        "sandbox_runtime_smoke",
        output_dir,
        status="blocker",
        scope="microsandbox or agent-infra/sandbox runtime smoke only if non-destructive host-level runtime start is clearly safe",
    )
    report["candidate"] = "microsandbox or agent-infra/sandbox"
    report["capability"] = "agent_computer_runtime_isolation"
    kvm_path = Path("/dev/kvm")
    report["summary"] = {
        "attempted_runtime_start": False,
        "reason": "No sandbox runtime was started from the scheduled job because the documented next steps start a KVM microVM or Docker container and may download runtime/image assets.",
        "platform": platform.platform(),
        "dev_kvm_exists": kvm_path.exists(),
        "docker_cli_present": shutil.which("docker") is not None,
        "run_external_requested": run_external,
    }
    report["blockers"].extend(
        [
            {
                "reason": "microsandbox README says it boots lightweight VMs locally and requires Linux KVM or Apple Silicon; this cron run did not start a KVM microVM or download OCI/runtime assets.",
                "next_command": f"cd {output_dir} && NPM_CONFIG_CACHE={output_dir / 'npm-cache'} npx --yes microsandbox run debian",
                "risk": "Downloads npm/OCI/runtime artifacts and starts a local KVM microVM. Run only when host resource impact and image downloads are explicitly in scope.",
            },
            {
                "reason": "agent-infra/sandbox quick start requires Docker with seccomp unconfined and a bound localhost service; this is beyond non-destructive cron scope.",
                "next_command": "docker run --security-opt seccomp=unconfined --rm -it -p 8080:8080 ghcr.io/agent-infra/sandbox:latest",
                "risk": "Downloads and starts a privileged-ish all-in-one sandbox container, binds port 8080, and may consume substantial CPU/memory/disk.",
            },
        ]
    )
    return _write_single_runtime_report(output_dir, report, "Sandbox Runtime Smoke Blocker", "sandbox-runtime-smoke")


def _aggregate_status(reports: Sequence[dict]) -> str:
    statuses = [report.get("status") for report in reports]
    if any(status == "fail" for status in statuses):
        return "fail"
    if any(status == "blocker" for status in statuses):
        return "blocker"
    if statuses and all(status == "pass" for status in statuses):
        return "pass"
    return "warn"


def _write_aggregate_markdown(path: Path, aggregate: dict) -> None:
    lines = [
        "# Become Manus Runtime E2E Report",
        "",
        f"Generated: `{aggregate['generated_at']}`",
        f"Status: `{aggregate['status']}`",
        f"Output dir: `{aggregate['output_dir']}`",
        "",
        "## Summary",
        "",
    ]
    for key, value in aggregate["summary"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## E2E reports",
            "",
            "| Name | Status | Capability complete | Report | Notes |",
            "|---|---:|---:|---|---|",
        ]
    )
    for item in aggregate["e2e_reports"]:
        notes = item.get("note") or ""
        lines.append(
            f"| {item['name']} | {item['status']} | {item['capability_complete']} | `{item['report_json']}` | {notes} |"
        )
    lines.extend(["", "## Blockers / exact next commands", ""])
    for item in aggregate["e2e_reports"]:
        blockers = item.get("blockers") or []
        if not blockers:
            continue
        lines.append(f"### {item['name']}")
        for blocker in blockers:
            lines.append(f"- {blocker.get('reason')}")
            if blocker.get("next_command"):
                lines.append(f"  - Next command: `{blocker['next_command']}`")
            if blocker.get("risk"):
                lines.append(f"  - Risk: {blocker['risk']}")
        lines.append("")
    lines.extend(["## Safety", ""])
    for key, value in aggregate["safety"].items():
        lines.append(f"- `{key}`: {value}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def run_runtime_e2e(
    output_dir: str | Path = "outputs/become-manus/runtime-e2e",
    *,
    summary_path: str | Path | None = "outputs/become-manus/runtime-e2e-report.md",
    run_external: bool = True,
    install_timeout: int = DEFAULT_INSTALL_TIMEOUT_SECONDS,
) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    if summary_path is None:
        summary_path = output_dir.parent / "runtime-e2e-report.md"
    summary_path = Path(summary_path)

    venv_report = None
    venv_python = None
    if run_external:
        venv_report = ensure_disposable_venv(output_dir)
        if venv_report["status"] == "pass":
            venv_python = venv_report["python"]

    if run_external and venv_python is None:
        docling = run_docling_fixture_parse_e2e(output_dir, run_external=False)
        docling["summary"]["reason"] = "disposable venv unavailable"
        crawl4ai = run_crawl4ai_fixture_crawl_e2e(output_dir, run_external=False)
        crawl4ai["summary"]["reason"] = "disposable venv unavailable"
    else:
        docling = run_docling_fixture_parse_e2e(
            output_dir,
            venv_python=venv_python,
            run_external=run_external,
            install_timeout=install_timeout,
        )
        crawl4ai = run_crawl4ai_fixture_crawl_e2e(
            output_dir,
            venv_python=venv_python,
            run_external=run_external,
            install_timeout=install_timeout,
        )
    sandbox = run_sandbox_runtime_smoke_blocker(output_dir, run_external=run_external)
    reports = [docling, crawl4ai, sandbox]
    e2e_reports = []
    for report in reports:
        e2e_reports.append(
            {
                "name": report["name"],
                "status": report["status"],
                "capability_complete": report["capability_complete"],
                "report_json": report["artifacts"].get("report_json"),
                "report_markdown": report["artifacts"].get("report_markdown"),
                "blockers": report.get("blockers", []),
                "note": report.get("summary", {}).get("reason", ""),
            }
        )
    status = _aggregate_status(reports)
    status_counts = {"pass": 0, "blocker": 0, "fail": 0, "warn": 0, "skip": 0}
    for report in reports:
        status_counts[report["status"]] = status_counts.get(report["status"], 0) + 1
    summary_json = output_dir / "runtime-e2e-summary.json"
    aggregate = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "status": status,
        "output_dir": str(output_dir),
        "run_external": run_external,
        "summary": {
            "report_count": len(reports),
            "status_counts": status_counts,
            "capability_complete_count": sum(1 for report in reports if report.get("capability_complete")),
            "docling_status": docling["status"],
            "crawl4ai_status": crawl4ai["status"],
            "sandbox_status": sandbox["status"],
        },
        "safety": {
            "venv_dir": str(output_dir / ".venv"),
            "global_python_mutation": "none_intended",
            "system_config_mutation": "none_intended",
            "credential_use": "none",
            "cron_scheduling": "no new cron jobs scheduled",
            "browser_cache": str(output_dir / "playwright-browsers"),
        },
        "venv": venv_report,
        "e2e_reports": e2e_reports,
        "artifacts": {
            "summary_json": str(summary_json),
            "summary_markdown": str(summary_path),
            "docling_report_json": docling["artifacts"].get("report_json"),
            "crawl4ai_report_json": crawl4ai["artifacts"].get("report_json"),
            "sandbox_report_json": sandbox["artifacts"].get("report_json"),
        },
    }
    _write_json(summary_json, aggregate)
    _write_aggregate_markdown(summary_path, aggregate)
    _write_json(summary_json, aggregate)
    return aggregate
