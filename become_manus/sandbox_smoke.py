from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path


def run_sandbox_smoke(output_dir: str | Path = "outputs/become-manus/sandbox-smoke") -> dict:
    """Run a non-destructive local process-isolation smoke proof.

    This does not claim container/sandbox-runtime parity. It proves the harness can
    execute code in a throwaway working directory with a constrained environment,
    capture transcript artifacts, and detect host-workspace mutation.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    workspace = Path.cwd().resolve()
    before = {p.name for p in workspace.iterdir()} if workspace.exists() else set()
    code = r'''
import json
import os
from pathlib import Path
payload = {
    "cwd": str(Path.cwd()),
    "env_allowlist": sorted(k for k in os.environ if k.startswith("BECOME_MANUS_")),
    "calculation": sum(range(10)),
}
Path("sandbox-output.json").write_text(json.dumps(payload, indent=2) + "\n")
print(json.dumps(payload, sort_keys=True))
'''
    with tempfile.TemporaryDirectory(prefix="become-manus-sandbox-") as tmp:
        tmp_path = Path(tmp)
        env = {"PATH": os.environ.get("PATH", ""), "BECOME_MANUS_SANDBOX": "1"}
        result = subprocess.run(
            [sys.executable, "-c", code],
            cwd=tmp_path,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        sandbox_output = tmp_path / "sandbox-output.json"
        parsed = json.loads(sandbox_output.read_text()) if sandbox_output.exists() else {}
        transcript = {
            "returncode": result.returncode,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "sandbox_output_exists": sandbox_output.exists(),
            "sandbox_output": parsed,
        }
    after = {p.name for p in workspace.iterdir()} if workspace.exists() else set()
    host_mutation_detected = before != after
    status = "pass" if result.returncode == 0 and transcript["sandbox_output_exists"] and not host_mutation_detected else "fail"
    json_path = output_dir / "sandbox-smoke.json"
    transcript_path = output_dir / "sandbox-transcript.json"
    report = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "capability": "local_process_sandbox_smoke",
        "scope": "non_destructive_no_container_no_service_no_install",
        "summary": {
            "subprocess_returncode": result.returncode,
            "host_mutation_detected": host_mutation_detected,
            "capability_complete": status == "pass",
            "note": "This is a local harness smoke proof, not yet agent-infra/microsandbox runtime parity.",
        },
        "artifacts": {"report_json": str(json_path), "transcript_json": str(transcript_path)},
    }
    transcript_path.write_text(json.dumps(transcript, indent=2) + "\n", encoding="utf-8")
    json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report
