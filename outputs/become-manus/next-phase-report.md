# Become Manus Next Phase Report — Sandbox / Deep Research Bakeoff

Generated: `2026-04-28T20:00:17Z`

## Outcome

Completed the next safe phase without scheduling cron jobs, installing packages, starting services, running containers, mutating host configuration, or using credentials.

This phase added a lightweight bakeoff harness for:

- Sandbox / agent-computer candidates: `agent-infra/sandbox`, `microsandbox`
- Deep-research candidates: `Crawl4AI`, `Docling`

The bakeoffs use GitHub API metadata plus package-index metadata (`npm view`, `python -m pip index versions` with safe fallback to `pip index versions` when the active Hermes Python has no pip). Local Python import and CLI checks are best-effort presence checks only; they do not install anything.

No sandbox or deep-research capability was marked complete. Both reports keep `capability_complete_count: 0` because no E2E/smoke proof was run for these candidates yet.

## Code and test changes

Updated or added:

- `become_manus/bakeoff.py` — new safe metadata/installability bakeoff module.
- `become_manus/__main__.py` — added CLI subcommands:
  - `sandbox-bakeoff`
  - `deep-research-bakeoff`
- `tests/test_become_manus_toolkit.py` — added schema/safety/parser coverage and CLI help assertions.
- `become_manus/deliverables.py` — added a stdlib PNG fallback so the existing deliverables test/CLI still pass when `matplotlib` is absent.

Also updated the local `become-manus` skill metadata to include the new commands/artifacts.

## Durable artifacts

New bakeoff artifacts:

- `/home/josh/workspace/outputs/become-manus/sandbox-bakeoff.json`
- `/home/josh/workspace/outputs/become-manus/sandbox-bakeoff.md`
- `/home/josh/workspace/outputs/become-manus/deep-research-bakeoff.json`
- `/home/josh/workspace/outputs/become-manus/deep-research-bakeoff.md`
- `/home/josh/workspace/outputs/become-manus/next-phase-report.md`

Regenerated/validated existing demo artifacts after the PNG fallback fix:

- `/home/josh/workspace/outputs/become-manus/demo/manifest.json`
- `/home/josh/workspace/outputs/become-manus/demo/capability_chart.png`
- `/home/josh/workspace/outputs/become-manus/demo/source_data.csv`
- `/home/josh/workspace/outputs/become-manus/demo/analysis.md`
- `/home/josh/workspace/outputs/become-manus/demo/executive_summary.html`
- `/home/josh/workspace/outputs/become-manus/demo/executive_summary.pdf`
- `/home/josh/workspace/outputs/become-manus/demo/analysis.xlsx`
- `/home/josh/workspace/outputs/become-manus/demo/presentation.pptx`

## Command log and results

### Discovery / safety checks

```bash
cd /home/josh/workspace
ps -eo pid,ppid,stat,etime,cmd | grep -E 'hermes|become_manus|pytest' | grep -v grep
```

Result: pass. Only long-lived Hermes gateway/webui processes were present; no duplicate `become_manus` or pytest writer was running.

```bash
cd /home/josh/workspace
git status --short && git branch --show-current && git diff --stat
```

Result: expected fail because `/home/josh/workspace` is not a git repository.

```bash
git -C /home/josh/.hermes/hermes-agent status --short
```

Result: pass. Existing unrelated dirty files were observed but not edited:

```text
M plugins/memory/hindsight/__init__.py
M tests/plugins/memory/test_hindsight_provider.py
```

### Package-index probes

Initial direct probes showed the active Hermes Python has no embedded pip:

```bash
cd /home/josh/workspace
python -m pip index versions crawl4ai
python -m pip index versions docling
python -m pip index versions microsandbox
```

Result: fail for all three with:

```text
/home/josh/.hermes/hermes-agent/venv/bin/python: No module named pip
```

Fallback package-index commands succeeded:

```bash
cd /home/josh/workspace
pip index versions crawl4ai
pip index versions docling
pip index versions microsandbox
npm view @agent-infra/sandbox version license repository.url --json
npm view microsandbox version license repository.url --json
```

Results:

- `crawl4ai`: latest `0.8.6`
- `docling`: latest `2.91.0`
- `microsandbox`: latest `0.4.0`
- `@agent-infra/sandbox`: version `1.0.15`, license `ISC`, repository `git+https://github.com/agent-infra/sandbox-sdk.git`
- `microsandbox` npm package also exists at `0.4.0`, license `Apache-2.0`

The new bakeoff code records the failed `python -m pip ...` attempt and the successful fallback to `/usr/sbin/pip` where applicable.

### Tests

First test run exposed a pre-existing optional dependency fragility:

```bash
cd /home/josh/workspace
python -m pytest tests/test_become_manus_toolkit.py -q
```

Result: fail, `1 failed, 8 passed`; failure was `ModuleNotFoundError: No module named 'matplotlib'` in `become_manus/deliverables.py`.

Fix applied: stdlib PNG fallback in `become_manus/deliverables.py`.

Final test run:

```bash
cd /home/josh/workspace
python -m pytest tests/test_become_manus_toolkit.py -q
```

Result: pass.

```text
9 passed in 0.96s
```

Final post-report verification also passed:

```bash
cd /home/josh/workspace
python -m pytest tests/test_become_manus_toolkit.py -q
```

```text
9 passed in 0.98s
```

### New CLI commands

```bash
cd /home/josh/workspace
python -m become_manus sandbox-bakeoff --output-dir outputs/become-manus
```

Result: pass exit code `0`; report status `warn` because optional local import/CLI checks are absent for `microsandbox`.

Summary:

- `candidate_count`: `2`
- `metadata_ready_count`: `2`
- `capability_complete_count`: `0`
- `agent-infra/sandbox`: `pass`
  - GitHub API: pass, `Apache-2.0`, non-archived, `4465` stars at check time.
  - npm metadata: pass, `@agent-infra/sandbox` version `1.0.15`.
- `microsandbox`: `warn`
  - GitHub API: pass, repo resolved to `superradcompany/microsandbox`, `Apache-2.0`, non-archived, `5867` stars at check time.
  - PyPI metadata: pass, latest `0.4.0`.
  - Local import: warn, not installed.
  - Local CLI: warn, not installed.

```bash
cd /home/josh/workspace
python -m become_manus deep-research-bakeoff --output-dir outputs/become-manus
```

Result: pass exit code `0`; report status `warn` because optional local import/CLI checks are absent for Crawl4AI and Docling.

Summary:

- `candidate_count`: `2`
- `metadata_ready_count`: `2`
- `capability_complete_count`: `0`
- `Crawl4AI`: `warn`
  - GitHub API: pass, `Apache-2.0`, non-archived, `64716` stars at check time.
  - PyPI metadata: pass, latest `0.8.6`.
  - Local import/CLI: warn, not installed.
- `Docling`: `warn`
  - GitHub API: pass, `MIT`, non-archived, `58725` stars at check time.
  - PyPI metadata: pass, latest `2.91.0`.
  - Local import/CLI: warn, not installed.

```bash
cd /home/josh/workspace
python -m become_manus --help
```

Result: pass. Help now lists:

- `sandbox-bakeoff`
- `deep-research-bakeoff`

### Existing deliverables CLI recheck

```bash
cd /home/josh/workspace
python -m become_manus demo --output-dir outputs/become-manus/demo >/tmp/become-manus-demo.out && python - <<'PY'
import json
from pathlib import Path
payload=json.loads(Path('/tmp/become-manus-demo.out').read_text())
print(payload['validation']['status'])
print(len(payload['manifest']['artifacts']))
PY
```

Result: pass.

```text
pass
7
```

## Current blockers / cautions

1. The active Hermes Python (`/home/josh/.hermes/hermes-agent/venv/bin/python`) has no `pip`, so direct `python -m pip index versions ...` fails. The bakeoff handles this by falling back to `/usr/sbin/pip`, but future install smoke tests should use an explicit isolated interpreter/venv rather than the Hermes runtime.
2. `microsandbox`, `crawl4ai`, and `docling` are not installed in the current environment; local imports and CLIs are unavailable.
3. No sandbox runtime E2E was run. Starting agent sandboxes may involve containers/services, so the next proof should be isolated and non-destructive.
4. No Crawl4AI or Docling E2E was run. Their packages can be dependency-heavy and Crawl4AI may require browser/runtime setup; next proof should use an isolated venv plus a tiny fixture URL/document.
5. `agent-infra/sandbox` GitHub repo is `Apache-2.0`, but npm metadata for `@agent-infra/sandbox` reports `ISC` and points at `agent-infra/sandbox-sdk`. Verify SDK/runtime mapping before deeper integration.
6. `zerocore-ai/microsandbox` resolves via GitHub API to `superradcompany/microsandbox`; candidate naming may need normalization in a later cleanup.

## Recommended next safe phase

Do not mark any of these complete until an E2E/smoke artifact passes. Recommended next step is a contained smoke layer:

1. Create an isolated temporary venv under `outputs/become-manus/venvs/` or `/tmp` for deep-research checks.
2. Install only one candidate at a time with pinned versions from the bakeoff report.
3. Run a tiny Crawl4AI fixture crawl and Docling fixture document parse.
4. For sandbox candidates, prefer SDK import/version smoke first; only run runtime/container checks after adding explicit safeguards and output cleanup.
5. Write all proof artifacts under `outputs/become-manus/` and keep `capability_complete` false unless the smoke passes.
