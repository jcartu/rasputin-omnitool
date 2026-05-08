#!/usr/bin/env python3
"""Browser Workflow E2E Test - minimal Playwright sync API.

Workflows:
  1. Navigate to example.com, extract page title and all links.
  2. Navigate to github.com/docling-project/docling, extract repo name, star count, description.
  3. Navigate to google.com/search?q=become+manus+oss (fallback DuckDuckGo), extract top 3 result titles.

Reports written to:
  /home/josh/workspace/outputs/become-manus/browser-workflow-e2e.json
  /home/josh/workspace/outputs/become-manus/browser-workflow-e2e.md
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# Ensure Playwright browsers are found
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/home/josh/workspace/outputs/become-manus/runtime-e2e/playwright-browsers"

from playwright.sync_api import sync_playwright  # noqa: E402

OUTPUT_DIR = Path("/home/josh/workspace/outputs/become-manus")
REPORT_JSON = OUTPUT_DIR / "browser-workflow-e2e.json"
REPORT_MD = OUTPUT_DIR / "browser-workflow-e2e.md"


def test_example_com(page):
    """Navigate to example.com, extract title and all links."""
    page.goto("https://example.com", timeout=30000)
    title = page.title()
    links = page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => ({href: a.href, text: a.textContent.trim()}))")
    return {
        "title": title,
        "links": links,
        "link_count": len(links),
    }


def test_github_docling(page):
    """Navigate to GitHub docling repo, extract repo name, stars, description."""
    page.goto("https://github.com/docling-project/docling", timeout=30000)
    # Repo name: from <title> (e.g. "docling-project/docling") or from h1
    title = page.title()
    repo_name = title.split(" · ")[0].strip() if " · " in title else title

    # Star count: look for the stars link text
    star_count = ""
    try:
        star_el = page.locator("a[href$='/stargazers']").first
        if star_el.is_visible(timeout=5000):
            star_count = star_el.inner_text().strip()
    except Exception:
        pass

    # Description: from the meta description tag or from the page content
    description = page.evaluate("() => { const m = document.querySelector('meta[name=\"description\"]'); return m ? m.getAttribute('content') : ''; }")
    if not description:
        try:
            desc_el = page.locator("p.f5.color-fg-muted").first
            if desc_el.is_visible(timeout=5000):
                description = desc_el.inner_text().strip()
        except Exception:
            pass

    return {
        "repo_name": repo_name,
        "star_count": star_count,
        "description": description,
    }


def test_google_search(page):
    """Search for 'become manus oss', extract top 3 result titles. Fallback to DuckDuckGo if blocked."""
    google_url = "https://www.google.com/search?q=become+manus+oss"
    page.goto(google_url, timeout=30000)

    # Check if we hit a CAPTCHA or reCAPTCHA
    body_text = page.inner_text("body", timeout=5000)
    captcha_words = ["verify you are a human", "recaptcha", "please verify", "unusual traffic"]
    blocked = any(w in body_text.lower() for w in captcha_words)

    if blocked:
        # Fallback to DuckDuckGo
        page.goto("https://duckduckgo.com/?q=become+manus+oss", timeout=30000)
        return _extract_search_results(page, "duckduckgo")

    return _extract_search_results(page, "google")


def _extract_search_results(page, engine):
    """Extract top search result titles."""
    titles = []

    if engine == "google":
        # Google search results are in h3 tags
        try:
            titles = page.evaluate("""() => {
                const els = document.querySelectorAll('h3');
                return Array.from(els).slice(0, 5).map(e => e.textContent.trim()).filter(t => t.length > 5);
            }""")
        except Exception:
            pass

    else:
        # DuckDuckGo - try multiple selector strategies
        # Strategy 1: result__a links
        try:
            titles = page.evaluate("""() => {
                const els = document.querySelectorAll('a.result__snippet, a.result__a, article.result a[href]');
                return Array.from(els).slice(0, 5).map(e => {
                    const h2 = e.parentElement ? e.parentElement.querySelector('h2') : null;
                    return h2 ? h2.textContent.trim() : e.textContent.trim().substring(0, 100);
                }).filter(t => t && t.length > 5);
            }""")
        except Exception:
            pass

        # Strategy 2: all h2 tags in main
        if not titles:
            try:
                titles = page.evaluate("""() => {
                    const main = document.querySelector('main, #results');
                    if (!main) return [];
                    const els = main.querySelectorAll('h2');
                    return Array.from(els).slice(0, 5).map(e => e.textContent.trim()).filter(t => t.length > 5);
                }""")
            except Exception:
                pass

        # Strategy 3: broader - any meaningful heading text
        if not titles:
            try:
                titles = page.evaluate("""() => {
                    const all = document.querySelectorAll('h1, h2, h3, h4');
                    const seen = new Set();
                    const result = [];
                    for (const el of all) {
                        const t = el.textContent.trim();
                        if (t.length > 10 && t.length < 200 && !seen.has(t)) {
                            seen.add(t);
                            result.push(t);
                        }
                        if (result.length >= 3) break;
                    }
                    return result;
                }""")
            except Exception:
                pass

    return {
        "engine": engine,
        "titles": titles,
        "title_count": len(titles),
        "blocked_by_captcha": engine != "google",
    }


def run_tests():
    """Run all browser workflow tests and return results."""
    results = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "workflows": {},
        "safety": {
            "headless": True,
            "no_persistence": True,
            "isolated_context": True,
        },
    }

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        # Test 1: example.com
        try:
            data = test_example_com(page)
            passed = bool(data.get("title")) and data.get("link_count", 0) >= 1
            results["workflows"]["example_com"] = {
                "name": "example.com title and links",
                "status": "pass" if passed else "fail",
                "passed": passed,
                "url": "https://example.com",
                "data": data,
            }
        except Exception as e:
            results["workflows"]["example_com"] = {
                "name": "example.com title and links",
                "status": "error",
                "passed": False,
                "url": "https://example.com",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

        # Test 2: GitHub docling
        try:
            data = test_github_docling(page)
            passed = bool(data.get("repo_name")) and bool(data.get("star_count"))
            results["workflows"]["github_docling"] = {
                "name": "github docling repo extraction",
                "status": "pass" if passed else "fail",
                "passed": passed,
                "url": "https://github.com/docling-project/docling",
                "data": data,
            }
        except Exception as e:
            results["workflows"]["github_docling"] = {
                "name": "github docling repo extraction",
                "status": "error",
                "passed": False,
                "url": "https://github.com/docling-project/docling",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

        # Test 3: Google search
        try:
            data = test_google_search(page)
            passed = data.get("title_count", 0) >= 1
            results["workflows"]["google_search"] = {
                "name": "google search become manus oss",
                "status": "pass" if passed else ("partial" if data.get("blocked_by_captcha") else "fail"),
                "passed": passed,
                "url": "https://www.google.com/search?q=become+manus+oss",
                "data": data,
            }
        except Exception as e:
            results["workflows"]["google_search"] = {
                "name": "google search become manus oss",
                "status": "error",
                "passed": False,
                "url": "https://www.google.com/search?q=become+manus+oss",
                "error": str(e),
                "traceback": traceback.format_exc(),
            }

        browser.close()

    return results


def generate_reports(results):
    """Write JSON and markdown reports."""
    # JSON report
    REPORT_JSON.write_text(json.dumps(results, indent=2) + "\n")

    # Summary stats
    workflows = results["workflows"]
    total = len(workflows)
    passed = sum(1 for w in workflows.values() if w.get("passed"))
    failed = total - passed
    all_passed = failed == 0

    # Markdown report
    md_lines = []
    md_lines.append("# Browser Workflow E2E Tests")
    md_lines.append("")
    md_lines.append(f"Generated: `{results['generated_at']}`")
    md_lines.append(f"Status: `{'pass' if all_passed else 'fail'}`")
    md_lines.append(f"Capability complete: `{all_passed}`")
    md_lines.append("")
    md_lines.append("## Scope")
    md_lines.append("")
    md_lines.append("Real browser E2E tests: (1) navigate to example.com and extract title + links, (2) navigate to github.com/docling-project/docling and extract repo name, star count, description, (3) search for 'become manus oss' and extract top 3 result titles")
    md_lines.append("")
    md_lines.append("## Summary")
    md_lines.append("")
    md_lines.append("- `playwright_import`: `ok`")
    md_lines.append("- `test_script_executed`: `True`")
    md_lines.append(f"- `test_count`: `{total}`")
    md_lines.append(f"- `pass_count`: `{passed}`")
    md_lines.append(f"- `fail_count`: `{failed}`")
    md_lines.append(f"- `all_passed`: `{all_passed}`")
    for key in ["example_com", "github_docling", "google_search"]:
        if key in workflows:
            md_lines.append(f"- `{key}_status`: `{workflows[key]['status']}`")
    md_lines.append("")
    md_lines.append("## Safety")
    md_lines.append("")
    for k, v in results.get("safety", {}).items():
        md_lines.append(f"- `{k}`: `{v}`")
    md_lines.append("")
    md_lines.append("## Test Results")
    md_lines.append("")

    for key, wf in workflows.items():
        status_icon = "PASS" if wf.get("passed") else ("PARTIAL" if wf.get("status") == "partial" else "FAIL")
        md_lines.append(f"### {status_icon} - {wf['name']}")
        md_lines.append("")
        md_lines.append(f"- **status**: `{wf['status']}`")
        md_lines.append(f"- **passed**: `{wf.get('passed', False)}`")
        md_lines.append(f"- **url**: `{wf['url']}`")

        if "data" in wf:
            md_lines.append("")
            md_lines.append("**Extracted data:**")
            md_lines.append("")
            data = wf["data"]
            for dk, dv in data.items():
                if isinstance(dv, list):
                    md_lines.append(f"- `{dk}`: `{len(dv)} items`")
                    if dk == "links":
                        for link in dv:
                            md_lines.append(f"  - [{link.get('text', '')}]({link.get('href', '')})")
                    elif dk == "titles":
                        for i, t in enumerate(dv, 1):
                            md_lines.append(f"  - {i}. `{t}`")
                    else:
                        md_lines.append(f"  - `{json.dumps(dv)}`")
                elif isinstance(dv, bool):
                    md_lines.append(f"- `{dk}`: `{dv}`")
                else:
                    md_lines.append(f"- `{dk}`: `{dv}`")

        if "error" in wf:
            md_lines.append("")
            md_lines.append(f"**Error:** `{wf['error']}`")

        md_lines.append("")

    # Write markdown
    REPORT_MD.write_text("\n".join(md_lines))


def main():
    print("Starting browser workflow E2E tests...")
    results = run_tests()
    generate_reports(results)
    print("Reports written to:")
    print(f"  JSON: {REPORT_JSON}")
    print(f"  MD:   {REPORT_MD}")

    for key, wf in results["workflows"].items():
        status = "PASS" if wf.get("passed") else ("PARTIAL" if wf.get("status") == "partial" else "FAIL")
        print(f"  [{status}] {wf['name']}")

    all_pass = all(wf.get("passed") for wf in results["workflows"].values())
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
