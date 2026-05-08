import asyncio
import contextlib
import json
import sys
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

fixture_dir = Path(sys.argv[1])
markdown_path = Path(sys.argv[2])
payload_path = Path(sys.argv[3])

class QuietHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(fixture_dir), **kwargs)
    def log_message(self, format, *args):
        pass

def extract_markdown(result):
    markdown = getattr(result, "markdown", "")
    if hasattr(markdown, "raw_markdown"):
        return markdown.raw_markdown or ""
    if markdown is None:
        return ""
    return str(markdown)

async def crawl(url):
    from crawl4ai import AsyncWebCrawler
    try:
        from crawl4ai import BrowserConfig
    except Exception:
        BrowserConfig = None
    try:
        from crawl4ai import CrawlerRunConfig, CacheMode
    except Exception:
        CrawlerRunConfig = None
        CacheMode = None

    errors = []
    crawler_factories = []
    if BrowserConfig is not None:
        try:
            browser_config = BrowserConfig(headless=True, verbose=False)
        except TypeError:
            browser_config = BrowserConfig(headless=True)
        crawler_factories.extend([
            lambda: AsyncWebCrawler(config=browser_config),
            lambda: AsyncWebCrawler(browser_config=browser_config),
        ])
    crawler_factories.extend([
        lambda: AsyncWebCrawler(headless=True, verbose=False),
        lambda: AsyncWebCrawler(),
    ])
    run_configs = [None]
    if CrawlerRunConfig is not None:
        try:
            cache_mode = CacheMode.BYPASS if CacheMode is not None else None
            run_configs.insert(0, CrawlerRunConfig(cache_mode=cache_mode))
        except Exception:
            pass

    for make_crawler in crawler_factories:
        try:
            async with make_crawler() as crawler:
                for run_config in run_configs:
                    try:
                        if run_config is not None:
                            result = await crawler.arun(url=url, config=run_config)
                        else:
                            result = await crawler.arun(url=url)
                        markdown = extract_markdown(result)
                        success = bool(getattr(result, "success", True))
                        contains = {
                            "become_manus": "Become Manus" in markdown,
                            "crawl4ai": "Crawl4AI" in markdown,
                        }
                        return {
                            "ok": success and all(contains.values()) and len(markdown) > 20,
                            "success": success,
                            "url": url,
                            "markdown_chars": len(markdown),
                            "contains": contains,
                            "error_message": getattr(result, "error_message", None),
                            "markdown": markdown,
                            "attempt_errors": errors,
                        }
                    except Exception as exc:
                        errors.append({"phase": "arun", "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
        except Exception as exc:
            errors.append({"phase": "crawler_context", "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
    return {"ok": False, "url": url, "markdown_chars": 0, "contains": {}, "attempt_errors": errors}

server = ThreadingHTTPServer(("127.0.0.1", 0), QuietHandler)
thread = threading.Thread(target=server.serve_forever, daemon=True)
thread.start()
url = f"http://127.0.0.1:{server.server_address[1]}/index.html"
try:
    payload = asyncio.run(crawl(url))
except Exception as exc:
    payload = {"ok": False, "url": url, "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]}
finally:
    with contextlib.suppress(Exception):
        server.shutdown()
    with contextlib.suppress(Exception):
        server.server_close()
if payload.get("markdown"):
    markdown_path.write_text(payload["markdown"], encoding="utf-8")
    payload.pop("markdown", None)
payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, sort_keys=True))
raise SystemExit(0 if payload.get("ok") else 2)
