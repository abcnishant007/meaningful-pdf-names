import argparse
import random
import string
import re
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "onto",
    "but", "not", "are", "were", "was", "have", "has", "had", "their",
    "its", "our", "your", "about", "using", "use", "based", "on", "of",
    "in", "to", "by", "an", "a", "as", "is", "be", "or", "we", "can",
    "such", "these", "those", "also", "it", "at"
}

_SUMMARIZER = None


def get_summarizer():
    """
    Lazy-load a small local HF summarization model, if transformers is installed.
    """
    global _SUMMARIZER
    if _SUMMARIZER is not None:
        return _SUMMARIZER

    if pipeline is None:
        return None

    try:
        _SUMMARIZER = pipeline(
            "summarization",
            model="sshleifer/distilbart-cnn-12-6",
            device=-1,  # CPU; user can change if needed
        )
    except Exception:
        _SUMMARIZER = None

    return _SUMMARIZER


def summarize_text(text: str, max_chars: int = 4000) -> str:
    """
    Summarize text using a local HF model if available.
    Falls back to original text on any failure.
    """
    text = text.strip()
    if not text:
        return ""

    summarizer = get_summarizer()
    if summarizer is None:
        return text

    chunk = text[:max_chars]
    try:
        out = summarizer(
            chunk,
            max_length=80,
            min_length=20,
            do_sample=False,
        )
        summary = (out[0].get("summary_text") or "").strip()
        return summary or text
    except Exception:
        return text


def extract_text_keywords(pdf_path: Path, max_keywords: int = 5, pages_to_read: int = 2):
    """
    Extract up to `max_keywords` from the first `pages_to_read` pages of the PDF.
    If `pages_to_read` exceeds total pages, reads all available pages.
    """
    text = ""

    if PdfReader is not None:
        try:
            reader = PdfReader(str(pdf_path))
            total_pages = len(reader.pages)
            if total_pages > 0:
                # Determine how many pages to actually read
                pages_to_extract = min(pages_to_read, total_pages)
                
                # Extract text from the first N pages
                for i in range(pages_to_extract):
                    page = reader.pages[i]
                    page_text = (page.extract_text() or "").strip()
                    if page_text:
                        text += page_text + " "
        except Exception:
            text = ""

    if not text.strip():
        # fallback: original filename as text source
        text = pdf_path.stem

    # Clean the text - remove URLs, DOIs, and other noise
    cleaned_text = clean_extracted_text(text)
    
    summarized = summarize_text(cleaned_text) or cleaned_text

    # Basic tokenization on summary
    tokens = re.findall(r"[A-Za-z][A-Za-z\-]{1,}", summarized.lower())
    filtered = [
        t for t in tokens
        if t not in STOPWORDS and len(t) > 2
    ]

    if not filtered:
        # fallback to filename-derived tokens
        fallback_tokens = re.findall(r"[A-Za-z0-9]+", pdf_path.stem.lower())
        filtered = [t for t in fallback_tokens if len(t) > 1] or ["paper"]

    # Deduplicate in order
    seen = set()
    ordered = []
    for t in filtered:
        if t not in seen:
            seen.add(t)
            ordered.append(t)

    return ordered[:max_keywords]


def clean_extracted_text(text: str) -> str:
    """
    Clean extracted PDF text by removing URLs, DOIs, emails, and other noise.
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://[^\s]+', '', text)
    text = re.sub(r'www\.[^\s]+', '', text)
    
    # Remove DOIs
    text = re.sub(r'doi:[^\s]+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'10\.\d{4,9}/[-._;()/:A-Z0-9]+', '', text, flags=re.IGNORECASE)
    
    # Remove emails
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove common PDF metadata patterns
    text = re.sub(r'received:\s*\d{1,2}\s+\w+\s+\d{4}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'accepted:\s*\d{1,2}\s+\w+\s+\d{4}', '', text, flags=re.IGNORECASE)
    text = re.sub(r'published:\s*\d{1,2}\s+\w+\s+\d{4}', '', text, flags=re.IGNORECASE)
    
    # Remove page numbers and headers/footers
    text = re.sub(r'\b\d{1,3}\b', '', text)  # Remove standalone numbers (likely page numbers)
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def slugify_keywords(keywords):
    """
    Turn keywords into a filesystem-safe slug.
    """
    cleaned = []
    for kw in keywords:
        kw = re.sub(r"[^a-z0-9\-]+", "-", kw.lower())
        kw = re.sub(r"-{2,}", "-", kw).strip("-")
        if kw:
            cleaned.append(kw)
    if not cleaned:
        cleaned = ["paper"]
    return "-".join(cleaned)


def random_suffix(length: int = 3):
    """
    Generate a short random suffix to minimize collisions.
    """
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choices(alphabet, k=length))


def build_new_name(keywords, suffix_len=3, max_len=120):
    """
    Build the base part of the new filename (without .pdf).
    """
    base_slug = slugify_keywords(keywords)

    # Reserve for "-xyz.pdf"
    max_base_len = max_len - (1 + suffix_len + 4)
    if max_base_len < 10:
        max_base_len = 10

    if len(base_slug) > max_base_len:
        base_slug = base_slug[:max_base_len].rstrip("-")

    return base_slug


def unique_target_path(folder: Path, base_slug: str, suffix_len: int = 3) -> Path:
    """
    Generate a unique filename in `folder` using base_slug + random suffix.
    """
    while True:
        suffix = random_suffix(suffix_len)
        candidate = folder / f"{base_slug}-{suffix}.pdf"
        if not candidate.exists():
            return candidate


def rename_pdfs(folder: Path, dry_run: bool = False, verbose: bool = True, pages_to_read: int = 2):
    """
    Rename all PDFs in the folder using text from the first `pages_to_read` pages.
    """
    if not folder.is_dir():
        raise ValueError(f"{folder} is not a directory")

    pdf_files = sorted(
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() == ".pdf"
    )

    if verbose:
        print(f"Found {len(pdf_files)} PDF(s) in {folder}")

    for pdf in pdf_files:
        keywords = extract_text_keywords(pdf, pages_to_read=pages_to_read)
        base_slug = build_new_name(keywords)
        target = unique_target_path(folder, base_slug)

        if target.name == pdf.name:
            if verbose:
                print(f"Skip (already well-named): {pdf.name}")
            continue

        if verbose:
            print(f"{pdf.name} -> {target.name}")

        if not dry_run:
            pdf.rename(target)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Rename PDFs using text-derived keywords plus a short suffix "
            "for clean, meaningful filenames."
        )
    )
    parser.add_argument(
        "folder",
        type=str,
        help="Path to folder containing PDFs."
    )
    parser.add_argument(
        "-p", "--pages",
        type=int,
        default=2,
        help="Number of pages to read from each PDF (default: 2). "
             "If larger than total pages, reads all available pages."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned renames without changing files."
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output."
    )

    args = parser.parse_args()
    folder = Path(args.folder).expanduser().resolve()

    rename_pdfs(folder, dry_run=args.dry_run, verbose=not args.quiet, pages_to_read=args.pages)


if __name__ == "__main__":
    main()
