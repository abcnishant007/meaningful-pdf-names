#!/usr/bin/env python3
"""
Unit tests specifically for the CLI -p/--pages option functionality.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
import sys

# Import the functions we want to test
from meaningful_pdf_names.cli import main, extract_text_keywords, rename_pdfs


class TestCLIPagesOption(unittest.TestCase):
    """Test cases for the CLI -p/--pages option."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = Path(self.temp_dir) / "test.pdf"
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_cli_help_shows_pages_option(self):
        """Test that the CLI help shows the -p/--pages option."""
        result = subprocess.run(
            [sys.executable, "-m", "meaningful_pdf_names", "--help"],
            capture_output=True, text=True
        )
        self.assertEqual(result.returncode, 0)
        # Check for both possible formats of the help output
        self.assertTrue(
            "-p, --pages PAGES" in result.stdout or "-p PAGES, --pages PAGES" in result.stdout,
            f"Pages option not found in help output: {result.stdout}"
        )
        self.assertIn("Number of pages to read from each PDF", result.stdout)
    
    @patch('meaningful_pdf_names.cli.rename_pdfs')
    def test_cli_pages_option_passed_to_rename_pdfs(self, mock_rename_pdfs):
        """Test that the -p option value is passed to rename_pdfs function."""
        with patch('sys.argv', ['meaningful_pdf_names', 'test.pdf', '-p', '5']):
            with patch('sys.exit'):
                main()
        
        # Check that rename_pdfs was called with pages_to_read=5
        mock_rename_pdfs.assert_called_once()
        call_args = mock_rename_pdfs.call_args
        self.assertEqual(call_args[1]['pages_to_read'], 5)
    
    @patch('meaningful_pdf_names.cli.rename_pdfs')
    def test_cli_default_pages_option(self, mock_rename_pdfs):
        """Test that default pages value (2) is used when -p is not specified."""
        with patch('sys.argv', ['meaningful_pdf_names', 'test.pdf']):
            with patch('sys.exit'):
                main()
        
        # Check that rename_pdfs was called with default pages_to_read=2
        mock_rename_pdfs.assert_called_once()
        call_args = mock_rename_pdfs.call_args
        self.assertEqual(call_args[1]['pages_to_read'], 2)
    
    @patch('meaningful_pdf_names.cli.rename_pdfs')
    def test_cli_pages_option_with_dry_run(self, mock_rename_pdfs):
        """Test that -p option works with --dry-run."""
        with patch('sys.argv', ['meaningful_pdf_names', 'test.pdf', '-p', '3', '--dry-run']):
            with patch('sys.exit'):
                main()
        
        # Check that rename_pdfs was called with correct parameters
        mock_rename_pdfs.assert_called_once()
        call_args = mock_rename_pdfs.call_args
        self.assertEqual(call_args[1]['pages_to_read'], 3)
        self.assertEqual(call_args[1]['dry_run'], True)
    
    @patch('meaningful_pdf_names.cli.rename_pdfs')
    def test_cli_pages_option_with_quiet(self, mock_rename_pdfs):
        """Test that -p option works with --quiet."""
        with patch('sys.argv', ['meaningful_pdf_names', 'test.pdf', '-p', '4', '--quiet']):
            with patch('sys.exit'):
                main()
        
        # Check that rename_pdfs was called with correct parameters
        mock_rename_pdfs.assert_called_once()
        call_args = mock_rename_pdfs.call_args
        self.assertEqual(call_args[1]['pages_to_read'], 4)
        self.assertEqual(call_args[1]['verbose'], False)
    
    def test_cli_pages_option_parsing(self):
        """Test that CLI correctly parses different page values."""
        test_cases = [
            (['-p', '1'], 1),
            (['-p', '10'], 10),
            (['-p', '100'], 100),
            (['--pages', '5'], 5),
            (['--pages', '25'], 25),
        ]
        
        for args, expected_pages in test_cases:
            with self.subTest(args=args, expected_pages=expected_pages):
                with patch('meaningful_pdf_names.cli.rename_pdfs') as mock_rename_pdfs:
                    with patch('sys.argv', ['meaningful_pdf_names', 'test.pdf'] + args):
                        with patch('sys.exit'):
                            main()
                    
                    # Check that rename_pdfs was called with correct pages
                    mock_rename_pdfs.assert_called_once()
                    call_args = mock_rename_pdfs.call_args
                    self.assertEqual(call_args[1]['pages_to_read'], expected_pages)
                    mock_rename_pdfs.reset_mock()


if __name__ == '__main__':
    unittest.main()
