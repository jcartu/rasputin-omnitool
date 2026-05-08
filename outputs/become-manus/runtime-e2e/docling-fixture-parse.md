# Docling Fixture Parse E2E

Generated: `2026-05-08T14:01:52.166365+00:00`
Status: `pass`
Capability complete: `True`

## Scope

actual Docling package install/import plus local DOCX/HTML fixture parse in disposable venv

## Summary

- `attempted_install`: `True`
- `install_ok`: `True`
- `attempted_parse`: `True`
- `parse_ok`: `True`
- `best_source`: `outputs/become-manus/runtime-e2e/fixtures/docling/become-manus-docling-fixture.docx`
- `markdown_chars`: `192`

## Commands

- `outputs/become-manus/runtime-e2e/.venv/bin/python -c import docling; print(getattr(docling, '__version__', 'import-ok'))` -> ok=`False` returncode=`1` timeout=`60`
  - stderr tail: `Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'docling'`
- `outputs/become-manus/runtime-e2e/.venv/bin/python -m pip install --no-input --no-cache-dir docling` -> ok=`True` returncode=`0` timeout=`600`
- `outputs/become-manus/runtime-e2e/.venv/bin/python -c import docling; print(getattr(docling, '__version__', 'import-ok'))` -> ok=`True` returncode=`0` timeout=`60`
- `outputs/become-manus/runtime-e2e/.venv/bin/python outputs/become-manus/runtime-e2e/scripts/docling_fixture_parse.py outputs/become-manus/runtime-e2e/fixtures/docling/become-manus-docling-fixture.docx outputs/become-manus/runtime-e2e/fixtures/docling/become-manus-docling-fixture.html outputs/become-manus/runtime-e2e/docling-extracted.md outputs/become-manus/runtime-e2e/docling-parse-payload.json` -> ok=`True` returncode=`0` timeout=`180`

## Artifacts

- `fixture_docx`: `outputs/become-manus/runtime-e2e/fixtures/docling/become-manus-docling-fixture.docx`
- `fixture_html`: `outputs/become-manus/runtime-e2e/fixtures/docling/become-manus-docling-fixture.html`
- `extracted_markdown`: `outputs/become-manus/runtime-e2e/docling-extracted.md`
- `parse_payload_json`: `outputs/become-manus/runtime-e2e/docling-parse-payload.json`
- `parse_script`: `outputs/become-manus/runtime-e2e/scripts/docling_fixture_parse.py`
- `report_json`: `outputs/become-manus/runtime-e2e/docling-fixture-parse.json`
- `report_markdown`: `outputs/become-manus/runtime-e2e/docling-fixture-parse.md`
