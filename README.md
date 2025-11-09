# meaningful-pdf-names

Offline-friendly CLI to turn your messy paper filenames into **compact, keyword-rich names** based on the PDF's first page.

Example:

`final_v3_really_final.pdf` → `urban-resilience-transport-inequality-policy-a9f.pdf`

## Features

- Uses only the **first page** (title, authors, abstract region) for speed
- Up to **5 meaningful keywords** per file
- Adds a **3-character [a-z0-9] suffix** to avoid collisions
- Works fully **offline** with `pypdf`
- Optional: use a small local Hugging Face summarizer
  (`sshleifer/distilbart-cnn-12-6`) via `transformers` + `torch`

## Prerequisites

- **Python 3.9+** installed on your system
- **pip** (Python package manager) - usually comes with Python

## Quick Install

### From PyPI (Recommended)

```bash
pip install meaningful-pdf-names
```

## Quick Start Guide

### For Mac Users

1. **Install the package** (see above)
2. **Navigate to your PDF folder**:
   - Open Finder and go to the folder containing your PDFs
   - Right-click on the folder and select "New Terminal at Folder"
   - This opens Terminal directly in that folder
3. **Run the command**:
   ```bash
   mpn .
   ```

### For Linux Users

1. **Install the package** (see above)
2. **Navigate to your PDF folder**:
   ```bash
   cd /path/to/your/pdf/folder
   ```
3. **Run the command**:
   ```bash
   mpn .
   ```

### For Any Folder Location

If you want to rename PDFs in a different folder without navigating there:

```bash
mpn /full/path/to/your/pdf/folder
```

## Usage Examples

**Basic usage (current folder):**
```bash
mpn .
```

**Specific folder:**
```bash
mpn ~/Downloads/research_papers
mpn /Users/username/Documents/PDFs
```

**Dry run (preview changes without renaming):**
```bash
mpn . --dry-run
```

**Quiet mode (minimal output):**
```bash
mpn . --quiet
```

## What It Does

- Scans all PDF files in the specified folder
- Extracts text from just the first page (fast!)
- Identifies meaningful keywords from titles, authors, abstracts
- Generates clean, readable filenames like:
  - `climate-change-urban-planning-sustainability-a9f.pdf`
  - `machine-learning-neural-networks-research-4x2.pdf`
  - `healthcare-policy-digital-transformation-b7c.pdf`

## Why Not Existing Tools?

Other tools often:

* Depend on **OpenAI / web APIs** (requires internet, API keys)
* Require DOIs or external metadata (not always available)
* Use long `Author - Title - Year` patterns (hard to read)

`meaningful-pdf-names` is:

* **Local-only** (no API keys, no network required)
* **Fast** (first-page only extraction)
* **Slug-based**: short, grep- and git-friendly names

## License

MIT
