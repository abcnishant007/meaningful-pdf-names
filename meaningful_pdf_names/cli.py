import argparse
import random
import string
import re
from pathlib import Path
from typing import Tuple

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text
except ImportError:
    pdfminer_extract_text = None

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


def is_bad_text(text: str) -> bool:
    """
    Heuristic detector for low-quality extraction output.
    """
    if not text:
        return True

    normalized = re.sub(r"\s+", " ", text).strip()
    if len(normalized) < 80:
        return True

    word_tokens = re.findall(r"[A-Za-z]{3,}", normalized)
    if len(word_tokens) < 12:
        return True

    weird_chars = re.findall(r"[^\w\s\.,;:!?'\-\(\)\[\]/&%$#@]", normalized)
    if len(weird_chars) / max(len(normalized), 1) > 0.08:
        return True

    replacement_count = normalized.count("\ufffd")
    if replacement_count / max(len(normalized), 1) > 0.005:
        return True

    unique_words = {w.lower() for w in word_tokens}
    if len(unique_words) / max(len(word_tokens), 1) < 0.25:
        return True

    return False


def _extract_with_pypdf(pdf_path: Path, pages_to_read: int) -> Tuple[str, object]:
    if PdfReader is None:
        return "", None
    try:
        reader = PdfReader(str(pdf_path))
        total_pages = len(reader.pages)
        text_parts = []
        if total_pages > 0:
            pages_to_extract = min(pages_to_read, total_pages)
            for i in range(pages_to_extract):
                page_text = (reader.pages[i].extract_text() or "").strip()
                if page_text:
                    text_parts.append(page_text)
        return " ".join(text_parts), reader
    except Exception:
        return "", None


def _extract_with_pdfminer(pdf_path: Path, pages_to_read: int) -> str:
    if pdfminer_extract_text is None:
        return ""
    try:
        page_numbers = list(range(max(pages_to_read, 1)))
        return (pdfminer_extract_text(str(pdf_path), page_numbers=page_numbers) or "").strip()
    except Exception:
        return ""


def _extract_metadata_text(reader: object) -> str:
    if reader is None:
        return ""
    try:
        metadata = getattr(reader, "metadata", None) or {}
        fields = []
        for key in ("/Title", "/Subject", "/Author", "/Keywords"):
            value = metadata.get(key)
            if value:
                fields.append(str(value))
        return " ".join(fields).strip()
    except Exception:
        return ""


def extract_text_with_fallback(pdf_path: Path, pages_to_read: int = 2) -> Tuple[str, str]:
    """
    Extraction order:
    pypdf -> pdfminer.six -> metadata -> filename fallback.
    """
    pypdf_text, reader = _extract_with_pypdf(pdf_path, pages_to_read=pages_to_read)
    if not is_bad_text(pypdf_text):
        return pypdf_text, "pypdf"

    pdfminer_text = _extract_with_pdfminer(pdf_path, pages_to_read=pages_to_read)
    if not is_bad_text(pdfminer_text):
        return pdfminer_text, "pdfminer.six"

    metadata_text = _extract_metadata_text(reader)
    if not is_bad_text(metadata_text):
        return metadata_text, "metadata"

    return pdf_path.stem, "filename fallback"


def extract_text_keywords(pdf_path: Path, max_keywords: int = 5, pages_to_read: int = 2):
    """
    Extract up to `max_keywords` from the first `pages_to_read` pages of the PDF.
    If `pages_to_read` exceeds total pages, reads all available pages.
    """
    text, _ = extract_text_with_fallback(pdf_path, pages_to_read=pages_to_read)
    return extract_keywords_from_text(text, pdf_path=pdf_path, max_keywords=max_keywords)


def extract_keywords_from_text(text: str, pdf_path: Path, max_keywords: int = 5):
    """
    Convert extracted text into keyword tokens.
    """

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


def rename_pdf_file(pdf_path: Path, dry_run: bool = False, verbose: bool = True, pages_to_read: int = 2):
    """
    Rename a single PDF file using text from the first `pages_to_read` pages.
    """
    if not pdf_path.is_file():
        raise ValueError(f"{pdf_path} is not a file")
    
    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"{pdf_path} is not a PDF file")

    folder = pdf_path.parent
    extracted_text, extractor_used = extract_text_with_fallback(pdf_path, pages_to_read=pages_to_read)
    keywords = extract_keywords_from_text(extracted_text, pdf_path=pdf_path)
    base_slug = build_new_name(keywords)
    target = unique_target_path(folder, base_slug)

    if target.name == pdf_path.name:
        if verbose:
            print(f"Skip (already well-named): {pdf_path.name}")
        return

    if verbose:
        if dry_run:
            print(f"[extractor: {extractor_used}] {pdf_path.name}")
        print(f"{pdf_path.name} -> {target.name}")

    if not dry_run:
        pdf_path.rename(target)


def rename_pdfs_in_folder(folder: Path, dry_run: bool = False, verbose: bool = True, pages_to_read: int = 2):
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
        rename_pdf_file(pdf, dry_run=dry_run, verbose=verbose, pages_to_read=pages_to_read)


def rename_pdfs(paths: list, dry_run: bool = False, verbose: bool = True, pages_to_read: int = 2):
    """
    Rename PDFs from the given paths (can be files or folders).
    """
    processed_files = 0
    
    for path_str in paths:
        path = Path(path_str).expanduser().resolve()
        
        if path.is_file():
            if path.suffix.lower() == ".pdf":
                rename_pdf_file(path, dry_run=dry_run, verbose=verbose, pages_to_read=pages_to_read)
                processed_files += 1
            else:
                if verbose:
                    print(f"Skipping non-PDF file: {path.name}")
        elif path.is_dir():
            pdf_files_before = len(list(path.glob("*.pdf")))
            rename_pdfs_in_folder(path, dry_run=dry_run, verbose=verbose, pages_to_read=pages_to_read)
            processed_files += pdf_files_before
        else:
            if verbose:
                print(f"Skipping non-existent path: {path}")
    
    if verbose and processed_files == 0:
        print("No PDF files found to process.")


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Rename PDFs using text-derived keywords plus a short suffix "
            "for clean, meaningful filenames."
        )
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=str,
        help="Paths to PDF files or folders containing PDFs. "
             "Can specify multiple files/folders separated by spaces."
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

    rename_pdfs(args.paths, dry_run=args.dry_run, verbose=not args.quiet, pages_to_read=args.pages)


if __name__ == "__main__":
    main()
