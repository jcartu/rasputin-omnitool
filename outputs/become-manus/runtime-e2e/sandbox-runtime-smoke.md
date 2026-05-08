# Sandbox Runtime Smoke Report

Generated: `2026-05-08T14:20:58.178380+00:00`
Status: `pass`
Capability complete: `True`

## Candidate

- **agent-infra/sandbox** (Docker runtime)

## Summary

- **docker_version**: `29.4.1`
- **image**: `ghcr.io/agent-infra/sandbox:latest`
- **container_name**: `become-manus-sandbox`
- **container_status**: `running`
- **python_code_execution**: `pass (2+2 = 4 via Jupyter kernel)`
- **health_endpoint**: `pass ({"status": "healthy"})`
- **sandbox_services**:
  - `python-server (port 8091)`
  - `code-server (port 8200)`
  - `jupyter (port 8888)`
  - `mcp-hub (port 8079)`
  - `mcp-server-browser (port 8100)`
  - `nginx reverse proxy (port 8080)`
  - `tigervnc (port 5900)`
  - `websocket proxy (port 6080)`
  - `chrome browser (port 9222)`
- **api_routes_discovered**:
  - `/v1/code/execute — Python code execution via Jupyter`
  - `/v1/jupyter/execute — Jupyter cell execution`
  - `/v1/file/* — file operations`
  - `/v1/sandbox/* — sandbox management`
  - `/v1/shell/* — shell session management`
  - `/v1/browser/* — browser automation`
  - `/v1/mcp/* — MCP hub proxy`
  - `/v1/nodejs/* — Node.js execution`
  - `/v1/skills/* — skills management`
  - `/health — health check`
  - `/terminal — web terminal`
  - `/llms.txt — API documentation for LLMs`
- **mcp_servers_configured**:
  - `sandbox (streamable-http, port 8091)`
  - `browser (streamable-http, port 8100)`
  - `chrome_devtools (stdio)`

## Commands

- ✅ `d o c k e r   r u n   - - s e c u r i t y - o p t   s e c c o m p = u n c o n f i n e d   - - r m   - d   - - n a m e   b e c o m e - m a n u s - s a n d b o x   - p   8 0 8 0 : 8 0 8 0   g h c r . i o / a g e n t - i n f r a / s a n d b o x : l a t e s t`
  - stdout: `Container started, health: starting`
- ✅ `d o c k e r   e x e c   b e c o m e - m a n u s - s a n d b o x   c u r l   - s   h t t p : / / 1 2 7 . 0 . 0 . 1 : 8 0 9 1 / h e a l t h`
  - stdout: `{"status": "healthy"}`
- ✅ `d o c k e r   e x e c   b e c o m e - m a n u s - s a n d b o x   c u r l   - s   - X   P O S T   h t t p : / / 1 2 7 . 0 . 0 . 1 : 8 0 9 1 / v 1 / c o d e / e x e c u t e   - H   ' C o n t e n t - T y p e :   a p p l i c a t i o n / j s o n '   - d   ' { " c o d e " :   " 2 + 2 " ,   " l a n g u a g e " :   " p y t h o n " } '`
  - stdout: `{"success":true,"data":{"language":"python","status":"ok","outputs":[{"output_type":"execute_result","data":{"text/plain":"4"}}]}}`

## Services Discovered

- python-server (port 8091)
- code-server (port 8200)
- jupyter (port 8888)
- mcp-hub (port 8079)
- mcp-server-browser (port 8100)
- nginx reverse proxy (port 8080)
- tigervnc (port 5900)
- websocket proxy (port 6080)
- chrome browser (port 9222)

## API Routes Discovered

- `/v1/code/execute — Python code execution via Jupyter`
- `/v1/jupyter/execute — Jupyter cell execution`
- `/v1/file/* — file operations`
- `/v1/sandbox/* — sandbox management`
- `/v1/shell/* — shell session management`
- `/v1/browser/* — browser automation`
- `/v1/mcp/* — MCP hub proxy`
- `/v1/nodejs/* — Node.js execution`
- `/v1/skills/* — skills management`
- `/health — health check`
- `/terminal — web terminal`
- `/llms.txt — API documentation for LLMs`

## Safety

- `workspace`: /home/josh/workspace
- `output_dir`: /home/josh/workspace/outputs/become-manus/runtime-e2e
- `global_python_mutation`: none_intended
- `system_config_mutation`: none_intended
- `credential_use`: none
- `container_isolation`: Docker container with --security-opt seccomp=unconfined, --rm (auto-delete on stop), isolated filesystem, port 8080 bound to localhost
- `cleanup_command`: docker stop become-manus-sandbox
