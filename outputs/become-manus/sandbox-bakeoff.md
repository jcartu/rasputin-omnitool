# Become Manus Sandbox Bakeoff

Generated: `2026-04-28T19:58:36.827418+00:00`
Status: `warn`
Candidates: `2`

## Safety scope

This bakeoff is metadata/installability readiness only. It does **not** install packages, run containers, start services, mutate host configuration, or use credentials.
No capability is marked complete here; `capability_complete` stays `false` until a later E2E/smoke proof writes a passing artifact.

## Summary table

| Candidate | Status | Package manager | Package | Latest/version | GitHub stars | Local import | Local CLI | Capability claim |
|---|---:|---|---|---|---:|---:|---:|---|
| agent-infra/sandbox | pass | npm | @agent-infra/sandbox | 1.0.15 | 4465 | no | no | not_complete_metadata_only_no_e2e_smoke_run |
| microsandbox | warn | pypi | microsandbox | 0.4.0 | 5867 | no | no | not_complete_metadata_only_no_e2e_smoke_run |

## Candidate notes and blockers

### agent-infra/sandbox

- Repo: `agent-infra/sandbox`
- Role: all-in-one Docker-style agent computer/sandbox runtime
- Host mutation risk for future E2E: full runtime likely requires Docker/containers; this bakeoff does not start containers or mutate the host
- Next E2E needed: `deferred_until_isolated_container_smoke`
- Notes: Evaluated with GitHub API and npm package metadata only.
- Checks:
  - `github_repo_metadata` agent-infra/sandbox: `pass`
  - `npm_view` @agent-infra/sandbox: `pass` version=1.0.15

### microsandbox

- Repo: `zerocore-ai/microsandbox`
- Role: local-first programmable code sandboxes
- Host mutation risk for future E2E: full runtime may start sandbox services/containers; this bakeoff only checks metadata/import/CLI availability
- Next E2E needed: `deferred_until_isolated_non_destructive_smoke`
- Notes: PyPI index/import/CLI checks are lightweight and do not install the package.
- Checks:
  - `github_repo_metadata` superradcompany/microsandbox: `pass`
  - `pypi_index` microsandbox: `pass` latest=0.4.0
  - `python_import_spec` microsandbox: `warn`
  - `cli_presence` microsandbox: `warn`
