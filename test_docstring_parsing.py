#!/usr/bin/env python3
"""
Test script for docstring parsing functionality.
"""

import re
from pathlib import Path

# Test the extraction function directly
def _extract_existing_usage_paths(content: str) -> tuple[str, set[str], str]:
    """Extract existing "Used in:" paths from docstring and return cleaned content."""
    # Pattern to match "Used in:" section with paths
    pattern = r"(\n\s*)(Used in:(?:\s*\n(?:\s*-\s*[^\n]+\n?)*)\s*)"
    
    match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
    if not match:
        return content, set(), ""
    
    # Extract indentation from the "Used in:" line
    indent_match = re.search(r"\n(\s*)Used in:", content)
    original_indent = indent_match.group(1) if indent_match else ""
    print(f"Debug indent_match: {indent_match}")
    if indent_match:
        print(f"Debug groups: {indent_match.groups()}")
    
    # Extract existing paths
    existing_paths = set()
    usage_section = match.group(2)
    
    # Find all paths in the usage section (lines starting with -)
    path_pattern = r"\s*-\s*(.+?)(?:\n|$)"
    for path_match in re.finditer(path_pattern, usage_section):
        path = path_match.group(1).strip()
        if path:
            existing_paths.add(path)
    
    # Remove the entire "Used in:" section from content
    cleaned_content = re.sub(pattern, "", content, flags=re.MULTILINE | re.DOTALL)
    
    return cleaned_content, existing_paths, original_indent

# Test cases
test_docstring1 = '''
    This is a function docstring.
    
    Used in:
    - old/path1.py
    - old/path2.py
    
    '''

test_docstring2 = '''
        Class docstring with different indentation.
        
        Used in:
        - existing/file.py
        - another/module.py
        
        '''

test_docstring3 = '''
    Function without existing usage.
    '''

print("Test 1:")
cleaned, paths, indent = _extract_existing_usage_paths(test_docstring1)
print(f"Cleaned: {repr(cleaned)}")
print(f"Paths: {paths}")
print(f"Indent: {repr(indent)}")

print("\nTest 2:")
cleaned, paths, indent = _extract_existing_usage_paths(test_docstring2)
print(f"Cleaned: {repr(cleaned)}")
print(f"Paths: {paths}")
print(f"Indent: {repr(indent)}")

print("\nTest 3:")
cleaned, paths, indent = _extract_existing_usage_paths(test_docstring3)
print(f"Cleaned: {repr(cleaned)}")
print(f"Paths: {paths}")
print(f"Indent: {repr(indent)}")