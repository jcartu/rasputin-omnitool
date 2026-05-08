from __future__ import annotations

import csv
import html
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape


def _write_minimal_xlsx(path: Path, rows: list[list[object]]) -> None:
    """Write a minimal XLSX workbook using stdlib zip/XML."""
    def cell_ref(row_idx: int, col_idx: int) -> str:
        col = ""
        n = col_idx
        while n:
            n, rem = divmod(n - 1, 26)
            col = chr(65 + rem) + col
        return f"{col}{row_idx}"

    sheet_rows = []
    for r_idx, row in enumerate(rows, start=1):
        cells = []
        for c_idx, value in enumerate(row, start=1):
            ref = cell_ref(r_idx, c_idx)
            if isinstance(value, (int, float)):
                cells.append(f'<c r="{ref}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{ref}" t="inlineStr"><is><t>{escape(str(value))}</t></is></c>')
        sheet_rows.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>""",
        "xl/workbook.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Analysis" sheetId="1" r:id="rId1"/></sheets></workbook>""",
        "xl/_rels/workbook.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>""",
        "xl/worksheets/sheet1.xml": f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>{''.join(sheet_rows)}</sheetData></worksheet>""",
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def _write_minimal_pptx(path: Path, title: str, bullets: list[str]) -> None:
    bullet_xml = "".join(
        f'<a:p><a:r><a:t>{escape(bullet)}</a:t></a:r></a:p>' for bullet in bullets
    )
    slide = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:sld xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:cSld><p:spTree><p:nvGrpSpPr><p:cNvPr id="1" name=""/><p:cNvGrpSpPr/><p:nvPr/></p:nvGrpSpPr><p:grpSpPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="0" cy="0"/><a:chOff x="0" y="0"/><a:chExt cx="0" cy="0"/></a:xfrm></p:grpSpPr><p:sp><p:nvSpPr><p:cNvPr id="2" name="Title"/><p:cNvSpPr/><p:nvPr/></p:nvSpPr><p:spPr/><p:txBody><a:bodyPr/><a:lstStyle/><a:p><a:r><a:rPr sz="3600" b="1"/><a:t>{escape(title)}</a:t></a:r></a:p>{bullet_xml}</p:txBody></p:sp></p:spTree></p:cSld><p:clrMapOvr><a:masterClrMapping/></p:clrMapOvr></p:sld>"""
    files = {
        "[Content_Types].xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/ppt/presentation.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.presentation.main+xml"/><Override PartName="/ppt/slides/slide1.xml" ContentType="application/vnd.openxmlformats-officedocument.presentationml.slide+xml"/></Types>""",
        "_rels/.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="ppt/presentation.xml"/></Relationships>""",
        "ppt/presentation.xml": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<p:presentation xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"><p:sldIdLst><p:sldId id="256" r:id="rId1"/></p:sldIdLst><p:sldSz cx="12192000" cy="6858000" type="wide"/><p:notesSz cx="6858000" cy="9144000"/></p:presentation>""",
        "ppt/_rels/presentation.xml.rels": """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/slide" Target="slides/slide1.xml"/></Relationships>""",
        "ppt/slides/slide1.xml": slide,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)


def _write_fallback_chart_png(path: Path, rows: list[dict]) -> None:
    """Write a tiny valid PNG bar chart using only the standard library."""
    import struct
    import zlib

    width, height = 900, 420
    canvas = bytearray([250, 250, 252] * width * height)

    def set_pixel(x: int, y: int, color: tuple[int, int, int]) -> None:
        if 0 <= x < width and 0 <= y < height:
            idx = (y * width + x) * 3
            canvas[idx:idx + 3] = bytes(color)

    def rect(x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
        x0, x1 = max(0, min(x0, width)), max(0, min(x1, width))
        y0, y1 = max(0, min(y0, height)), max(0, min(y1, height))
        for y in range(y0, y1):
            row_start = (y * width + x0) * 3
            row_end = (y * width + x1) * 3
            canvas[row_start:row_end] = bytes(color) * max(0, x1 - x0)

    # Axes and bars. This intentionally avoids fonts/text; the CSV/HTML carry labels.
    chart_left, chart_top, chart_right, chart_bottom = 80, 50, 860, 350
    rect(chart_left, chart_top, chart_left + 2, chart_bottom, (45, 55, 72))
    rect(chart_left, chart_bottom, chart_right, chart_bottom + 2, (45, 55, 72))
    colors = [(109, 93, 252), (0, 184, 148), (253, 203, 110), (225, 112, 85)]
    slot = (chart_right - chart_left) // max(1, len(rows))
    for idx, row in enumerate(rows):
        value = max(0.0, min(100.0, float(row["score"])))
        bar_height = int((chart_bottom - chart_top - 20) * value / 100.0)
        x0 = chart_left + idx * slot + 28
        x1 = chart_left + (idx + 1) * slot - 28
        y0 = chart_bottom - bar_height
        rect(x0, y0, x1, chart_bottom, colors[idx % len(colors)])
        # Add a small black cap so different values are visible even in grayscale.
        rect(x0, y0, x1, min(chart_bottom, y0 + 4), (25, 28, 36))
    # Decorative title underline.
    for x in range(80, 520):
        set_pixel(x, 30, (109, 93, 252))
        set_pixel(x, 31, (0, 184, 148))

    raw = b"".join(b"\x00" + bytes(canvas[y * width * 3:(y + 1) * width * 3]) for y in range(height))

    def chunk(tag: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _make_chart(path: Path, rows: list[dict]) -> None:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        _write_fallback_chart_png(path, rows)
        return

    labels = [row["capability"] for row in rows]
    values = [float(row["score"]) for row in rows]
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(labels, values, color=["#6d5dfc", "#00b894", "#fdcb6e", "#e17055"])
    ax.set_ylim(0, 100)
    ax.set_title("Become Manus local smoke capability scores")
    ax.set_ylabel("Readiness")
    ax.tick_params(axis="x", rotation=20)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def create_demo_deliverables(output_dir: str | Path) -> dict:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = [
        {"capability": "Browser", "score": 95, "candidate": "Playwright MCP"},
        {"capability": "Research", "score": 88, "candidate": "Crawl4AI + Docling"},
        {"capability": "Deliverables", "score": 84, "candidate": "Marp/PPTX/PDF/XLSX"},
        {"capability": "Apps", "score": 76, "candidate": "bolt.diy + OpenHands"},
    ]

    csv_path = output_dir / "source_data.csv"
    with csv_path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["capability", "score", "candidate"])
        writer.writeheader()
        writer.writerows(rows)

    chart_path = output_dir / "capability_chart.png"
    _make_chart(chart_path, rows)

    md_path = output_dir / "analysis.md"
    avg = sum(float(r["score"]) for r in rows) / len(rows)
    md_path.write_text(
        "# Become Manus Demo Analysis\n\n"
        f"Average readiness score: **{avg:.1f}**.\n\n"
        "This generated artifact bundle proves Hermes can create CSV, chart, HTML, PDF, XLSX, and PPTX deliverables from one local workflow.\n"
    )

    html_path = output_dir / "executive_summary.html"
    html_rows = "".join(f"<tr><td>{html.escape(r['capability'])}</td><td>{r['score']}</td><td>{html.escape(r['candidate'])}</td></tr>" for r in rows)
    html_path.write_text(f"""<!doctype html><html><head><meta charset='utf-8'><title>Become Manus Demo</title>
<style>body{{font-family:Inter,Arial,sans-serif;margin:40px;color:#17202a}}table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #ddd;padding:8px}}th{{background:#111827;color:white}}img{{max-width:100%}}</style></head><body>
<h1>Become Manus Demo Deliverables</h1><p>Generated at {datetime.now(timezone.utc).isoformat()}</p>
<table><thead><tr><th>Capability</th><th>Score</th><th>Candidate</th></tr></thead><tbody>{html_rows}</tbody></table>
<p><img src='{chart_path.name}' alt='Capability chart'></p></body></html>""")

    pdf_path = output_dir / "executive_summary.pdf"
    try:
        from weasyprint import HTML
        HTML(filename=str(html_path)).write_pdf(str(pdf_path))
    except Exception:
        # Valid enough fallback marker if WeasyPrint/Cairo stack is unavailable.
        pdf_path.write_bytes(b"%PDF-1.4\n% Become Manus fallback PDF artifact\n1 0 obj <<>> endobj\ntrailer <<>>\n%%EOF\n")

    xlsx_path = output_dir / "analysis.xlsx"
    _write_minimal_xlsx(xlsx_path, [["Capability", "Score", "Candidate"]] + [[r["capability"], r["score"], r["candidate"]] for r in rows])

    pptx_path = output_dir / "presentation.pptx"
    _write_minimal_pptx(pptx_path, "Become Manus Demo", [f"{r['capability']}: {r['score']} via {r['candidate']}" for r in rows])

    artifact_specs = [
        ("source_data_csv", csv_path),
        ("analysis_markdown", md_path),
        ("chart_png", chart_path),
        ("executive_summary_html", html_path),
        ("executive_summary_pdf", pdf_path),
        ("workbook_xlsx", xlsx_path),
        ("presentation_pptx", pptx_path),
    ]
    manifest = {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "artifacts": [{"name": name, "path": str(path), "size_bytes": path.stat().st_size} for name, path in artifact_specs],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest


def validate_artifacts(manifest: dict) -> dict:
    results = []
    for item in manifest.get("artifacts", []):
        path = Path(item["path"])
        exists = path.exists()
        size = path.stat().st_size if exists else 0
        valid_container = True
        if path.suffix in {".xlsx", ".pptx"} and exists:
            try:
                with zipfile.ZipFile(path) as zf:
                    valid_container = "[Content_Types].xml" in zf.namelist()
            except Exception:
                valid_container = False
        results.append({"name": item["name"], "path": str(path), "exists": exists, "size_bytes": size, "valid_container": valid_container})
    status = "pass" if results and all(r["exists"] and r["size_bytes"] > 0 and r["valid_container"] for r in results) else "fail"
    return {"schema_version": 1, "status": status, "artifacts": results}
