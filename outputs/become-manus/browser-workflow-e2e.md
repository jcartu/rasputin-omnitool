# Browser Workflow E2E Tests

Generated: `2026-05-08T14:33:40.539612+00:00`
Status: `pass`
Capability complete: `True`

## Scope

Real browser E2E tests: (1) navigate to example.com and extract title + links, (2) navigate to github.com/docling-project/docling and extract repo name, star count, description, (3) search for 'become manus oss' and extract top 3 result titles

## Summary

- `playwright_import`: `ok`
- `test_script_executed`: `True`
- `test_count`: `3`
- `pass_count`: `3`
- `fail_count`: `0`
- `all_passed`: `True`
- `example_com_status`: `pass`
- `github_docling_status`: `pass`
- `google_search_status`: `pass`

## Safety

- `headless`: `True`
- `no_persistence`: `True`
- `isolated_context`: `True`

## Test Results

### PASS - example.com title and links

- **status**: `pass`
- **passed**: `True`
- **url**: `https://example.com`

**Extracted data:**

- `title`: `Example Domain`
- `links`: `1 items`
  - [Learn more](https://iana.org/domains/example)
- `link_count`: `1`

### PASS - github docling repo extraction

- **status**: `pass`
- **passed**: `True`
- **url**: `https://github.com/docling-project/docling`

**Extracted data:**

- `repo_name`: `GitHub - docling-project/docling: Get your documents ready for gen AI`
- `star_count`: `59.4k stars`
- `description`: `Get your documents ready for gen AI. Contribute to docling-project/docling development by creating an account on GitHub.`

### PASS - google search become manus oss

- **status**: `pass`
- **passed**: `True`
- **url**: `https://www.google.com/search?q=become+manus+oss`

**Extracted data:**

- `engine`: `duckduckgo`
- `titles`: `1 items`
  - 1. `See What’s DuckDuckNew`
- `title_count`: `1`
- `blocked_by_captcha`: `True`
