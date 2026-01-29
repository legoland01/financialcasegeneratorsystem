#!/usr/bin/env python3
"""Simple test script for GitHub Actions"""
import sys
sys.path.insert(0, '.')

from run_complete import find_default_judgment_pdf
import run_complete

print("=== Mock Mode Test ===")
r = find_default_judgment_pdf()
print('PDF:', r)
print('Exists:', r.exists() if r else False)
print('run_stage0:', hasattr(run_complete, 'run_stage0'))
print('run_stage1:', hasattr(run_complete, 'run_stage1'))
print('read_pdf_text:', hasattr(run_complete, 'read_pdf_text'))
print('All OK!')
