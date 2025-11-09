# meaningful-pdf-names

Offline-friendly CLI to turn your messy paper filenames into **compact, keyword-rich names** based on the PDF's first page.

Example:

`final_v3_really_final.pdf` → `urban-resilience-transport-inequality-policy-a9f.pdf`

## Features

- Uses only the **first page** (title, authors, abstract region) for speed.
- Up to **5 meaningful keywords** per file.
- Adds a **3-character [a-z0-9] suffix** to avoid collisions.
- Works fully **offline** with `pypdf`.
- Optional: use a small local Hugging Face summarizer
  (`sshleifer/distilbart-cnn-12-6`) via `transformers` + `torch`.

## Install

From source / Git:

```bash
pip install git+https://github.com/yourname/meaningful-pdf-names.git
```

(When published to PyPI:)

```bash
pip install meaningful-pdf-names
```

With optional local summarizer:

```bash
pip install "meaningful-pdf-names[summarizer]"
```

## Usage

```bash
meaningful-pdf-names /path/to/pdfs
meaningful-pdf-names /path/to/pdfs --dry-run
mpn /path/to/pdfs
```

## Why not existing tools?

Other tools often:

* Depend on **OpenAI / web APIs**.
* Require DOIs or external metadata.
* Use long `Author - Title - Year` patterns.

`meaningful-pdf-names` is:

* **Local-only** (no API keys, no network).
* **Fast** (first-page only).
* **Slug-based**: short, grep- and git-friendly names.

## License

MIT
