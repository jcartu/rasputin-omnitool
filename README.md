# Become Manus

OSS replacement guide & integration harness for Manus-class agent capabilities.

## What this provides

- A curated catalog of OSS tools mapping to Manus AI capabilities
- License review for cataloged tools
- A bakeoff harness checking GitHub/PyPI/npm metadata per candidate
- Library-import smoke tests for Docling and Crawl4AI
- Parameterized deliverable generator (CSV/MD/PDF/XLSX/PPTX)
- Browser E2E via Playwright
- Sandbox HTTP probe for agent-infra/sandbox
- Runtime E2E tests for core capabilities
- Webapp generation and serving smoke test
- Sandbox hosting verification

## What this does NOT provide

- Verified production-ready implementations of all capabilities
- Guaranteed compatibility across all tool combinations
- Complete feature parity with Manus
- Automated deployment or integration setup

## Quick start

```bash
git clone https://github.com/jcartu/become-manus.git
cd become-manus
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m become_manus matrix
python -m become_manus license-review
python -m become_manus runtime-e2e
```

## Tests

```bash
pytest
```

## License

MIT
