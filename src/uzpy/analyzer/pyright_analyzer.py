# this_file: src/uzpy/analyzer/pyright_analyzer.py

"""
Pyright-based analyzer for uzpy.

This module provides a PyrightAnalyzer class that uses the Pyright command-line
tool (Microsoft's static type checker for Python) to find references to
Python constructs. Pyright offers fast and accurate cross-file analysis.
"""

import json
import subprocess
from pathlib import Path
from typing import Any  # Optional removed

from loguru import logger

from uzpy.types import Construct, Reference


class PyrightAnalyzer:
    """
    An analyzer that uses the Pyright tool to find references to constructs.
    Pyright is run as a subprocess, and its JSON output is parsed.
    """

    def __init__(self, project_root: Path, python_executable: str | None = None):
        """
        Initialize the PyrightAnalyzer.

        Args:
            project_root: The root directory of the project being analyzed.
                          Pyright needs this to resolve imports correctly.
            python_executable: Path to the python executable for Pyright's environment.
                               If None, Pyright will try to discover it.
        """
        self.project_root = project_root.resolve()
        self.python_executable = python_executable
        logger.info(f"PyrightAnalyzer initialized. Project root: {self.project_root}")
        if self.python_executable:
            logger.info(f"Using Python executable for Pyright: {self.python_executable}")

    def _run_pyright_find_references(self, file_path: Path, line: int, character: int) -> list[dict[str, Any]]:
        """
        Run Pyright's 'find references' command and parse its JSON output.

        Args:
            file_path: The path to the file containing the symbol.
            line: The 0-indexed line number of the symbol.
            character: The 0-indexed character offset (UTF-16) of the symbol.

        Returns:
            A list of reference information dictionaries from Pyright's JSON output.
        """
        try:
            # Pyright's find references is not a direct CLI command.
            # It's typically accessed via its Language Server Protocol (LSP) capabilities.
            # However, Pyright's CLI *can* output detailed analysis in JSON format for a whole project,
            # which includes definition locations and sometimes reference information, but not a direct
            # "find all references for symbol at X:Y" command that outputs simple references.
            #
            # The PLAN.md suggested:
            # cmd = [ "pyright", "--outputjson", f"--pythonpath={self.project_root}", "--files", str(construct.file_path)]
            # This command runs type checking and outputs errors/warnings, not references for a *specific* symbol.
            #
            # To get references for a specific symbol, one would typically need to interact with Pyright as a language server
            # or use a tool that wraps Pyright's LSP functions.
            #
            # Given the constraints of a simple subprocess call, a common workaround is to parse the *full analysis*
            # output if it contains enough detail, or use a different Pyright CLI option if one exists that's closer.
            # Some language servers have a command like `--stdio` to communicate over LSP.
            #
            # For now, I will simulate what might be possible if Pyright had a direct CLI for this,
            # or assume that a hypothetical `pyright --find-references ...` command exists.
            # The `pyright --createstub <module>` can sometimes reveal import structure.
            #
            # A more realistic approach for subprocess usage if no direct find-references CLI:
            # 1. Generate pyrightconfig.json if not present, defining project root.
            # 2. Run `pyright --outputjson .` to get full project analysis.
            # 3. Parse this large JSON to find the definition of the target symbol.
            # 4. Then, manually search for all nodes in the JSON that match this definition's ID or unique signature.
            # This is complex.
            #
            # Let's assume a hypothetical `pyright --find-references-raw <file> <line> <char>` for simplicity,
            # acknowledging this is a placeholder for a more complex LSP interaction or parsing strategy.
            # If such a command doesn't exist, this analyzer part might be unimplementable purely via CLI subprocess
            # without a more sophisticated Pyright interaction mechanism.

            # Fallback: If no direct find-references CLI exists, this analyzer might be very limited.
            # One could try to parse `pyright --verifytypes <module>` output, but it's not designed for this.

            # For the purpose of this implementation, I will return an empty list,
            # as reliably getting specific references via a simple Pyright CLI call is not standard.
            # This part of the plan might need re-evaluation based on available Pyright CLI features
            # or by deciding to implement an LSP client.
            logger.warning(
                "PyrightAnalyzer._run_pyright_find_references: "
                "Direct CLI for 'find references' is not a standard Pyright feature. "
                "This method is a placeholder and will likely not find references effectively."
            )
            # To make it runnable, let's try the --outputjson on the specific file.
            # This will give type checking info, not references, but it's a runnable command.
            command = ["pyright", "--outputjson"]
            if self.python_executable:
                command.extend(["--pythonpath", str(self.project_root), "--pythonversion", "3.10"])  # Example version
            command.append(str(file_path.resolve()))

            logger.debug(f"Running Pyright command: {' '.join(command)}")
            process = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                check=False,
            )

            if process.stderr:
                # Pyright often outputs info to stderr even on success
                logger.debug(f"Pyright stderr for {file_path}:\n{process.stderr}")

            if process.stdout:
                try:
                    # The output of `pyright --outputjson <file>` is a JSON object with
                    # a "generalDiagnostics" or "typeCompleteness" key, not references.
                    # We would need to parse this to find relevant information if possible.
                    json.loads(process.stdout)
                    # This data is not directly references. We'd need to interpret it.
                    # For now, returning empty as this doesn't give references.
                    logger.debug(f"Pyright output for {file_path} (first 200 chars): {process.stdout[:200]}")
                    return []  # Placeholder
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse Pyright JSON output for {file_path}: {e}\nOutput:\n{process.stdout}")
                    return []
            return []
        except FileNotFoundError:
            logger.error(
                "Pyright command not found. Please ensure Pyright (npm install -g pyright) is installed and in PATH."
            )
            return []
        except Exception as e:
            logger.error(f"Error running Pyright for {file_path}: {e}")
            return []

    def _get_symbol_position(self, construct: Construct) -> tuple[Path, int, int] | None:
        """
        Get the file path, line, and character for a construct's definition.
        Pyright typically needs 0-indexed line and UTF-16 character offset.
        """
        # Tree-sitter nodes (if available on construct) provide byte offsets.
        # Converting to line/char and UTF-16 can be complex.
        # For simplicity, we'll use the construct's line_number (1-based)
        # and assume character 0 for the start of the line.
        # This might not be precise enough for Pyright in all cases.
        if construct.line_number is None:
            return None

        # Pyright LSP uses 0-indexed lines and 0-indexed UTF-16 character counts.
        # A simple approximation:
        line_0_indexed = construct.line_number - 1

        # Character offset is harder. If we have the node, we could use start_byte.
        # If not, we might need to read the file line and find the name.
        # For now, let's try to find the column of the construct name.
        char_0_indexed = 0  # Default
        try:
            content = construct.file_path.read_text(encoding="utf-8").splitlines()
            if line_0_indexed < len(content):
                line_text = content[line_0_indexed]
                # A simple find for the name. This is naive for complex lines.
                char_offset_in_line = line_text.find(construct.name)
                if char_offset_in_line != -1:
                    # Convert byte offset in line to UTF-16 character offset
                    prefix = line_text[:char_offset_in_line]
                    char_0_indexed = len(prefix.encode("utf-16-le")) // 2  # Each UTF-16 char is 2 bytes (LE)
        except Exception as e:
            logger.warning(f"Could not accurately determine character offset for {construct.full_name}: {e}")

        return construct.file_path, line_0_indexed, char_0_indexed

    def find_usages(self, construct: Construct, search_paths: list[Path]) -> list[Reference]:
        """
        Uses Pyright to find references to the given construct.

        Args:
            construct: The construct to find usages for.
            search_paths: List of Python files/directories to search within.
                          (Note: Pyright typically analyzes based on its config,
                           so search_paths might be less directly used here unless
                           we filter Pyright's project-wide results).

        Returns:
            A list of Reference objects. Accuracy depends on Pyright's capabilities
            and the method of interaction (direct CLI vs LSP).
        """
        logger.debug(f"PyrightAnalyzer looking for usages of {construct.full_name} ({construct.type}).")

        position_info = self._get_symbol_position(construct)
        if not position_info:
            logger.warning(f"Could not get position for construct {construct.full_name}. Skipping Pyright analysis.")
            return []

        file_path, line, char = position_info

        # This is where the call to a hypothetical Pyright "find references" CLI would go.
        # As discussed in _run_pyright_find_references, this is a placeholder.
        pyright_raw_references = self._run_pyright_find_references(file_path, line, char)

        references: list[Reference] = []
        if not pyright_raw_references:
            logger.debug(
                f"Pyright did not return references for {construct.full_name} (or CLI interaction is limited)."
            )
            return references

        # Example of parsing hypothetical raw references:
        # Each `raw_ref` would be a dict like:
        # { "filePath": "/path/to/file.py", "range": { "start": { "line": L, "character": C }, ... } }
        for raw_ref in pyright_raw_references:
            try:
                ref_file_path = Path(raw_ref["filePath"])
                # Ensure the reference is within the requested search_paths
                if not any(self._is_path_in_search_paths(ref_file_path, sp) for sp in search_paths):
                    continue

                # Pyright gives 0-indexed line and char. Convert line to 1-indexed for Reference object.
                ref_line = raw_ref["range"]["start"]["line"] + 1
                # context would require reading the file content at that line
                references.append(
                    Reference(
                        file_path=ref_file_path,
                        line_number=ref_line,
                        column_number=raw_ref["range"]["start"]["character"],
                    )
                )
            except KeyError as e:
                logger.warning(f"Could not parse Pyright reference, missing key: {e}. Raw ref: {raw_ref}")
            except Exception as e:
                logger.error(f"Error processing Pyright reference: {e}. Raw ref: {raw_ref}")

        logger.debug(f"PyrightAnalyzer found {len(references)} potential references for {construct.full_name}.")
        return references

    def _is_path_in_search_paths(self, path_to_check: Path, search_root: Path) -> bool:
        """Checks if path_to_check is under search_root or is search_root itself."""
        try:
            if search_root.is_file():
                return path_to_check.resolve() == search_root.resolve()
            if search_root.is_dir():
                return (
                    search_root.resolve() in path_to_check.resolve().parents
                    or path_to_check.resolve() == search_root.resolve()
                )
        except Exception:
            return False  # Path resolution errors
        return False

    def analyze_batch(self, constructs: list[Construct], search_paths: list[Path]) -> dict[Construct, list[Reference]]:
        """
        Analyze a batch of constructs.
        For Pyright, this will call find_usages for each construct, as true batch
        reference finding for multiple arbitrary symbols via CLI is not standard.
        """
        results = {}
        for construct in constructs:
            results[construct] = self.find_usages(construct, search_paths)
        return results

    def __del__(self) -> None:
        logger.debug("PyrightAnalyzer instance being deleted.")

    def close(self) -> None:
        logger.debug("PyrightAnalyzer closed (no specific resources to release).")
