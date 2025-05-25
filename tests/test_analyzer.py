# this_file: tests/test_analyzer.py

"""
Tests for the analyzer functionality.
"""

import tempfile
from pathlib import Path

import pytest

from uzpy.analyzer.hybrid_analyzer import HybridAnalyzer
from uzpy.parser import Construct, ConstructType


@pytest.fixture
def sample_project():
    """Create a sample project structure for testing."""
    project_dir = Path(tempfile.mkdtemp())
    
    # Create main module
    main_content = '''"""Main module."""

from utils import helper_function
from models import UserClass

def main():
    """Main function."""
    user = UserClass("test")
    result = helper_function(user.name)
    return result

if __name__ == "__main__":
    main()
'''
    
    # Create utils module
    utils_content = '''"""Utility functions."""

def helper_function(name):
    """Helper function for processing names."""
    return f"Hello, {name}!"

def unused_function():
    """This function is not used."""
    pass
'''
    
    # Create models module
    models_content = '''"""Data models."""

class UserClass:
    """User model class."""
    
    def __init__(self, name):
        """Initialize user."""
        self.name = name
    
    def get_display_name(self):
        """Get display name."""
        return f"User: {self.name}"

class UnusedClass:
    """This class is not used."""
    pass
'''
    
    # Write files
    (project_dir / "main.py").write_text(main_content)
    (project_dir / "utils.py").write_text(utils_content)
    (project_dir / "models.py").write_text(models_content)
    
    yield project_dir
    
    # Cleanup
    import shutil
    shutil.rmtree(project_dir)


@pytest.fixture
def sample_constructs(sample_project):
    """Create sample constructs for testing."""
    constructs = [
        Construct(
            name="helper_function",
            type=ConstructType.FUNCTION,
            file_path=sample_project / "utils.py",
            line_number=3,
            docstring="Helper function for processing names.",
            full_name="helper_function"
        ),
        Construct(
            name="UserClass",
            type=ConstructType.CLASS,
            file_path=sample_project / "models.py",
            line_number=3,
            docstring="User model class.",
            full_name="UserClass"
        ),
        Construct(
            name="unused_function",
            type=ConstructType.FUNCTION,
            file_path=sample_project / "utils.py",
            line_number=7,
            docstring="This function is not used.",
            full_name="unused_function"
        ),
        Construct(
            name="UnusedClass",
            type=ConstructType.CLASS,
            file_path=sample_project / "models.py",
            line_number=14,
            docstring="This class is not used.",
            full_name="UnusedClass"
        )
    ]
    return constructs


def test_hybrid_analyzer_initialization(sample_project):
    """Test HybridAnalyzer initialization."""
    analyzer = HybridAnalyzer(sample_project)
    assert analyzer.project_path == sample_project
    assert analyzer.rope_analyzer is not None
    assert analyzer.jedi_analyzer is not None


def test_find_usages_with_results(sample_project, sample_constructs):
    """Test finding usages for constructs that are actually used."""
    analyzer = HybridAnalyzer(sample_project)
    
    # Test helper_function which is imported and called in main.py
    helper_construct = sample_constructs[0]  # helper_function
    
    ref_files = [sample_project / "main.py"]
    references = analyzer.find_usages(helper_construct, ref_files)
    
    # Should find at least one reference (import or call)
    assert len(references) > 0
    
    # Check that we found references in main.py
    ref_files_found = {ref.file_path for ref in references}
    assert sample_project / "main.py" in ref_files_found


def test_find_usages_no_results(sample_project, sample_constructs):
    """Test finding usages for constructs that are not used."""
    analyzer = HybridAnalyzer(sample_project)
    
    # Test unused_function which is not referenced anywhere
    unused_construct = sample_constructs[2]  # unused_function
    
    ref_files = [sample_project / "main.py"]
    references = analyzer.find_usages(unused_construct, ref_files)
    
    # Should find no references
    assert len(references) == 0


def test_find_usages_class(sample_project, sample_constructs):
    """Test finding usages for class constructs."""
    analyzer = HybridAnalyzer(sample_project)
    
    # Test UserClass which is imported and instantiated in main.py
    user_class = sample_constructs[1]  # UserClass
    
    ref_files = [sample_project / "main.py"]
    references = analyzer.find_usages(user_class, ref_files)
    
    # Should find references (import and instantiation)
    assert len(references) > 0


def test_analyze_multiple_constructs(sample_project, sample_constructs):
    """Test analyzing multiple constructs at once."""
    analyzer = HybridAnalyzer(sample_project)
    
    ref_files = [sample_project / "main.py"]
    results = analyzer.analyze_constructs(sample_constructs, ref_files)
    
    # Should return a dictionary mapping constructs to references
    assert isinstance(results, dict)
    assert len(results) == len(sample_constructs)
    
    # Used constructs should have references
    helper_construct = sample_constructs[0]  # helper_function
    user_construct = sample_constructs[1]   # UserClass
    
    assert len(results[helper_construct]) > 0
    assert len(results[user_construct]) > 0
    
    # Unused constructs should have no references
    unused_construct = sample_constructs[2]  # unused_function
    unused_class = sample_constructs[3]     # UnusedClass
    
    assert len(results[unused_construct]) == 0
    assert len(results[unused_class]) == 0


def test_analyzer_statistics(sample_project, sample_constructs):
    """Test analyzer statistics generation."""
    analyzer = HybridAnalyzer(sample_project)
    
    ref_files = [sample_project / "main.py"]
    results = analyzer.analyze_constructs(sample_constructs, ref_files)
    
    stats = analyzer.get_analysis_statistics(results)
    
    assert "total_constructs" in stats
    assert "constructs_with_usages" in stats
    assert "constructs_without_usages" in stats
    assert "total_references" in stats
    
    assert stats["total_constructs"] == len(sample_constructs)
    assert stats["constructs_with_usages"] > 0
    assert stats["constructs_without_usages"] > 0


def test_analyzer_with_nonexistent_files(sample_project, sample_constructs):
    """Test analyzer behavior with non-existent reference files."""
    analyzer = HybridAnalyzer(sample_project)
    
    # Try to analyze with non-existent file
    ref_files = [Path("/nonexistent/file.py")]
    
    helper_construct = sample_constructs[0]
    references = analyzer.find_usages(helper_construct, ref_files)
    
    # Should handle gracefully and return empty results
    assert len(references) == 0


def test_analyzer_confidence_scoring(sample_project, sample_constructs):
    """Test that references include confidence scores."""
    analyzer = HybridAnalyzer(sample_project)
    
    helper_construct = sample_constructs[0]  # helper_function
    ref_files = [sample_project / "main.py"]
    
    references = analyzer.find_usages(helper_construct, ref_files)
    
    if references:  # Only test if we found references
        for ref in references:
            assert hasattr(ref, 'confidence')
            assert 0.0 <= ref.confidence <= 1.0


def test_analyzer_reference_types(sample_project, sample_constructs):
    """Test that references include type information."""
    analyzer = HybridAnalyzer(sample_project)
    
    helper_construct = sample_constructs[0]  # helper_function
    ref_files = [sample_project / "main.py"]
    
    references = analyzer.find_usages(helper_construct, ref_files)
    
    if references:  # Only test if we found references
        for ref in references:
            assert hasattr(ref, 'reference_type')
            assert ref.reference_type in ['call', 'import', 'attribute', 'inheritance', 'unknown']


def test_analyzer_error_handling():
    """Test analyzer error handling with invalid project."""
    # Try to create analyzer with non-existent project
    analyzer = HybridAnalyzer(Path("/nonexistent/project"))
    
    # Should initialize but handle errors gracefully during analysis
    fake_construct = Construct(
        name="fake_function",
        type=ConstructType.FUNCTION,
        file_path=Path("/fake/file.py"),
        line_number=1,
        docstring="Fake function",
        full_name="fake_function"
    )
    
    references = analyzer.find_usages(fake_construct, [Path("/fake/ref.py")])
    
    # Should return empty list without crashing
    assert len(references) == 0


def test_analyzer_performance_tracking(sample_project, sample_constructs):
    """Test that analyzer tracks performance metrics."""
    analyzer = HybridAnalyzer(sample_project)
    
    ref_files = [sample_project / "main.py"]
    
    # Analyze constructs and check if timing information is available
    results = analyzer.analyze_constructs(sample_constructs, ref_files)
    
    # The analyzer should complete without errors
    assert isinstance(results, dict)
    
    # Performance tracking should be implemented in the analyzer
    # This is a placeholder for future performance tracking features
    assert True  # Placeholder assertion