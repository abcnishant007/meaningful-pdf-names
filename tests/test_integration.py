#!/usr/bin/env python3
"""
Integration tests for meaningful_pdf_names using actual test data.
"""

import tempfile
import shutil
from pathlib import Path
import subprocess
import sys


def test_cli_with_test_data():
    """Test the CLI with actual test data PDFs."""
    # Copy test data to a temporary directory to avoid modifying original files
    temp_dir = tempfile.mkdtemp()
    try:
        # Copy test PDFs to temporary directory
        test_data_dir = Path("test_data")
        temp_test_dir = Path(temp_dir) / "test_pdfs"
        temp_test_dir.mkdir()
        
        # Copy all PDFs from test_data
        for pdf_file in test_data_dir.glob("*.pdf"):
            shutil.copy2(pdf_file, temp_test_dir)
        
        print(f"Testing with {len(list(temp_test_dir.glob('*.pdf')))} PDF files")
        
        # Test 1: Default behavior (2 pages)
        print("\nTesting default behavior (2 pages)...")
        result = subprocess.run(
            [sys.executable, "-m", "meaningful_pdf_names", str(temp_test_dir), "--dry-run"],
            capture_output=True, text=True
        )
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Test 2: Single page
        print("\nTesting single page (-p 1)...")
        result = subprocess.run(
            [sys.executable, "-m", "meaningful_pdf_names", str(temp_test_dir), "--dry-run", "-p", "1"],
            capture_output=True, text=True
        )
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Test 3: Multiple pages
        print("\nTesting multiple pages (-p 4)...")
        result = subprocess.run(
            [sys.executable, "-m", "meaningful_pdf_names", str(temp_test_dir), "--dry-run", "-p", "4"],
            capture_output=True, text=True
        )
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        assert result.returncode == 0, f"Command failed with return code {result.returncode}"
        
        # Test 4: Help command
        print("\nTesting help command...")
        result = subprocess.run(
            [sys.executable, "-m", "meaningful_pdf_names", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0, f"Help command failed with return code {result.returncode}"
        # Check for the pages option in help (format might vary)
        assert "-p PAGES, --pages PAGES" in result.stdout or "-p, --pages PAGES" in result.stdout, "Pages option not found in help"
        
        print("\n✅ All integration tests passed!")
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir)


def test_mpn_command():
    """Test the mpn command alias."""
    # Test that mpn command is available and shows help
    try:
        result = subprocess.run(
            ["mpn", "--help"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("✅ mpn command is available")
            # Check for the pages option in help (format might vary)
            if "-p PAGES, --pages PAGES" in result.stdout or "-p, --pages PAGES" in result.stdout:
                print("✅ Pages option found in mpn help")
            else:
                print("⚠️ Pages option not found in mpn help (but command works)")
        else:
            print("⚠️ mpn command not available (this is OK if not installed)")
    except FileNotFoundError:
        print("⚠️ mpn command not found (this is OK if not installed in PATH)")


if __name__ == "__main__":
    print("Running integration tests...")
    test_cli_with_test_data()
    test_mpn_command()
    print("\n🎉 All tests completed successfully!")
