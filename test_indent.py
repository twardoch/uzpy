#!/usr/bin/env python3
"""Test module with properly indented docstring.

This module is for testing proper indentation handling
in docstring modifications.
"""

def well_documented_function():
    """This is a well-documented function.
    
    It has proper indentation and formatting
    that should be preserved when adding usage info.
    
    Args:
        None
        
    Returns:
        A greeting string

    Used in:
    - /Users/adam/Developer/vcs/github.twardoch/pub/uzpy/test_indent.py
"""
    return "Hello from well documented function!"

class WellDocumentedClass:
    """This is a well-documented class.
    
    It demonstrates proper docstring formatting
    with multiple lines and proper indentation.

    Used in:
    - /Users/adam/Developer/vcs/github.twardoch/pub/uzpy/test_indent.py
"""
    
    def method_with_docs(self):
        """Method with proper documentation.
        
        This method shows how indentation should
        be preserved in method docstrings.

        Used in:
        - /Users/adam/Developer/vcs/github.twardoch/pub/uzpy/test_indent.py
"""
        return self.well_documented_function()

# Use the functions to create references
if __name__ == "__main__":
    func_result = well_documented_function()
    instance = WellDocumentedClass()
    method_result = instance.method_with_docs()
    print(func_result, method_result)