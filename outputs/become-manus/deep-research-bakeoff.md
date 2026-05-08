# Become Manus Deep Research Bakeoff

Generated: `2026-04-28T19:58:40.182559+00:00`
Status: `warn`
Candidates: `2`

## Safety scope

This bakeoff is metadata/installability readiness only. It does **not** install packages, run containers, start services, mutate host configuration, or use credentials.
No capability is marked complete here; `capability_complete` stays `false` until a later E2E/smoke proof writes a passing artifact.

## Summary table

| Candidate | Status | Package manager | Package | Latest/version | GitHub stars | Local import | Local CLI | Capability claim |
|---|---:|---|---|---|---:|---:|---:|---|
| Crawl4AI | warn | pypi | crawl4ai | 0.8.6 | 64716 | no | no | not_complete_metadata_only_no_e2e_smoke_run |
| Docling | warn | pypi | docling | 2.91.0 | 58725 | no | no | not_complete_metadata_only_no_e2e_smoke_run |

## Candidate notes and blockers

### Crawl4AI

- Repo: `unclecode/crawl4ai`
- Role: LLM-friendly web crawler/extractor
- Host mutation risk for future E2E: install may download browser/runtime assets; this bakeoff avoids installs and browser setup
- Next E2E needed: `deferred_until_crawl_smoke_with_fixture_url`
- Notes: Import/CLI checks are best-effort against the current environment only.
- Checks:
  - `github_repo_metadata` unclecode/crawl4ai: `pass`
  - `pypi_index` crawl4ai: `pass` latest=0.8.6
  - `python_import_spec` crawl4ai: `warn`
  - `cli_presence` crawl4ai-setup: `warn`
  - `cli_presence` crawl4ai-doctor: `warn`

### Docling

- Repo: `docling-project/docling`
- Role: PDF/Office/document parsing and conversion
- Host mutation risk for future E2E: install can be dependency-heavy; this bakeoff avoids installing or mutating global Python state
- Next E2E needed: `deferred_until_fixture_document_parse_smoke`
- Notes: PyPI metadata and local import/CLI presence are checked without installation.
- Checks:
  - `github_repo_metadata` docling-project/docling: `pass`
  - `pypi_index` docling: `pass` latest=2.91.0
  - `python_import_spec` docling: `warn`
  - `cli_presence` docling: `warn`
