#!/usr/bin/env python3
"""
Unit tests for the page count functionality in meaningful_pdf_names.
"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Import the functions we want to test
from meaningful_pdf_names.cli import extract_text_keywords, rename_pdfs


class TestPageCountFunctionality(unittest.TestCase):
    """Test cases for the page count functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_pdf_path = Path(self.temp_dir) / "test.pdf"
        
    def tearDown(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    @patch('meaningful_pdf_names.cli.PdfReader')
    def test_extract_text_keywords_default_pages(self, mock_pdf_reader):
        """Test that extract_text_keywords reads 2 pages by default."""
        # Mock PDF reader with 5 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock() for _ in range(5)]
        
        # Mock page text extraction
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content"
        
        mock_pdf_reader.return_value = mock_reader
        
        # Call function with default pages_to_read
        result = extract_text_keywords(self.test_pdf_path)
        
        # Verify only first 2 pages were read
        self.assertEqual(mock_reader.pages[0].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[1].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[2].extract_text.call_count, 0)
        
    @patch('meaningful_pdf_names.cli.PdfReader')
    def test_extract_text_keywords_custom_pages(self, mock_pdf_reader):
        """Test that extract_text_keywords reads specified number of pages."""
        # Mock PDF reader with 5 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock() for _ in range(5)]
        
        # Mock page text extraction
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content"
        
        mock_pdf_reader.return_value = mock_reader
        
        # Call function with custom pages_to_read
        result = extract_text_keywords(self.test_pdf_path, pages_to_read=3)
        
        # Verify only first 3 pages were read
        self.assertEqual(mock_reader.pages[0].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[1].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[2].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[3].extract_text.call_count, 0)
        
    @patch('meaningful_pdf_names.cli.PdfReader')
    def test_extract_text_keywords_more_pages_than_total(self, mock_pdf_reader):
        """Test that extract_text_keywords handles page count > total pages."""
        # Mock PDF reader with only 2 pages
        mock_reader = Mock()
        mock_reader.pages = [Mock() for _ in range(2)]
        
        # Mock page text extraction
        for i, page in enumerate(mock_reader.pages):
            page.extract_text.return_value = f"Page {i+1} content"
        
        mock_pdf_reader.return_value = mock_reader
        
        # Call function with pages_to_read larger than total pages
        result = extract_text_keywords(self.test_pdf_path, pages_to_read=5)
        
        # Verify only available pages were read
        self.assertEqual(mock_reader.pages[0].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[1].extract_text.call_count, 1)
        # No more pages to read
        
    @patch('meaningful_pdf_names.cli.PdfReader')
    def test_extract_text_keywords_single_page(self, mock_pdf_reader):
        """Test that extract_text_keywords works with single page."""
        # Mock PDF reader with 1 page
        mock_reader = Mock()
        mock_reader.pages = [Mock()]
        mock_reader.pages[0].extract_text.return_value = "Single page content"
        
        mock_pdf_reader.return_value = mock_reader
        
        # Call function with pages_to_read=1
        result = extract_text_keywords(self.test_pdf_path, pages_to_read=1)
        
        # Verify only first page was read
        self.assertEqual(mock_reader.pages[0].extract_text.call_count, 1)
        
    @patch('meaningful_pdf_names.cli.PdfReader')
    def test_extract_text_keywords_empty_pages(self, mock_pdf_reader):
        """Test that extract_text_keywords handles empty pages gracefully."""
        # Mock PDF reader with 3 pages, second page empty
        mock_reader = Mock()
        mock_reader.pages = [Mock(), Mock(), Mock()]
        mock_reader.pages[0].extract_text.return_value = "Page 1 content"
        mock_reader.pages[1].extract_text.return_value = ""  # Empty page
        mock_reader.pages[2].extract_text.return_value = "Page 3 content"
        
        mock_pdf_reader.return_value = mock_reader
        
        # Call function
        result = extract_text_keywords(self.test_pdf_path, pages_to_read=3)
        
        # Verify all pages were attempted to be read
        self.assertEqual(mock_reader.pages[0].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[1].extract_text.call_count, 1)
        self.assertEqual(mock_reader.pages[2].extract_text.call_count, 1)
        
    def test_extract_text_keywords_pages_parameter(self):
        """Test that extract_text_keywords accepts pages_to_read parameter."""
        # This test verifies the function signature accepts the parameter
        import inspect
        sig = inspect.signature(extract_text_keywords)
        self.assertIn('pages_to_read', sig.parameters)
        self.assertEqual(sig.parameters['pages_to_read'].default, 2)
        
    def test_rename_pdfs_pages_parameter(self):
        """Test that rename_pdfs accepts pages_to_read parameter."""
        # This test verifies the function signature accepts the parameter
        import inspect
        sig = inspect.signature(rename_pdfs)
        self.assertIn('pages_to_read', sig.parameters)
        self.assertEqual(sig.parameters['pages_to_read'].default, 2)


if __name__ == '__main__':
    unittest.main()
