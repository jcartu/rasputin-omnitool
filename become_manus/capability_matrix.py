from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass(frozen=True)
class Candidate:
    name: str
    url: str
    license: str
    role: str
    preferred: bool = False


CAPABILITIES: Dict[str, List[Candidate]] = {
    "agent_computer": [
        Candidate("agent-infra/sandbox", "https://github.com/agent-infra/sandbox", "Apache-2.0", "all-in-one Docker agent computer", True),
        Candidate("microsandbox", "https://github.com/zerocore-ai/microsandbox", "Apache-2.0", "local-first programmable sandboxes", True),
        Candidate("Daytona", "https://github.com/daytonaio/daytona", "AGPL-3.0", "elastic AI/dev sandboxes"),
        Candidate("OpenSandbox", "https://github.com/alibaba/OpenSandbox", "verify", "Docker/Kubernetes sandbox API"),
    ],
    "browser_operator": [
        Candidate("Playwright MCP", "https://github.com/microsoft/playwright-mcp", "Apache-2.0", "MCP browser automation", True),
        Candidate("browser-use", "https://github.com/browser-use/browser-use", "MIT", "agentic browser control", True),
        Candidate("Stagehand", "https://github.com/browserbase/stagehand", "MIT", "AI-assisted Playwright abstraction"),
        Candidate("Skyvern", "https://github.com/Skyvern-AI/skyvern", "AGPL-3.0", "browser workflow automation"),
    ],
    "coding_agents": [
        Candidate("OpenHands", "https://github.com/All-Hands-AI/OpenHands", "MIT", "autonomous coding agent/runtime", True),
        Candidate("aider", "https://github.com/Aider-AI/aider", "Apache-2.0", "CLI repo-editing pair programmer", True),
        Candidate("SWE-agent", "https://github.com/SWE-agent/SWE-agent", "MIT", "SWE-bench style issue fixing"),
    ],
    "wide_research": [
        Candidate("Hermes delegate_task", "local", "built-in", "parallel subagents with isolated context", True),
        Candidate("LangGraph", "https://github.com/langchain-ai/langgraph", "MIT", "stateful agent graph orchestration"),
        Candidate("AutoGen", "https://github.com/microsoft/autogen", "MIT", "multi-agent orchestration"),
    ],
    "deep_research": [
        Candidate("Crawl4AI", "https://github.com/unclecode/crawl4ai", "Apache-2.0", "LLM-friendly crawler", True),
        Candidate("Docling", "https://github.com/docling-project/docling", "MIT", "PDF/Office/document parsing", True),
        Candidate("ScrapeGraphAI", "https://github.com/ScrapeGraphAI/Scrapegraph-ai", "MIT", "schema-driven LLM scraping"),
        Candidate("Firecrawl", "https://github.com/firecrawl/firecrawl", "AGPL-3.0", "crawl/search/extract API"),
    ],
    "webapp_builder": [
        Candidate("bolt.diy", "https://github.com/stackblitz-labs/bolt.diy", "MIT", "prompt-to-full-stack app generator", True),
        Candidate("Puck", "https://github.com/measuredco/puck", "MIT", "React visual page editor", True),
        Candidate("GrapesJS", "https://github.com/GrapesJS/grapesjs", "BSD-3-Clause", "WYSIWYG page builder"),
        Candidate("Supabase", "https://github.com/supabase/supabase", "Apache-2.0 components", "generated app backend", True),
        Candidate("PocketBase", "https://github.com/pocketbase/pocketbase", "MIT", "small app backend"),
        Candidate("Coolify", "https://github.com/coollabsio/coolify", "Apache-2.0", "self-host PaaS", True),
    ],
    "design_view": [
        Candidate("Penpot", "https://github.com/penpot/penpot", "MPL-2.0", "OSS design platform", True),
        Candidate("Onlook", "https://github.com/onlook-dev/onlook", "verify", "visual editor for React apps"),
        Candidate("Mitosis", "https://github.com/BuilderIO/mitosis", "MIT", "framework-neutral components"),
    ],
    "mobile_publishing": [
        Candidate("Expo", "https://github.com/expo/expo", "MIT", "React Native app platform", True),
        Candidate("Capacitor", "https://github.com/ionic-team/capacitor", "MIT", "web-to-native packaging", True),
        Candidate("fastlane", "https://github.com/fastlane/fastlane", "MIT", "store upload automation", True),
    ],
    "slides": [
        Candidate("Marp", "https://github.com/marp-team/marp", "MIT", "Markdown slides", True),
        Candidate("PptxGenJS", "https://github.com/gitbrent/PptxGenJS", "MIT", "programmatic PPTX", True),
        Candidate("reveal.js", "https://github.com/hakimel/reveal.js", "MIT", "web slides"),
    ],
    "documents": [
        Candidate("Pandoc", "https://github.com/jgm/pandoc", "GPL-2.0+", "universal document converter"),
        Candidate("Gotenberg", "https://github.com/gotenberg/gotenberg", "MIT", "document to PDF API", True),
        Candidate("WeasyPrint", "https://github.com/Kozea/WeasyPrint", "BSD-3-Clause", "HTML/CSS to PDF", True),
    ],
    "data_analysis": [
        Candidate("DuckDB", "https://github.com/duckdb/duckdb", "MIT", "embedded analytics DB", True),
        Candidate("JupyterLab", "https://github.com/jupyterlab/jupyterlab", "BSD-3-Clause", "notebooks", True),
        Candidate("Evidence", "https://github.com/evidence-dev/evidence", "MIT", "SQL+Markdown BI reports", True),
        Candidate("Apache Superset", "https://github.com/apache/superset", "Apache-2.0", "BI dashboards"),
    ],
    "workflow_integrations": [
        Candidate("Activepieces", "https://github.com/activepieces/activepieces", "MIT CE", "Zapier-like workflows", True),
        Candidate("MCP servers", "https://github.com/modelcontextprotocol/servers", "MIT/Apache-2.0", "standard tool connectors", True),
        Candidate("Composio", "https://github.com/ComposioHQ/composio", "MIT SDK", "OAuth-heavy SaaS tools", True),
        Candidate("n8n", "https://github.com/n8n-io/n8n", "source-available", "large connector library"),
    ],
    "mail_agent": [
        Candidate("Hermes gateway email", "local", "built-in", "email platform adapter", True),
        Candidate("Himalaya", "https://github.com/pimalaya/himalaya", "MIT", "terminal IMAP/SMTP client"),
    ],
    "api_platform": [
        Candidate("Hermes gateway API server", "local", "built-in", "task API/webhook base", True),
        Candidate("FastAPI", "https://github.com/fastapi/fastapi", "MIT", "REST API service"),
    ],
    "scheduled_tasks": [
        Candidate("Hermes cron", "local", "built-in", "scheduled autonomous jobs", True),
        Candidate("Apache Airflow", "https://github.com/apache/airflow", "Apache-2.0", "batch/data workflows"),
        Candidate("Kestra", "https://github.com/kestra-io/kestra", "Apache-2.0 core", "event workflows"),
    ],
    "analytics": [
        Candidate("PostHog", "https://github.com/PostHog/posthog", "verify", "product analytics/replay/flags", True),
        Candidate("Umami", "https://github.com/umami-software/umami", "MIT", "web analytics"),
        Candidate("Plausible", "https://github.com/plausible/analytics", "AGPL-3.0", "privacy analytics"),
    ],
}


def all_candidates() -> list[dict]:
    rows: list[dict] = []
    for capability, candidates in CAPABILITIES.items():
        for candidate in candidates:
            row = asdict(candidate)
            row["capability"] = capability
            rows.append(row)
    return rows


def candidate_summary() -> dict:
    rows = all_candidates()
    preferred = sorted({row["name"] for row in rows if row["preferred"]})
    return {
        "capability_count": len(CAPABILITIES),
        "candidate_count": len(rows),
        "preferred_candidates": preferred,
        "license_review_required": sorted({row["name"] for row in rows if "verify" in row["license"].lower() or "agpl" in row["license"].lower() or "source" in row["license"].lower()}),
    }
