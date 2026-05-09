# Contributing to rasputin-omnitool

Thanks for considering a contribution. This kernel is small, opinionated, and tightly scoped — please read this before opening a PR.

## What belongs here

- New OSS capability entries in the catalog (with license SPDX + GitHub URL).
- License-review schema improvements.
- New parameterized deliverable formats (CSV / MD / HTML / PDF / XLSX / PPTX).
- Library-smoke harness extensions for additional libraries.

## What doesn't belong here

- Agent logic, planners, LLM clients — those live in [rasputin-omnitool-skill](https://github.com/jcartu/rasputin-omnitool-skill).
- Heavy dependencies. Stdlib first; optional extras get their own `[project.optional-dependencies]` group.
- "Verified" claims for catalog entries — the catalog is a curation, not an integration test.

## Workflow

1. Open an issue first for non-trivial changes. Describe the goal and the surface area.
2. Branch from `main`: `feat/<short-name>` or `fix/<short-name>`.
3. Tests must pass: `pytest`. Add tests for new behavior.
4. Keep diffs small. One logical change per PR.
5. Match existing code style. No formatter is enforced; just be consistent with neighbors.
6. Commit messages: imperative mood, summary in 72 chars or less, body wrapped at 72.

## License-review changes

License entries are evidence-driven. Don't hand-edit `licenses_manual.py` to mark something as "permissive" without a GitHub-fetched SPDX or a documented manual review with a source link.

## Tests

```bash
pip install -e .[dev]
pytest
```

The library-smoke tests install Docling and Crawl4AI in disposable venvs. They're slow on first run but should be deterministic.

## Reporting issues

Use the issue templates. Minor papercuts are welcome — see existing `[MINOR]` labels for examples.

## Code of Conduct

Be civil. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
