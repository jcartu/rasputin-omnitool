from __future__ import annotations

import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run_browser_e2e(output_dir: str | Path = "outputs/become-manus/browser-e2e", *, url: str = "https://example.com", run_external: bool = True) -> dict:
    """Run a minimal browser-operator E2E and write durable proof.

    Uses Playwright CLI through npx so this can run independently of a live Hermes
    conversation while still validating the browser stack needed by Playwright MCP.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    screenshot = output_dir / "example.png"
    report_path = output_dir / "browser-e2e.json"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "url": url,
        "status": "skip",
        "checks": [],
        "artifacts": {"screenshot": str(screenshot)},
    }
    npx = shutil.which("npx")
    if not npx:
        report["status"] = "fail"
        report["checks"].append({"name": "npx", "status": "fail", "details": "npx not found"})
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        return report
    report["checks"].append({"name": "npx", "status": "pass", "details": npx})
    if not run_external:
        report["status"] = "skip"
        report_path.write_text(json.dumps(report, indent=2) + "\n")
        return report
    result = subprocess.run(
        [npx, "-y", "playwright@latest", "screenshot", "--browser=chromium", url, str(screenshot)],
        text=True,
        capture_output=True,
        timeout=120,
    )
    ok = result.returncode == 0 and screenshot.exists() and screenshot.stat().st_size > 0
    report["checks"].append(
        {
            "name": "playwright_screenshot",
            "status": "pass" if ok else "fail",
            "details": {
                "returncode": result.returncode,
                "stdout": result.stdout.strip(),
                "stderr": result.stderr.strip(),
                "screenshot_exists": screenshot.exists(),
                "screenshot_size": screenshot.stat().st_size if screenshot.exists() else 0,
            },
        }
    )
    report["status"] = "pass" if ok else "fail"
    report_path.write_text(json.dumps(report, indent=2) + "\n")
    return report
