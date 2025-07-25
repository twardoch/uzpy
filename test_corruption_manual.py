#!/usr/bin/env python3
# this_file: test_corruption_manual.py

"""
Manual test script to reproduce and understand the corruption issue.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from uzpy.modifier.libcst_modifier import LibCSTModifier
from uzpy.parser import Construct, ConstructType, Reference


def test_corruption_scenario():
    """Test a specific corruption scenario."""
    
    # Test code with triple quotes in docstring
    test_code = 'def example():\n    """This docstring contains """ + """more text."""\n    pass\n'
    
    print("Original code:")
    print(test_code)
    print("-" * 40)
    
    # Create modifier
    modifier = LibCSTModifier(project_root=Path.cwd())
    
    # Create usage map
    construct = Construct(
        name="example",
        type=ConstructType.FUNCTION,
        file_path=Path("test.py"),
        line=1
    )
    reference = Reference(
        name="example",
        file_path=Path("other.py"),
        line=10
    )
    usage_map = {construct: [reference]}
    
    try:
        # Modify the code
        result = modifier.modify_string(test_code, Path("test.py"), usage_map)
        
        print("Modified code:")
        print(result)
        print("-" * 40)
        
        # Check syntax
        import ast
        try:
            ast.parse(result)
            print("✓ Valid Python syntax")
        except SyntaxError as e:
            print(f"✗ SYNTAX ERROR: {e}")
            print(f"  Line {e.lineno}: {e.text}")
            
    except Exception as e:
        print(f"ERROR during modification: {e}")
        import traceback
        traceback.print_exc()


def test_nested_quotes():
    """Test various nested quote scenarios."""
    
    test_cases = [
        # Single quotes in triple quotes
        '''def f1():
    """Has 'single' quotes."""
    pass''',
        
        # Double quotes in triple quotes
        '''def f2():
    """Has "double" quotes."""
    pass''',
        
        # Triple quotes in docstring (problematic!)
        'def f3():\n    """Has """ + """triple quotes."""\n    pass',
        
        # Escaped quotes
        r'''def f4():
    """Has \"escaped\" quotes."""
    pass''',
        
        # Mixed quotes
        '''def f5():
    """Has 'single' and "double" quotes."""
    pass''',
    ]
    
    modifier = LibCSTModifier(project_root=Path.cwd())
    
    for i, code in enumerate(test_cases):
        print(f"\nTest case {i+1}:")
        print("Original:", repr(code))
        
        construct = Construct(
            name=f"f{i+1}",
            type=ConstructType.FUNCTION,
            file_path=Path("test.py"),
            line=1
        )
        reference = Reference(
            name=f"f{i+1}",
            file_path=Path("other.py"),
            line=10
        )
        usage_map = {construct: [reference]}
        
        try:
            result = modifier.modify_string(code, Path("test.py"), usage_map)
            
            # Check syntax
            import ast
            try:
                ast.parse(result)
                print("✓ Valid syntax after modification")
            except SyntaxError as e:
                print(f"✗ SYNTAX ERROR: {e}")
                print("Modified code:", repr(result))
                
        except Exception as e:
            print(f"✗ ERROR: {e}")


if __name__ == "__main__":
    print("Testing corruption scenarios...")
    test_corruption_scenario()
    print("\n" + "="*60 + "\n")
    test_nested_quotes()