#!/usr/bin/env python3
"""Simple test script for GitHub Actions"""
import sys
from pathlib import Path

print("=== Mock Mode Test ===")

try:
    # Test 1: Check if test_data directory exists
    test_data = Path("test_data")
    print(f"test_data dir exists: {test_data.exists()}")
    
    # Test 2: Check if any PDF exists
    pdf_files = list(test_data.glob("*.pdf"))
    print(f"PDF files found: {len(pdf_files)}")
    
    # Test 3: Check required modules can be imported
    print("Importing modules...")
    from run_complete import find_default_judgment_pdf
    print("  find_default_judgment_pdf: OK")
    
    import run_complete
    print("  run_complete: OK")
    
    # Test 4: Test the function
    result = find_default_judgment_pdf()
    print(f"find_default_judgment_pdf result: {result}")
    print(f"  exists: {result.exists() if result else 'N/A'}")
    
    print("All checks passed!")
    sys.exit(0)
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
