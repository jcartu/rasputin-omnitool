import json
import re
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright


def trim(s, limit=300):
    if not s:
        return s
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:limit]


def test_example_com(page):
    page.goto('https://example.com', timeout=30000)
    page.wait_for_load_state('domcontentloaded')
    title = page.title()
    links = page.query_selector_all('a')
    link_data = []
    for link in links:
        href = link.get_attribute('href') or ''
        text = (link.inner_text() or '').strip()
        link_data.append({'href': href, 'text': trim(text)})
    return {'title': title, 'link_count': len(link_data), 'links': link_data}


def test_github_docling(page):
    page.goto('https://github.com/docling-project/docling', timeout=30000)
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)

    # Repo name: look for .sr-only span inside h1 (GitHub's repo title)
    repo_name = ''
    sr_only = page.query_selector('h1 .sr-only')
    if sr_only:
        repo_name = sr_only.inner_text().strip()
    if not repo_name:
        page_title = page.title()
        if '/' in page_title:
            repo_name = page_title.split(' - ')[0].strip()

    # Star count
    star_count = ''
    star_elem = page.query_selector("a[href*='/stargazers']")
    if star_elem:
        star_count = star_elem.inner_text().strip()
    if not star_count:
        star_elem = page.query_selector("[data-hydro-click*='stargazers']")
        if star_elem:
            star_count = star_elem.inner_text().strip()

    # Description: try multiple sources
    description = ''
    desc_elem = page.query_selector('.repo-description')
    if desc_elem:
        description = desc_elem.inner_text().strip()
    if not description:
        desc_elem = page.query_selector('[itemprop=\'description\']')
        if desc_elem:
            description = desc_elem.inner_text().strip()
    if not description:
        meta_desc = page.query_selector('meta[name=\'description\']')
        if meta_desc:
            description = (meta_desc.get_attribute('content') or '').strip()
    if not description:
        og_desc = page.query_selector('meta[property=\'og:description\']')
        if og_desc:
            description = (og_desc.get_attribute('content') or '').strip()

    return {'repo_name': trim(repo_name), 'star_count': trim(star_count), 'description': trim(description)}


def test_google_search(page):
    source_note = ''
    titles = []
    seen = set()

    # Try Google first
    page.goto('https://www.google.com/search?q=become+manus+oss', timeout=30000)
    page.wait_for_load_state('domcontentloaded')
    page.wait_for_timeout(3000)
    if '/sorry/' in page.url or 'captcha' in page.url.lower():
        source_note = 'google_blocked_by_captcha'
    else:
        all_links = page.query_selector_all("a[href*='/url?q=']")
        for link in all_links:
            h3 = link.query_selector('h3')
            if h3:
                t = (h3.inner_text() or '').strip()
            else:
                t = (link.inner_text() or '').strip()
            low = t.lower()
            skip = any(w in low for w in ['google', 'privacy', 'terms', 'preferences', 'settings', 'advanced'])
            if t and len(t) > 15 and t not in seen and not skip:
                titles.append(t)
                seen.add(t)
            if len(titles) >= 5:
                break
        if len(titles) < 3:
            h3_texts = page.evaluate('() => Array.from(document.querySelectorAll("h3")).map(h => h.textContent.trim()).filter(t => t.length > 15).slice(0, 10)')
            for t in h3_texts:
                if t not in seen:
                    titles.append(t)
                    seen.add(t)
                if len(titles) >= 5:
                    break

    # Fallback: Brave Search (more headless-browser friendly)
    if len(titles) < 3:
        source_note = 'brave_search'
        page.goto('https://search.brave.com/search?q=become+manus+oss', timeout=30000)
        page.wait_for_load_state('domcontentloaded')
        page.wait_for_timeout(5000)
        # Extract titles via JS - grab headings and visible link texts
        brave_titles = page.evaluate('() => {
            const results = [];
            // Try h3 elements first
            document.querySelectorAll("h3").forEach(h => {
                const t = h.textContent.trim();
                if (t.length > 15 && t.length < 200) results.push(t);
            });
            // Try result links
            document.querySelectorAll("a[href]").forEach(a => {
                const t = a.textContent.trim();
                if (t.length > 15 && t.length < 200 && !t.startsWith("> ") && results.length < 10) {
                    results.push(t);
                }
            });
            return results;
        }')
        for t in brave_titles:
            if t not in seen and len(t) > 15 and len(t) < 200:
                titles.append(t)
                seen.add(t)
            if len(titles) >= 5:
                break

    result = {'titles': titles[:3], 'title_count': len(titles[:3])}
    if source_note:
        result['search_engine_note'] = source_note
    return result


def main():
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/tmp/browser-e2e-results.json')
    results = {'ok': True, 'tests': [], 'errors': []}

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            # Test 1: example.com
            try:
                data = test_example_com(page)
                results['tests'].append({
                    'name': 'example.com title and links',
                    'status': 'pass',
                    'passed': True,
                    'url': 'https://example.com',
                    'extracted': data,
                })
            except Exception as exc:
                results['tests'].append({
                    'name': 'example.com title and links',
                    'status': 'fail',
                    'passed': False,
                    'url': 'https://example.com',
                    'error': f'{type(exc).__name__}: {exc}',
                })
                results['ok'] = False

            # Test 2: github docling
            try:
                data = test_github_docling(page)
                passed = bool(data.get('repo_name') and data.get('description'))
                results['tests'].append({
                    'name': 'github docling repo extraction',
                    'status': 'pass' if passed else 'partial',
                    'passed': passed,
                    'url': 'https://github.com/docling-project/docling',
                    'extracted': data,
                })
                if not passed:
                    results['ok'] = False
            except Exception as exc:
                results['tests'].append({
                    'name': 'github docling repo extraction',
                    'status': 'fail',
                    'passed': False,
                    'url': 'https://github.com/docling-project/docling',
                    'error': f'{type(exc).__name__}: {exc}',
                })
                results['ok'] = False

            # Test 3: google search
            try:
                data = test_google_search(page)
                passed = data.get('title_count', 0) >= 3
                results['tests'].append({
                    'name': 'google search become manus oss',
                    'status': 'pass' if passed else 'partial',
                    'passed': passed,
                    'url': 'https://www.google.com/search?q=become+manus+oss',
                    'extracted': data,
                })
                if not passed:
                    results['ok'] = False
            except Exception as exc:
                results['tests'].append({
                    'name': 'google search become manus oss',
                    'status': 'fail',
                    'passed': False,
                    'url': 'https://www.google.com/search?q=become+manus+oss',
                    'error': f'{type(exc).__name__}: {exc}',
                })
                results['ok'] = False

            browser.close()

    except Exception as exc:
        results['ok'] = False
        results['errors'].append({'phase': 'playwright_setup', 'error': f'{type(exc).__name__}: {exc}'})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0 if results['ok'] else 1


if __name__ == '__main__':
    raise SystemExit(main())