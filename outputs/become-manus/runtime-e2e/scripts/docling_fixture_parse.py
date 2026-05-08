import json
import sys
import traceback
from pathlib import Path

from docling.document_converter import DocumentConverter

sources = [Path(sys.argv[1]), Path(sys.argv[2])]
markdown_path = Path(sys.argv[3])
payload_path = Path(sys.argv[4])
errors = []
best = None
converter = DocumentConverter()
for source in sources:
    try:
        result = converter.convert(source)
        markdown = result.document.export_to_markdown()
        contains = {
            "become_manus": "Become Manus" in markdown,
            "docling": "Docling" in markdown,
        }
        current = {
            "source": str(source),
            "markdown_chars": len(markdown),
            "contains": contains,
            "markdown": markdown,
        }
        if all(contains.values()) and len(markdown) > 20:
            best = current
            break
        if best is None:
            best = current
    except Exception as exc:
        errors.append({"source": str(source), "error": f"{type(exc).__name__}: {exc}", "traceback_tail": traceback.format_exc()[-2000:]})
ok = bool(best and all(best["contains"].values()) and best["markdown_chars"] > 20)
if best:
    markdown_path.write_text(best["markdown"], encoding="utf-8")
payload = {
    "ok": ok,
    "best_source": best["source"] if best else None,
    "markdown_chars": best["markdown_chars"] if best else 0,
    "contains": best["contains"] if best else {},
    "errors": errors,
}
payload_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(payload, sort_keys=True))
raise SystemExit(0 if ok else 2)
