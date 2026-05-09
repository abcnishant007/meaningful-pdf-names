#!/usr/bin/env python3

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from meaningful_pdf_names.cli import extract_text_with_fallback, is_bad_text, rename_pdf_file


class TestExtractionFallbacks(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.tmp_path = Path(self.temp_dir)

    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir)

    def test_is_bad_text_rejects_noise(self):
        self.assertTrue(is_bad_text("@@@ \ufffd \ufffd \ufffd"))
        self.assertTrue(is_bad_text("short text"))

    def test_extraction_prefers_pypdf_when_quality_good(self):
        pdf_path = self.tmp_path / "paper.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        good = (
            "This is a meaningful abstract about transport planning and urban policy "
            "with enough normal words to pass quality checks. "
        ) * 3

        with patch("meaningful_pdf_names.cli._extract_with_pypdf", return_value=(good, Mock())):
            with patch("meaningful_pdf_names.cli._extract_with_pdfminer", return_value=""):
                text, source = extract_text_with_fallback(pdf_path, pages_to_read=2)

        self.assertEqual(source, "pypdf")
        self.assertEqual(text, good)

    def test_extraction_falls_back_to_pdfminer(self):
        pdf_path = self.tmp_path / "weak.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        weak = "\ufffd \ufffd @@"
        good_pdfminer = (
            "Detailed methods and results section describing robust extraction quality "
            "and readable layout text in natural language for downstream naming. "
        ) * 3

        with patch("meaningful_pdf_names.cli._extract_with_pypdf", return_value=(weak, Mock())):
            with patch("meaningful_pdf_names.cli._extract_with_pdfminer", return_value=good_pdfminer):
                text, source = extract_text_with_fallback(pdf_path, pages_to_read=2)

        self.assertEqual(source, "pdfminer.six")
        self.assertEqual(text, good_pdfminer)

    def test_extraction_falls_back_to_metadata(self):
        pdf_path = self.tmp_path / "scan.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        weak = "\ufffd\ufffd"
        reader = Mock()
        reader.metadata = {
            "/Title": "Urban Heat Islands and Public Health Longitudinal Study",
            "/Subject": "Climate adaptation policy and city planning evidence",
        }

        with patch("meaningful_pdf_names.cli._extract_with_pypdf", return_value=(weak, reader)):
            with patch("meaningful_pdf_names.cli._extract_with_pdfminer", return_value=weak):
                text, source = extract_text_with_fallback(pdf_path, pages_to_read=2)

        self.assertEqual(source, "metadata")
        self.assertIn("Urban Heat Islands", text)

    def test_extraction_falls_back_to_filename_stem(self):
        pdf_path = self.tmp_path / "my-research-paper.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

        with patch("meaningful_pdf_names.cli._extract_with_pypdf", return_value=("", Mock())):
            with patch("meaningful_pdf_names.cli._extract_with_pdfminer", return_value=""):
                with patch("meaningful_pdf_names.cli._extract_metadata_text", return_value=""):
                    text, source = extract_text_with_fallback(pdf_path, pages_to_read=2)

        self.assertEqual(source, "filename fallback")
        self.assertEqual(text, "my-research-paper")

    def test_dry_run_logs_extractor_source(self):
        pdf_path = self.tmp_path / "paper.pdf"
        pdf_path.write_bytes(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        with patch(
            "meaningful_pdf_names.cli.extract_text_with_fallback",
            return_value=("A " * 200, "pdfminer.six"),
        ):
            with patch("builtins.print") as mock_print:
                rename_pdf_file(pdf_path, dry_run=True, verbose=True, pages_to_read=2)
        joined = "\n".join(" ".join(map(str, call.args)) for call in mock_print.call_args_list)
        self.assertIn("[extractor: pdfminer.six]", joined)


if __name__ == "__main__":
    unittest.main()
