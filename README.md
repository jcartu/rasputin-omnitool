# become-manus-kernel

Curated catalog of OSS tools mapping to Manus AI capabilities, plus a license-review and library-import smoke harness.

This is a **kernel package**, not an agent. The agent layer that consumes this kernel lives in [become-manus-skill](../become-manus-skill/) (an OpenClaw skill bundle).

## What this provides

- **Capability catalog** (`become_manus_kernel.catalog`) — 28 capabilities mapped to OSS tools as of May 2026. Voice, image, video, music, memory, observability, all the usual suspects.
- **License review** (`become_manus_kernel.licenses`, `licenses_manual`) — fetches GitHub license metadata; manually annotates dual-licensed projects.
- **Bakeoff** (`become_manus_kernel.bakeoff`) — checks PyPI/npm metadata + import resolvability per candidate. Returns honest `capability_complete: False` because metadata is not integration.
- **Library smoke** (`become_manus_kernel.library_smoke`) — installs Docling and Crawl4AI in a disposable venv and runs them on bundled fixture documents. This is a real library-import test, not a metadata fetch.
- **Deliverables** (`become_manus_kernel.deliverables`) — stdlib-only generators for CSV / MD / HTML / PDF / XLSX / PPTX from a parameterized spec.

## What this does NOT provide

- An autonomous agent (no planner, no executor, no LLM client). That's the skill's job.
- "Verified" claims for any of the 28 capabilities — the catalog is a curation, not a guarantee.
- Production integrations of the cataloged tools — the bakeoff is metadata-only by design.

## Install

```bash
pip install -e .
```

## CLI

```bash
python -m become_manus_kernel matrix              # print the catalog as JSON
python -m become_manus_kernel license-review      # fetch and write GitHub license metadata
python -m become_manus_kernel manual-license-review
python -m become_manus_kernel bakeoff             # PyPI/npm/GitHub metadata + import checks
python -m become_manus_kernel library-smoke       # disposable-venv Docling/Crawl4AI smokes
```

## Tests

```bash
pytest
```

The suite verifies catalog structure, license-review schemas, parameterized deliverable generation, and the disposable-venv library smokes.

## Companion: become-manus-skill

[become-manus-skill](../become-manus-skill/) wires this kernel into a planner / executor / reviewer agent loop with 12 tools (6 core + 6 multimodal extensions). Run end-to-end agent goals there.

## License

MIT.
