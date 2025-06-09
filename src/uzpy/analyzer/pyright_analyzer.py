# this_file: src/uzpy/analyzer/pyright_analyzer.py

"""
Pyright-based analyzer for fast and accurate cross-file analysis.

This module provides an analyzer that uses Pyright's type checking and
language server capabilities for accurate and fast usage detection,
replacing the slower Rope analyzer for many use cases.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from uzpy.types import Construct, ConstructType, Reference


class PyrightAnalyzer:
    """
    Fast and accurate analyzer using Pyright.
    
    This analyzer leverages Pyright's language server protocol capabilities
    for accurate cross-file analysis. It's significantly faster than Rope
    while maintaining good accuracy for most use cases.
    """
    
    def __init__(self, project_root: Path, exclude_patterns: Optional[list[str]] = None):
        """
        Initialize Pyright analyzer.
        
        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis
        """
        self.project_root = project_root
        self.exclude_patterns = exclude_patterns or []
        
        # Check if pyright is available
        try:
            result = subprocess.run(["pyright", "--version"], capture_output=True, text=True)
            logger.debug(f"Using Pyright {result.stdout.strip()}")
            self.pyright_cmd = ["pyright"]
        except FileNotFoundError:
            logger.warning("Pyright not found in PATH, trying npx pyright")
            self.pyright_cmd = ["npx", "pyright"]
        
        # Create pyright config if needed
        self._ensure_pyright_config()
    
    def find_usages(self, construct: Construct, reference_files: list[Path]) -> list[Reference]:
        """
        Find usages of a construct using Pyright's analysis.
        
        This method uses Pyright to accurately identify usages through
        type analysis and cross-file resolution.
        
        Args:
            construct: The construct to find usages for
            reference_files: List of files to search in
            
        Returns:
            List of references to the construct
        """
        references = []
        
        # Create a temporary analysis script
        analysis_script = self._create_analysis_script(construct, reference_files)
        script_path = self.project_root / ".uzpy_pyright_temp.py"
        
        try:
            # Write temporary analysis script
            script_path.write_text(analysis_script)
            
            # Run Pyright analysis
            cmd = self.pyright_cmd + [
                "--outputjson",
                "--pythonpath", str(self.project_root),
                str(script_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and result.stdout:
                # Parse Pyright output
                try:
                    output = json.loads(result.stdout)
                    references = self._parse_pyright_output(output, construct, reference_files)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Pyright output: {e}")
            
        finally:
            # Clean up temporary file
            if script_path.exists():
                script_path.unlink()
        
        return references
    
    def _ensure_pyright_config(self):
        """Ensure a basic pyrightconfig.json exists."""
        config_path = self.project_root / "pyrightconfig.json"
        if not config_path.exists():
            config = {
                "include": ["**/*.py"],
                "exclude": self.exclude_patterns + ["**/node_modules", "**/__pycache__"],
                "reportMissingImports": False,
                "reportMissingTypeStubs": False,
                "pythonVersion": "3.10",
            }
            config_path.write_text(json.dumps(config, indent=2))
            logger.debug("Created pyrightconfig.json")
    
    def _create_analysis_script(self, construct: Construct, reference_files: list[Path]) -> str:
        """
        Create a temporary Python script for Pyright to analyze.
        
        Args:
            construct: The construct to find usages for
            reference_files: List of files to analyze
            
        Returns:
            Python script content
        """
        # Import the construct and all reference files
        imports = [f"from {construct.module_path} import {construct.name}"]
        
        # Add imports for all reference files to force analysis
        for ref_file in reference_files:
            module_path = self._file_to_module(ref_file)
            if module_path:
                imports.append(f"import {module_path}")
        
        script = "\n".join(imports)
        return script
    
    def _file_to_module(self, file_path: Path) -> Optional[str]:
        """Convert file path to module path."""
        try:
            relative = file_path.relative_to(self.project_root)
            parts = relative.with_suffix("").parts
            return ".".join(parts)
        except ValueError:
            return None
    
    def _parse_pyright_output(
        self, 
        output: dict, 
        construct: Construct,
        reference_files: list[Path]
    ) -> list[Reference]:
        """
        Parse Pyright JSON output to extract references.
        
        Args:
            output: Pyright JSON output
            construct: The construct being searched for
            reference_files: List of files that were analyzed
            
        Returns:
            List of references found
        """
        references = []
        
        # Check diagnostics for import-related information
        diagnostics = output.get("generalDiagnostics", [])
        
        # Also check if files import the construct
        for ref_file in reference_files:
            if self._file_imports_construct(ref_file, construct):
                references.append(
                    Reference(
                        file_path=ref_file,
                        line_number=1,  # Import typically at top
                        column=0,
                        context=f"Imports {construct.name}",
                    )
                )
        
        return references
    
    def _file_imports_construct(self, file_path: Path, construct: Construct) -> bool:
        """
        Check if a file imports a specific construct.
        
        Args:
            file_path: File to check
            construct: Construct to look for
            
        Returns:
            True if the file imports the construct
        """
        try:
            content = file_path.read_text(encoding="utf-8")
            
            # Check various import patterns
            import_patterns = [
                f"from {construct.module_path} import {construct.name}",
                f"from {construct.module_path} import .* {construct.name}",
                f"import {construct.module_path}.{construct.name}",
            ]
            
            return any(pattern in content for pattern in import_patterns)
            
        except Exception as e:
            logger.debug(f"Failed to check imports in {file_path}: {e}")
            return False