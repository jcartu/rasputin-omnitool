# rasputin-omnitool

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
[![Tests](https://github.com/jcartu/rasputin-omnitool/actions/workflows/tests.yml/badge.svg)](https://github.com/jcartu/rasputin-omnitool/actions/workflows/tests.yml)

Curated catalog of OSS tools mapping to Manus AI capabilities, plus a license-review and library-import smoke harness.

This is a **kernel package**, not an agent. The agent layer that consumes this kernel lives in [rasputin-omnitool-skill](https://github.com/jcartu/rasputin-omnitool-skill) (an OpenClaw skill bundle).

> Formerly `become-manus`. Renamed to `rasputin-omnitool` at v0.3.0. Historical artifacts under `outputs/become-manus/` are pre-rename run records and are kept as-is for traceability.

## What this provides

- **Capability catalog** (`rasputin_omnitool.catalog`) — 28 capabilities mapped to OSS tools as of May 2026. Covers agent infrastructure, browser automation, coding agents, research, webapps, design, mobile, slides, documents, data analysis, workflows, mail, APIs, scheduling, analytics, plus voice (TTS/STT), image/video/music generation, memory, vector storage, reranking, LLM serving, web search, observability, and eval harnesses.
- **License review** (`rasputin_omnitool.licenses`, `licenses_manual`) — fetches GitHub license metadata; manually annotates dual-licensed projects.
- **Bakeoff** (`rasputin_omnitool.bakeoff`) — checks PyPI/npm metadata + import resolvability per candidate. Returns honest `capability_complete: False` because metadata is not integration.
- **Library smoke** (`rasputin_omnitool.library_smoke`) — installs Docling and Crawl4AI in a disposable venv and runs them on bundled fixture documents. This is a real library-import test, not a metadata fetch.
- **Deliverables** (`rasputin_omnitool.deliverables`) — stdlib-only generators for CSV / MD / HTML / PDF / XLSX / PPTX from a parameterized spec.

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
python -m rasputin_omnitool matrix              # print the catalog as JSON
python -m rasputin_omnitool license-review      # fetch and write GitHub license metadata
python -m rasputin_omnitool manual-license-review
python -m rasputin_omnitool bakeoff             # PyPI/npm/GitHub metadata + import checks
python -m rasputin_omnitool library-smoke       # disposable-venv Docling/Crawl4AI smokes
```

## Tests

```bash
pytest
```

The suite verifies catalog structure, license-review schemas, parameterized deliverable generation, and the disposable-venv library smokes.

## Companion: rasputin-omnitool-skill

[rasputin-omnitool-skill](https://github.com/jcartu/rasputin-omnitool-skill) wires this kernel into a planner / executor / reviewer agent loop with 18 tools. Includes real Langfuse observability, cost ceiling enforcement, Promptfoo evals, and an Open WebUI plugin for chat-driven goal invocation.

## License

MIT.
