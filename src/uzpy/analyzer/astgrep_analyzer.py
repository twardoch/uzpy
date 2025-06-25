# this_file: src/uzpy/analyzer/astgrep_analyzer.py

"""
ast-grep based analyzer for uzpy.

This module provides an analyzer that uses ast-grep for intuitive and fast
structural pattern matching across Python codebases.

"""

from pathlib import Path
from loguru import logger  # Moved logger import to the top

from sgql import SGConfig

# In older versions, it might be: from ast_grep_py import SgRoot
# Checking common import paths for ast-grep's Python API
try:
    from ast_grep_py import SgRoot, TreeSitterLang  # Modern ast-grep-py
except ImportError:
    try:
        from ast_grep_py.langs import TreeSitterLang
        from ast_grep_py.sg_root import SgRoot  # Older layout
    except ImportError:
        SgRoot = None  # Fallback if import fails
        TreeSitterLang = None
        logger.warning("Failed to import SgRoot from ast_grep_py. AstGrepAnalyzer may not function.")


from uzpy.types import Construct, ConstructType, Reference


class AstGrepAnalyzer:
    """
    Structural pattern matching analyzer using ast-grep.

    This analyzer leverages ast-grep's powerful pattern matching capabilities
    to find complex usage patterns that other analyzers might miss.

    Used in:
    - src/uzpy/analyzer/__init__.py
    - src/uzpy/analyzer/modern_hybrid_analyzer.py
    """

    def __init__(self, project_root: Path):
        """
        Initialize the AstGrepAnalyzer.

        Args:
            project_root: Root directory of the project
            exclude_patterns: Patterns to exclude from analysis

        """
        self.project_root = project_root
        if SgRoot is None:
            logger.error("ast-grep Python bindings (SgRoot) not available. AstGrepAnalyzer will be non-functional.")
        logger.info(f"AstGrepAnalyzer initialized for project root: {self.project_root}")

        Returns:
            List of references to the construct

        Used in:
        - src/uzpy/analyzer/modern_hybrid_analyzer.py
        """
        Generate ast-grep patterns for a given construct.
        See ast-grep pattern syntax: https://ast-grep.github.io/guide/pattern-syntax.html
        """
        name = construct.name
        patterns = []

        # General call pattern (works for functions and methods if object is not specified)
        patterns.append({"rule": {"pattern": f"{name}($$$)"}, "description": "Direct call"})

        Returns:
            List of ast-grep pattern strings

        """
        patterns = []
        name = construct.name

        # Import patterns
        # from module import name
        patterns.append({"rule": {"pattern": f"from $_ import {name}"}, "description": "Direct import"})
        patterns.append(
            {"rule": {"pattern": f"from $_ import $MODULE as {name}"}, "description": "Direct import with alias"}
        )
        # from module import name as alias (if construct.name is the original name)
        patterns.append(
            {
                "rule": {"pattern": f"from $_ import {name} as $_"},
                "description": "Direct import with alias for construct",
            }
        )

        # from module.submodule import name
        patterns.append(
            {"rule": {"pattern": f"from $_.$_ import {name}"}, "description": "Direct import from submodule"}
        )

        # import module (if construct is a module, this requires matching module name)
        if construct.type == ConstructType.MODULE:
            # ast-grep might need specific patterns for module imports if 'name' is 'module.submodule'
            # For a simple module name:
            patterns.append({"rule": {"pattern": f"import {name}"}, "description": "Module import"})
            patterns.append({"rule": {"pattern": f"import {name} as $_"}, "description": "Module import with alias"})

        return patterns

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Uses ast-grep to find structural usages of the construct.

        Args:
            construct: The construct to find usages for.
            search_paths: List of Python files to search within.

        Returns:
            List of references found

        """
        if SgRoot is None or TreeSitterLang is None:
            logger.error("AstGrepAnalyzer cannot function because SgRoot or TreeSitterLang is not imported.")
            return []

        logger.debug(f"AstGrepAnalyzer looking for usages of {construct.full_name} in {len(search_paths)} paths.")
        references: list[Reference] = []

        patterns_with_desc = self._get_ast_grep_patterns(construct)

        for file_path in search_paths:
            if not file_path.is_file() or not file_path.exists():
                logger.warning(f"Skipping non-existent or non-file path: {file_path}")
                continue

        Returns:
            List of references

        """
        references = []

        try:
            # ast-grep outputs one JSON object per line
            for line in output.strip().split("\n"):
                if not line:
                    continue

                match = json.loads(line)

                # Extract file path and location
                file_path = Path(match.get("file", ""))

                # Get match location
                range_info = match.get("range", {})
                start = range_info.get("start", {})
                line = start.get("line", 0) + 1  # ast-grep uses 0-based lines
                column = start.get("column", 0)

                # Get matched text as context
                text = match.get("text", "")

                if file_path and line > 0:
                    references.append(
                        Reference(
                            file_path=file_path,
                            line_number=line,
                            column=column,
                            context=text[:100],  # Limit context length
                        )
                        references.append(
                            Reference(
                                file_path=file_path,
                                line_number=line_number,
                                column_number=column_number,
                                context=context,
                            )
                        )
            except Exception as e:
                logger.error(f"Error processing file {file_path} with ast-grep for construct {construct.name}: {e}")

        logger.debug(f"AstGrepAnalyzer found {len(references)} references for {construct.full_name}.")
        return references

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs.
        For ast-grep, this will call find_usages for each construct.
        Batching source file parsing could be an optimization if ast-grep supports it directly.
        """
        results = {}
        if SgRoot is None:  # Guard if ast-grep is not available
            for construct in constructs:
                results[construct] = []
            return results

        for construct in constructs:
            results[construct] = self.find_usages(construct, search_paths)
        return results

        Returns:
            List of file batches

        """
        return [files[i : i + batch_size] for i in range(0, len(files), batch_size)]
