# become_manus_kernel

Reusable Python kernel for the Become Manus sprint: OSS capability catalog, license review, bakeoff reports, deliverable generation, and isolated Docling/Crawl4AI library smoke checks.

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

python -m become_manus_kernel matrix
python -m become_manus_kernel license-review
python -m become_manus_kernel manual-license-review
python -m become_manus_kernel bakeoff --no-external
python -m become_manus_kernel library-smoke --no-external
```

The installed console script is also available as:

```bash
become-manus-kernel --help
```

## CLI subcommands

- `matrix` — print the OSS capability catalog
- `license-review` — fetch GitHub license metadata
- `manual-license-review` — write dual-license review markdown/JSON
- `bakeoff` — run sandbox and deep-research candidate bakeoffs
- `library-smoke` — run isolated Docling and Crawl4AI fixture smokes

## Tests

```bash
pytest
pyflakes become_manus_kernel/
```

## License

MIT
