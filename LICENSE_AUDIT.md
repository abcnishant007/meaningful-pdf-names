# License Audit

Date: 2026-05-09
Project: meaningful-pdf-names

## Scope

- Direct runtime dependencies
- Transitive runtime dependencies
- Optional dependencies
- Build/packaging dependencies
- DMG installer/app bundle behavior

## Direct runtime dependencies

- `pypdf` (`>=5.0.0`): `BSD-3-Clause`
- `pdfminer.six` (`>=20250506`): `MIT`

Notes:
- Latest `pdfminer.six` on PyPI is `20260107` (MIT), but it requires Python `>=3.10`.
- Project supports Python `>=3.9`, so lower bound `>=20250506` is used for compatibility.

## Transitive runtime dependencies (from chosen extractor stack)

From `pdfminer.six`:
- `charset-normalizer>=2.0.0`: MIT
- `cryptography>=36.0.0`: Apache-2.0 OR BSD-3-Clause

From `cryptography`:
- `cffi>=2.0.0`: MIT
- `pycparser` (via `cffi`): BSD-3-Clause

From `pypdf`:
- No mandatory runtime dependencies for core extraction path.
- Optional `pypdf[crypto]` pulls crypto deps only when explicitly enabled.

## Optional dependencies

Project optional extra `summarizer`:
- `transformers>=4.45.0`: Apache-2.0 (metadata field)
- `torch>=2.0.0`: BSD-3-Clause

Notes:
- `summarizer` is optional and not required for core PDF extraction.
- No OCR dependencies were added.

## Build / packaging dependencies

From `pyproject.toml`:
- `setuptools>=61.0`: MIT
- `wheel`: MIT

## DMG / app bundle distribution notes

`create_DMG.sh` installs this package via `pipx install --force meaningful-pdf-names` and installs a Finder Quick Action wrapper.

Current codebase does not bundle or require:
- PyMuPDF / MuPDF (AGPL/commercial)
- OCRmyPDF, Tesseract, Poppler, or `pdf2image`

Therefore, no AGPL/GPL/LGPL/SSPL/BUSL/Commons-Clause/commercial-only runtime dependency was introduced in this change set.

## Risk flags

- No high-risk license detected in direct runtime deps for current extraction flow.
- Keep reviewing optional extras separately before including them in packaged defaults.
