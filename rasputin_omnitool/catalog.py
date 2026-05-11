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
        Candidate("OpenSandbox", "https://github.com/alibaba/OpenSandbox", "Apache-2.0", "Docker/Kubernetes sandbox API"),
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
        Candidate("LangGraph", "https://github.com/langchain-ai/langgraph", "MIT", "stateful agent graph orchestration", True),
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
        Candidate("Onlook", "https://github.com/onlook-dev/onlook", "Apache-2.0", "visual editor for React apps"),
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
        Candidate("n8n", "https://github.com/n8n-io/n8n", "Sustainable Use License (source-available)", "large connector library"),
    ],
    "mail_agent": [
        Candidate("Himalaya", "https://github.com/pimalaya/himalaya", "MIT", "terminal IMAP/SMTP client", True),
    ],
    "api_platform": [
        Candidate("FastAPI", "https://github.com/fastapi/fastapi", "MIT", "REST API service", True),
    ],
    "scheduled_tasks": [
        Candidate("Apache Airflow", "https://github.com/apache/airflow", "Apache-2.0", "batch/data workflows", True),
        Candidate("Kestra", "https://github.com/kestra-io/kestra", "Apache-2.0 core", "event workflows"),
    ],
    "analytics": [
        Candidate("PostHog", "https://github.com/PostHog/posthog", "MIT (server) + commercial (cloud features)", "product analytics/replay/flags", True),
        Candidate("Umami", "https://github.com/umami-software/umami", "MIT", "web analytics"),
        Candidate("Plausible", "https://github.com/plausible/analytics", "AGPL-3.0", "privacy analytics"),
    ],
    # v0.4 additions — 12 new capability rows
    "tts": [
        Candidate("Voxtral TTS", "https://github.com/mistralai/voxtral", "Apache-2.0", "Mistral TTS, beat ElevenLabs Flash v2.5 in blind tests", True),
        Candidate("Kokoro 82M", "https://github.com/hexgrad/kokoro", "Apache-2.0", "ultra-light TTS, runs on CPU", True),
        Candidate("Chatterbox", "https://github.com/resemble-ai/chatterbox", "MIT", "voice cloning TTS"),
        Candidate("Piper", "https://github.com/rhasspy/piper", "MIT", "fast neural TTS for local use"),
    ],
    "stt": [
        Candidate("Canary-Qwen 2.5B", "https://huggingface.co/nvidia/canary-qwen-2.5b", "CC-BY-4.0", "NVIDIA SALM, top of HF Open ASR Leaderboard", True),
        Candidate("Whisper-large-v3-turbo", "https://huggingface.co/openai/whisper-large-v3-turbo", "MIT", "fast multilingual STT", True),
        Candidate("Parakeet TDT", "https://huggingface.co/nvidia/parakeet-tdt-1.1b", "CC-BY-4.0", "low-latency streaming"),
        Candidate("Moonshine v2", "https://github.com/usefulsensors/moonshine", "MIT", "27 MB edge STT"),
    ],
    "image_generation": [
        Candidate("FLUX.2 [dev]", "https://github.com/black-forest-labs/flux", "FLUX.1 [dev] Non-Commercial License", "32B frontier-quality image gen", True),
        Candidate("Z-Image-Turbo", "https://github.com/QwenLM/Z-Image", "Apache-2.0", "fast bilingual image gen", True),
        Candidate("Stable Diffusion 3.5 Large", "https://github.com/Stability-AI/sd3.5", "Stability Community License", "mature SD ecosystem"),
        Candidate("HiDream-I1", "https://github.com/HiDream-ai/HiDream-I1", "MIT", "open-weight image gen"),
    ],
    "video_generation": [
        Candidate("Wan 2.1", "https://github.com/Wan-Video/Wan2.1", "Apache-2.0", "fits 96GB single card without aggressive quant", True),
        Candidate("HunyuanVideo", "https://github.com/Tencent/HunyuanVideo", "Tencent Community License", "needs 60GB+, slower"),
        Candidate("Open-Sora 2.0", "https://github.com/hpcaitech/Open-Sora", "Apache-2.0", "more permissive but lower quality"),
        Candidate("CogVideoX", "https://github.com/THUDM/CogVideo", "Apache-2.0", "alternative T2V"),
    ],
    "music_generation": [
        Candidate("MusicGen-Melody", "https://github.com/facebookresearch/audiocraft", "MIT", "Meta T2M, stable", True),
        Candidate("YuE", "https://github.com/multimodal-art-projection/YuE", "Apache-2.0", "full-song with vocals, less stable"),
    ],
    "memory": [
        Candidate("RASPUTIN", "https://github.com/jcartu/rasputin-memory", "MIT", "Joshua's MCP-served hybrid retrieval, 72.4% LoCoMo", True),
        Candidate("Mem0", "https://github.com/mem0ai/mem0", "Apache-2.0", "91.6% LoCoMo, popular"),
        Candidate("Hindsight", "https://github.com/leodriesch/hindsight", "MIT", "89.61% LoCoMo"),
    ],
    "vector_db": [
        Candidate("Qdrant", "https://github.com/qdrant/qdrant", "Apache-2.0", "Joshua's choice, RASPUTIN backend", True),
        Candidate("Weaviate", "https://github.com/weaviate/weaviate", "BSD-3-Clause", "graph + vector"),
        Candidate("Chroma", "https://github.com/chroma-core/chroma", "Apache-2.0", "embedded, easy onboarding"),
        Candidate("LanceDB", "https://github.com/lancedb/lancedb", "Apache-2.0", "columnar, multimodal"),
    ],
    "reranker": [
        Candidate("Qwen3-Reranker-0.6B", "https://huggingface.co/Qwen/Qwen3-Reranker-0.6B", "Apache-2.0", "fast cross-encoder", True),
        Candidate("bge-reranker-v2-m3", "https://huggingface.co/BAAI/bge-reranker-v2-m3", "Apache-2.0", "multilingual reranker"),
    ],
    "llm_serving": [
        Candidate("vLLM", "https://github.com/vllm-project/vllm", "Apache-2.0", "production-grade LLM serving", True),
        Candidate("SGLang", "https://github.com/sgl-project/sglang", "Apache-2.0", "structured generation"),
        Candidate("Ollama", "https://github.com/ollama/ollama", "MIT", "edge / dev convenience"),
        Candidate("TGI", "https://github.com/huggingface/text-generation-inference", "Apache-2.0", "HF reference server"),
    ],
    "web_search": [
        Candidate("SearXNG", "https://github.com/searxng/searxng", "AGPL-3.0", "federated meta-search", True),
        Candidate("Meilisearch", "https://github.com/meilisearch/meilisearch", "MIT", "typed full-text"),
        Candidate("Typesense", "https://github.com/typesense/typesense", "GPL-3.0", "fast typed search"),
    ],
    "observability": [
        Candidate("Langfuse", "https://github.com/langfuse/langfuse", "MIT (core)", "LLM-native tracing", True),
        Candidate("Arize Phoenix", "https://github.com/Arize-ai/phoenix", "Elastic-2.0", "stronger eval rigor"),
        Candidate("Helicone", "https://github.com/Helicone/helicone", "Apache-2.0", "API gateway + tracing"),
        Candidate("OpenLLMetry", "https://github.com/traceloop/openllmetry", "Apache-2.0", "OTel-based"),
    ],
    "eval_harness": [
        Candidate("Promptfoo", "https://github.com/promptfoo/promptfoo", "MIT", "YAML-driven LLM evals", True),
        Candidate("DeepEval", "https://github.com/confident-ai/deepeval", "Apache-2.0", "pytest-style evals"),
        Candidate("TruLens", "https://github.com/truera/trulens", "MIT", "feedback functions"),
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
