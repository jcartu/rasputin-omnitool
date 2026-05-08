from __future__ import annotations

import json
import re
import socket
import subprocess
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _write_static_app(app_dir: Path) -> None:
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "index.html").write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Become Manus Static App</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <main>
    <h1>Become Manus Static App</h1>
    <p id="status">Generated, served, and verified by Hermes.</p>
    <button id="action">Run local interaction</button>
    <pre id="output" aria-live="polite"></pre>
  </main>
  <script src="app.js"></script>
</body>
</html>
""",
        encoding="utf-8",
    )
    (app_dir / "styles.css").write_text(
        """body{font-family:Inter,system-ui,sans-serif;margin:0;background:#0b1020;color:#edf2ff}main{max-width:760px;margin:8vh auto;padding:2rem;border:1px solid #334155;border-radius:20px;background:#111827}button{padding:.7rem 1rem;border-radius:10px;border:0;background:#7c3aed;color:white}pre{background:#020617;padding:1rem;border-radius:12px;overflow:auto} """,
        encoding="utf-8",
    )
    (app_dir / "app.js").write_text(
        """document.getElementById('action').addEventListener('click', () => {
  document.getElementById('output').textContent = JSON.stringify({ok:true, capability:'webapp_smoke'}, null, 2);
});
""",
        encoding="utf-8",
    )


def run_webapp_smoke(output_dir: str | Path = "outputs/become-manus/webapp-smoke") -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    app_dir = output_dir / "app"
    _write_static_app(app_dir)
    port = _free_port()
    server = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"],
        cwd=app_dir,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    http_status = 0
    body = ""
    error = ""
    try:
        for _ in range(30):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/index.html", timeout=2) as response:
                    http_status = int(response.status)
                    body = response.read().decode("utf-8")
                    error = ""
                    break
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                time.sleep(0.1)
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait(timeout=5)
    title_match = re.search(r"<title>(.*?)</title>", body, flags=re.IGNORECASE | re.DOTALL)
    title = title_match.group(1).strip() if title_match else ""
    status = "pass" if http_status == 200 and "Generated, served, and verified" in body else "fail"
    json_path = output_dir / "webapp-smoke.json"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "capability": "static_webapp_generation_and_serve_smoke",
        "scope": "local_static_app_no_external_deploy_no_credentials",
        "summary": {
            "http_status": http_status,
            "page_title": title,
            "served_url": f"http://127.0.0.1:{port}/index.html",
            "capability_complete": status == "pass",
            "error": error,
        },
        "artifacts": {"report_json": str(json_path), "app_dir": str(app_dir)},
    }
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
