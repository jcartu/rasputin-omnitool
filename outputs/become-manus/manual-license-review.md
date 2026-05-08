# Become Manus — Manual License Review

Generated: 2026-05-08 14:59 UTC

Manual review for projects with dual-licensing, source-available, or non-standard licenses.

## Summary

- **Approved**: 0
- **Conditional** (approved with caveats): 3
- **Review Required**: 1

---

## OpenHands

- **Repo**: [All-Hands-AI/OpenHands](https://github.com/All-Hands-AI/OpenHands)
- **Capability**: coding_agents
- **Core License**: MIT License (dual-license)
- **Commercial Use**: Allowed for core (MIT)
- **Enterprise License**: PolyForm Free Trial 1.0.0
- **Enterprise Restricted**: Yes
- **SPDX**: MIT (core); PolyForm-Free-Trial-1.0.0 (enterprise/)
- **Recommendation**: conditional
- **Recent Changes**: Enterprise license updated Apr 14 2026 (commit 4cdf88d). Main LICENSE clarified dual-license structure Sep 2 2025.

### Key Obligations
- Include MIT copyright notice in core usage
- Enterprise/ directory uses PolyForm Free Trial 1.0.0 — 30-day trial only, requires commercial license beyond
- Do not distribute enterprise features without license

---

## Activepieces

- **Repo**: [activepieces/activepieces](https://github.com/activepieces/activepieces)
- **Capability**: workflow_integrations
- **Core License**: MIT License (dual-license)
- **Commercial Use**: Allowed for community edition (MIT)
- **Enterprise License**: Activepieces Enterprise License (proprietary)
- **Enterprise Restricted**: Yes
- **SPDX**: MIT (community); LicenseRef-Activepieces-Enterprise (ee/)
- **Recommendation**: conditional
- **Recent Changes**: LICENSE last updated Feb 15 2024. No license type changes since inception — always MIT + commercial dual license.

### Key Obligations
- Include MIT copyright notice
- Enterprise features (packages/ee/, packages/server/api/src/app/ee) require commercial license
- Do not redistribute enterprise features

---

## PostHog

- **Repo**: [PostHog/posthog](https://github.com/PostHog/posthog)
- **Capability**: analytics
- **Core License**: PostHog License (custom) (source-available)
- **Commercial Use**: Allowed for self-hosted; competing SaaS restricted
- **Enterprise License**: PostHog Enterprise License (proprietary)
- **Enterprise Restricted**: Yes
- **SPDX**: LicenseRef-PostHog (main); LicenseRef-PostHog-Enterprise (ee/)
- **Recommendation**: review_required
- **Recent Changes**: Custom license is a departure from standard OSI licenses. Historical shifts between license models observed.

### Key Obligations
- Custom license — not OSI-approved open source
- Third-party components retain their original licenses
- Enterprise features (ee/) use separate PostHog Enterprise License
- Restrictions on offering competing hosted services

---

## bolt.diy

- **Repo**: [stackblitz-labs/bolt.diy](https://github.com/stackblitz-labs/bolt.diy)
- **Capability**: webapp_builder
- **Core License**: MIT License (permissive)
- **Commercial Use**: Allowed (MIT), but WebContainer API requires commercial license for production for-profit use
- **SPDX**: MIT (core); WebContainer API license separate
- **Recommendation**: conditional
- **Recent Changes**: Originally by Cole Medin, now community-driven. Active development with many contributors.

### Key Obligations
- Include MIT copyright notice
- WebContainers (StackBlitz tech) — free for prototypes/POCs, commercial license for production
- No additional copyleft or network-use obligations in core codebase

---
