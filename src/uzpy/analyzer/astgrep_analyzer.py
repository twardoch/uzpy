# this_file: src/uzpy/analyzer/astgrep_analyzer.py

"""
ast-grep based analyzer for uzpy.

This module provides an AstGrepAnalyzer class that uses the ast-grep tool
(via its Python bindings `ast-grep-py`) to find Python constructs based on
structural patterns. This allows for more flexible and precise pattern matching
than simple text searches.
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
    An analyzer that uses ast-grep for structural code searching.
    It matches code patterns to find usages of constructs.
    """

    def __init__(self, project_root: Path):
        """
        Initialize the AstGrepAnalyzer.

        Args:
            project_root: The root directory of the project. Used for resolving relative paths.
        """
        self.project_root = project_root
        if SgRoot is None:
            logger.error("ast-grep Python bindings (SgRoot) not available. AstGrepAnalyzer will be non-functional.")
        logger.info(f"AstGrepAnalyzer initialized for project root: {self.project_root}")

    def _get_ast_grep_patterns(self, construct: Construct) -> list[dict[str, str]]:
        """
        Generate ast-grep patterns for a given construct.
        See ast-grep pattern syntax: https://ast-grep.github.io/guide/pattern-syntax.html
        """
        name = construct.name
        patterns = []

        # General call pattern (works for functions and methods if object is not specified)
        patterns.append({"rule": {"pattern": f"{name}($$$)"}, "description": "Direct call"})

        # Attribute access / method call (e.g., object.method_name)
        # $OBJ.{name}($$$) where $OBJ is a metavariable matching any identifier/expression.
        patterns.append({"rule": {"pattern": "$_.$name($$$)"}, "description": "Method call on object"})
        patterns.append({"rule": {"pattern": "$_.$name"}, "description": "Attribute access"})

        if construct.type == ConstructType.CLASS:
            # Class instantiation
            patterns.append({"rule": {"pattern": f"{name}($$$)"}, "description": "Class instantiation"})
            # Type hints
            patterns.append({"rule": {"pattern": f"$_: {name}"}, "description": "Type hint (variable)"})
            patterns.append({"rule": {"pattern": f"$_: Optional[{name}]"}, "description": "Type hint (Optional)"})
            patterns.append({"rule": {"pattern": f"$_: Union[{name}, $$$]"}, "description": "Type hint (Union, first)"})
            patterns.append({"rule": {"pattern": f"$_: Union[$$$, {name}]"}, "description": "Type hint (Union, other)"})
            patterns.append({"rule": {"pattern": f"-> {name}"}, "description": "Return type hint"})

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
            A list of Reference objects.
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

            try:
                file_content = file_path.read_text(encoding="utf-8")
                sg_root = SgRoot(file_content, TreeSitterLang.Python)  # Use Python language

                for item in patterns_with_desc:
                    pattern_config = SGConfig(rule=item["rule"])
                    description = item["description"]

                    for node_match in sg_root.find_all(pattern_config):
                        # node_match is an SgNode object
                        line_number = node_match.range().start.line + 1  # ast-grep is 0-indexed
                        column_number = node_match.range().start.col  # ast-grep is 0-indexed

                        # Extract context (e.g., the matched line)
                        # SgNode.text() gives the matched text. For context, we might need the line.
                        start_line_idx = node_match.range().start.line
                        end_line_idx = node_match.range().end.line

                        lines = file_content.splitlines()
                        context_lines = lines[start_line_idx : end_line_idx + 1]
                        context = " | ".join(l.strip() for l in context_lines)

                        logger.debug(
                            f"Found match for '{construct.name}' ({description}) in {file_path}:{line_number} "
                            f"Context: {context[:100]}"
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

    def __del__(self) -> None:
        logger.debug("AstGrepAnalyzer instance being deleted.")

    def close(self) -> None:
        logger.debug("AstGrepAnalyzer closed (no specific resources to release).")
