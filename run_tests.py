#!/usr/bin/env python3
"""
Test runner script for meaningful-pdf-names.
Run this before releases to ensure everything works correctly.
"""

import sys
import subprocess
import os


def run_command(cmd, description):
    """Run a command and print the result."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SUCCESS")
        if result.stdout.strip():
            print("Output:", result.stdout.strip())
    else:
        print("❌ FAILED")
        print("Return code:", result.returncode)
        if result.stdout.strip():
            print("STDOUT:", result.stdout.strip())
        if result.stderr.strip():
            print("STDERR:", result.stderr.strip())
        return False
    
    return True


def main():
    """Run all tests."""
    print("🧪 Running meaningful-pdf-names test suite")
    print("This validates the package before release.")
    
    all_passed = True
    
    # Test 1: Unit tests
    all_passed &= run_command(
        [sys.executable, "-m", "unittest", "discover", "tests", "-v"],
        "Unit tests"
    )
    
    # Test 2: Integration tests
    all_passed &= run_command(
        [sys.executable, "tests/test_integration.py"],
        "Integration tests with test data"
    )
    
    # Test 3: CLI help
    all_passed &= run_command(
        [sys.executable, "-m", "meaningful_pdf_names", "--help"],
        "CLI help command"
    )
    
    # Test 4: Dry run with test data (default pages)
    all_passed &= run_command(
        [sys.executable, "-m", "meaningful_pdf_names", "test_data", "--dry-run"],
        "Dry run with default pages (2)"
    )
    
    # Test 5: Dry run with custom pages
    all_passed &= run_command(
        [sys.executable, "-m", "meaningful_pdf_names", "test_data", "--dry-run", "-p", "4"],
        "Dry run with custom pages (4)"
    )
    
    # Test 6: Package installation test
    print(f"\n{'='*60}")
    print("Testing package installation...")
    print('='*60)
    try:
        # Try to import the package
        import meaningful_pdf_names
        from meaningful_pdf_names.cli import extract_text_keywords, rename_pdfs
        print("✅ Package imports successfully")
        
        # Test function signatures
        import inspect
        sig1 = inspect.signature(extract_text_keywords)
        sig2 = inspect.signature(rename_pdfs)
        
        if 'pages_to_read' in sig1.parameters and 'pages_to_read' in sig2.parameters:
            print("✅ Function signatures include pages_to_read parameter")
        else:
            print("❌ Function signatures missing pages_to_read parameter")
            all_passed = False
            
    except ImportError as e:
        print(f"❌ Failed to import package: {e}")
        all_passed = False
    
    # Final result
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED! Package is ready for release.")
        return 0
    else:
        print("❌ SOME TESTS FAILED! Please fix issues before release.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
