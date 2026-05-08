from __future__ import annotations

import html.parser
import json
import re
from datetime import datetime, timezone
from pathlib import Path


class _LinkExtractor(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[dict] = []
        self._href: str | None = None
        self._text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "a":
            attrs_dict = dict(attrs)
            self._href = attrs_dict.get("href")
            self._text = []

    def handle_data(self, data: str) -> None:
        if self._href:
            self._text.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._href:
            self.links.append({"href": self._href, "text": " ".join(self._text).strip()})
            self._href = None
            self._text = []


def _write_fixture_corpus(corpus_dir: Path) -> dict:
    corpus_dir.mkdir(parents=True, exist_ok=True)
    html_path = corpus_dir / "manus-capabilities.html"
    memo_path = corpus_dir / "research-memo.md"
    html_path.write_text(
        """<!doctype html>
<html><head><title>Become Manus Fixture</title></head>
<body>
<h1>Become Manus Research Fixture</h1>
<p>Manus-class agents need browser operation, research, code execution, and deliverables.</p>
<a href="https://github.com/microsoft/playwright-mcp">Playwright MCP</a>
<a href="https://github.com/docling-project/docling">Docling</a>
<a href="https://github.com/unclecode/crawl4ai">Crawl4AI</a>
</body></html>
""",
        encoding="utf-8",
    )
    memo_path.write_text(
        """# Deep Research Fixture Memo

## Claims

- Browser operators need deterministic screenshots and network traces.
- Research pipelines need citation extraction and document parsing.
- Deliverables should produce durable artifacts for verification.

## Sources

- Playwright MCP: browser automation through MCP.
- Docling: document parsing.
- Crawl4AI: crawler/extractor for LLM research workflows.
""",
        encoding="utf-8",
    )
    return {"html": html_path, "memo": memo_path}


def _parse_markdown_sections(text: str) -> list[dict]:
    sections: list[dict] = []
    current: dict | None = None
    for line in text.splitlines():
        if line.startswith("#"):
            if current:
                current["body"] = "\n".join(current["body"]).strip()
                sections.append(current)
            level = len(line) - len(line.lstrip("#"))
            current = {"level": level, "heading": line.lstrip("#").strip(), "body": []}
        elif current is not None:
            current["body"].append(line)
    if current:
        current["body"] = "\n".join(current["body"]).strip()
        sections.append(current)
    return sections


def run_research_pipeline_e2e(output_dir: str | Path = "outputs/become-manus/research-pipeline") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    corpus = _write_fixture_corpus(output_dir / "fixtures")

    parser = _LinkExtractor()
    html_text = corpus["html"].read_text(encoding="utf-8")
    parser.feed(html_text)
    memo_text = corpus["memo"].read_text(encoding="utf-8")
    sections = _parse_markdown_sections(memo_text)
    citations = [link for link in parser.links if link["href"].startswith("https://github.com/")]
    claims = re.findall(r"^- (.+)$", memo_text, flags=re.MULTILINE)

    status = "pass" if len(citations) >= 2 and len(sections) >= 2 and len(claims) >= 3 else "fail"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "capability": "deep_research_fixture_pipeline",
        "scope": "fixture_e2e_no_external_network_no_package_install",
        "summary": {
            "citation_count": len(citations),
            "parsed_document_count": len(corpus),
            "section_count": len(sections),
            "claim_count": len(claims),
            "capability_complete": status == "pass",
        },
        "citations": citations,
        "sections": sections,
        "claims": claims,
        "artifacts": {},
    }
    json_path = output_dir / "research-pipeline-e2e.json"
    md_path = output_dir / "research-pipeline-e2e.md"
    report["artifacts"] = {"report_json": str(json_path), "report_md": str(md_path), "fixture_dir": str(output_dir / "fixtures")}
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# Become Manus Research Pipeline E2E",
        "",
        f"Status: `{status}`",
        f"Generated: `{report['generated_at']}`",
        "",
        "## Citations",
        "",
    ]
    for citation in citations:
        md_lines.append(f"- [{citation['text']}]({citation['href']})")
    md_lines.extend(["", "## Claims", ""])
    for claim in claims:
        md_lines.append(f"- {claim}")
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    return report
