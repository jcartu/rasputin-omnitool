# Become Manus Runtime E2E Report

Generated: `2026-05-08T15:05:00+00:00`
Status: `pass`
Output dir: `outputs/become-manus/runtime-e2e`

## Summary

- `capability_complete_count`: `3`
- `crawl4ai_status`: `pass`
- `docling_status`: `pass`
- `sandbox_status`: `pass`
- `report_count`: `3`
- `status_counts`: `{'blocker': 0, 'fail': 0, 'pass': 3, 'skip': 0, 'warn': 0}`

## E2E Reports

- ✅ **docling_fixture_parse**: status=`pass` capability_complete=`True`
- ✅ **crawl4ai_fixture_crawl**: status=`pass` capability_complete=`True`
- ✅ **sandbox_runtime_smoke**: status=`pass` capability_complete=`True`
  - Docker container `become-manus-sandbox` running with `--rm` flag
  - Ports mapped: 8080 (nginx/gateway), 18200 (Python server), 18888 (Jupyter)
  - Health check: `{"status":"healthy"}` via `/health` endpoint
  - Code execution API: `/v1/code/execute` on port 8091 returned `4` for `2+2`

## Sandbox Hosting E2E (NEW)

- ✅ **sandbox_hosting_e2e**: Full pipeline verified
  - Generated Linear-style landing page with 54 design system templates
  - Deployed to sandbox container via `docker cp`
  - Configured nginx reverse proxy at `/site/` path
  - Verified at `http://127.0.0.1:8080/site/`
  - All 6 checks passed:
    - Docker available (v29.4.1)
    - Sandbox container running
    - Site served (HTTP 200, correct title)
    - CSS styles present
    - JavaScript interactivity present
    - Responsive viewport meta present
    - Design tokens (dark BG, Inter font) verified

## Research & License Review (NEW)

- ✅ **bolt.diy research**: Full assessment for webapp_builder integration
  - Open-source Bolt.new clone, prompt-to-full-stack generation
  - 19+ LLM providers including local models (Ollama, LM Studio)
  - Supports React, Vue, Svelte, Next.js, Nuxt, Expo/React Native
  - Supabase integration for PostgreSQL + auth
  - Assessment: Moderately suitable — browser-first architecture requires Playwright automation
  - ⚠️ WebContainer licensing: Free for prototypes, commercial license for production
  - Report: `/home/josh/bolt-diy-research-report.md`

- ✅ **Manual license review**: 4 projects reviewed
  - **OpenHands**: MIT (core) + PolyForm Free Trial (enterprise/) — **conditional**
  - **Activepieces**: MIT (community) + proprietary (enterprise/) — **conditional**
  - **PostHog**: Custom PostHog License + proprietary (enterprise/) — **review_required**
  - **bolt.diy**: MIT (core) + WebContainer commercial license — **conditional**
  - Outputs: `outputs/become-manus/manual-license-review.md` + `.json`

## Advanced Web Generation (NEW)

- ✅ **54 design systems available**: Stripe, Linear, Vercel, Notion, Apple, Figma, etc.
- ✅ **Linear-style landing page**: Complete multi-section SPA with:
  - Dark-mode-first `#08090a` background
  - Inter Variable typography with weight 510 and negative letter-spacing
  - Hero section with gradient text
  - 4-card dashboard preview with live metrics
  - 6 capability feature cards with hover animations
  - Stats section, code block, CTA, full footer
  - Scroll animations via IntersectionObserver
  - Responsive breakpoints and reduced-motion support

## Test Suite Status

- **20/20 tests passing** (was 18/18, added 2 new tests)
- New tests: `test_sandbox_hosting_schema`, `test_manual_license_review_writes_outputs`
- New CLI entrypoints: `sandbox-hosting`, `manual-license-review`

## Remaining Blockers

- None — all primary capabilities verified

## Safety

- `browser_cache`: outputs/become-manus/runtime-e2e/playwright-browsers
- `credential_use`: none
- `cron_scheduling`: no new cron jobs scheduled
- `global_python_mutation`: none_intended
- `system_config_mutation`: none_intended
- `venv_dir`: outputs/become-manus/runtime-e2e/.venv
