# this_file: tests/test_safe_integration.py

"""
Integration test for the safe modifier - runs uzpy on its own source.

This test verifies that the safe modifier can process the entire uzpy
codebase without causing any syntax corruption.
"""

import ast
import shutil
import tempfile
from pathlib import Path

import pytest

# Import the safe modifier
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from uzpy.modifier.safe_modifier import SafeLibCSTModifier
from uzpy.parser import CachedParser, TreeSitterParser
from uzpy.analyzer import ModernHybridAnalyzer
from uzpy.types import Construct, ConstructType, Reference


class TestSafeIntegration:
    """Integration tests for the safe modifier."""
    
    @pytest.fixture
    def temp_uzpy_copy(self):
        """Create a temporary copy of the uzpy source."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Copy uzpy source
            src_path = Path(__file__).parent.parent / "src/uzpy"
            dest_path = temp_path / "uzpy"
            shutil.copytree(src_path, dest_path)
            
            yield dest_path
    
    def validate_all_files(self, directory: Path) -> list[tuple[Path, str]]:
        """
        Validate all Python files in a directory.
        
        Returns:
            List of (file_path, error_message) tuples for files with errors
        """
        errors = []
        
        for py_file in directory.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
                
            try:
                code = py_file.read_text()
                ast.parse(code)
            except SyntaxError as e:
                errors.append((py_file, str(e)))
            except Exception as e:
                errors.append((py_file, f"Read error: {e}"))
        
        return errors
    
    @pytest.mark.slow
    @pytest.mark.integration
    def test_safe_modifier_on_uzpy_source(self, temp_uzpy_copy):
        """Test that the safe modifier can process uzpy source without corruption."""
        # Validate source before modification
        errors_before = self.validate_all_files(temp_uzpy_copy)
        assert not errors_before, f"Source has errors before modification: {errors_before}"
        
        # Set up components
        project_root = temp_uzpy_copy.parent
        parser = TreeSitterParser()
        analyzer = ModernHybridAnalyzer()
        modifier = SafeLibCSTModifier(project_root)
        
        # Parse all Python files
        all_constructs = []
        py_files = list(temp_uzpy_copy.rglob("*.py"))
        
        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue
            try:
                constructs = parser.parse_file(py_file)
                all_constructs.extend(constructs)
            except Exception as e:
                pytest.fail(f"Failed to parse {py_file}: {e}")
        
        # Find usages (simplified - just create some mock references)
        usage_map = {}
        for construct in all_constructs:
            # Mock: each construct is used in at least one other file
            refs = []
            for other_file in py_files[:3]:  # Just use first 3 files as references
                if other_file != construct.file_path:
                    refs.append(Reference(
                        name=construct.name,
                        file_path=other_file,
                        line=10
                    ))
            if refs:
                usage_map[construct] = refs
        
        # Modify files with safe modifier
        modified_count = 0
        for py_file in py_files:
            if "__pycache__" in str(py_file):
                continue
                
            # Filter usage map for this file
            file_usage_map = {
                c: refs for c, refs in usage_map.items()
                if c.file_path == py_file
            }
            
            if file_usage_map:
                success = modifier.modify_file(
                    py_file, 
                    file_usage_map,
                    dry_run=False,
                    backup=True
                )
                if success:
                    modified_count += 1
        
        # Validate all files after modification
        errors_after = self.validate_all_files(temp_uzpy_copy)
        
        # Report results
        if errors_after:
            error_report = "\n".join(
                f"{file}: {error}" for file, error in errors_after
            )
            pytest.fail(
                f"Syntax errors after modification:\n{error_report}\n"
                f"Modified {modified_count} files"
            )
        
        assert modified_count > 0, "Should have modified at least some files"
        print(f"Successfully modified {modified_count} files without corruption")
    
    def test_safe_modifier_edge_cases(self):
        """Test the safe modifier with specific edge cases."""
        modifier = SafeLibCSTModifier(Path.cwd())
        
        # Test case: docstring with triple quotes
        test_code = '''
def example():
    """This has """ + """nested quotes."""
    pass
'''
        
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.py', delete=False
        ) as tmp:
            tmp.write(test_code)
            tmp_path = Path(tmp.name)
        
        try:
            # Create mock usage
            construct = Construct(
                name="example",
                type=ConstructType.FUNCTION,
                file_path=tmp_path,
                line=2
            )
            usage_map = {
                construct: [
                    Reference("example", Path("other.py"), 10)
                ]
            }
            
            # Modify with safe modifier
            success = modifier.modify_file(
                tmp_path,
                usage_map,
                dry_run=False,
                backup=True
            )
            
            assert success, "Safe modifier should handle edge cases"
            
            # Verify syntax is valid
            modified_code = tmp_path.read_text()
            try:
                ast.parse(modified_code)
            except SyntaxError:
                pytest.fail(f"Modified code has syntax error:\n{modified_code}")
                
        finally:
            # Cleanup
            tmp_path.unlink(missing_ok=True)
            backup_path = tmp_path.with_suffix('.py.bak')
            backup_path.unlink(missing_ok=True)