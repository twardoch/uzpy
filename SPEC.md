# uzpy Technical Specification

**Version**: 0.1.0  
**Status**: Beta – Functional Implementation  
**Last Updated**: January 2025

## 1. Overview

uzpy is a Python static analysis tool that tracks cross-file usage of functions, classes, methods, and modules. It updates their docstrings with a "Used in:" section listing all known references. The tool uses Tree-sitter for parsing, Rope and Jedi for analysis, and LibCST for safe code modification.

## 2. Core Requirements

### 2.1. Functional Requirements

1. **Code Discovery** – Find Python files respecting `.gitignore` and custom exclusions.
2. **Construct Extraction** – Parse code to identify functions, classes, methods, and modules along with their docstrings.
3. **Usage Analysis** – Locate where each construct is used across the project using hybrid Rope+Jedi analysis.
4. **Docstring Modification** – Add or update "Used in:" sections in docstrings without altering formatting.
5. **Error Recovery** – Gracefully handle syntax errors, import issues, and analysis failures.

### 2.2. Non-Functional Requirements

1. **Safety** – Never lose data during modifications; preserve all existing formatting.
2. **Compatibility** – Works on Python 3.10+ projects.
3. **Reliability** – Continue operation even when individual components fail.
4. **Maintainability** – Modular structure with clear separation between discovery, parsing, analysis, and modification.

## 3. Architecture

### 3.1. High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   File Discovery │───▶│  Tree-sitter     │───▶│  Hybrid Analyzer│───▶│  LibCST Modifier│
│   (pathspec +    │    │  Parser          │    │  (Rope + Jedi)  │    │  (docstring     │
│   gitignore)     │    │  (AST extraction)│    │  (usage finding)│    │   updates)      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └─────────────────┘
```

### 3.2. Component Implementation

#### 3.2.1. CLI Interface (`cli.py`)
- **Technology**: Python Fire
- **Commands**:
  - `run` – Analyze and update docstrings.
  - `clean` – Remove all "Used in:" sections.
  - `test` – Dry-run mode.

#### 3.2.2. File Discovery (`discovery.py`)
- **Technology**: `pathlib` + `pathspec`
- Scans directories respecting `.gitignore` and additional exclusion patterns.
- Reports file statistics.

#### 3.2.3. Tree-sitter Parser (`parser/tree_sitter_parser.py`)
- **Technology**: tree-sitter + tree-sitter-python
- Fast AST parsing with error recovery.
- Identifies constructs and extracts current docstrings.
- Tracks fully qualified names and line numbers.

#### 3.2.4. Hybrid Analyzer (`analyzer/hybrid_analyzer.py`)
- **Technology**: Rope + Jedi
- **Components**:
  - `rope_analyzer.py` – Detailed cross-file analysis.
  - `jedi_analyzer.py` – Quick symbol resolution.
  - `hybrid_analyzer.py` – Strategy-based combination of both.
- Supports multiple fallback strategies based on project size and complexity.

#### 3.2.5. LibCST Modifier (`modifier/libcst_modifier.py`)
- **Technology**: LibCST
- Safely modifies docstrings while preserving all formatting.
- Manages creation and merging of "Used in:" sections.
- Uses relative paths from the project root.

## 4. Data Models

### 4.1. Core Data Structures

```python
@dataclass
class Construct:
    """Represents a Python construct with metadata."""
    name: str
    type: ConstructType  # function, class, method, module
    file_path: Path
    line_number: int     # 1-based
    docstring: str | None
    full_name: str
    node: Node | None

@dataclass  
class Reference:
    """A usage reference to a construct."""
    file_path: Path
    line_number: int
    column_number: int = 0
    context: str = ""
```

### 4.2. Pipeline Implementation

```python
def run_analysis_and_modification(
    edit_path: Path,
    ref_path: Path,
    exclude_patterns: list[str] | None,
    dry_run: bool,
) -> dict[Construct, list[Reference]]:
    # Phase 1: Discovery
    edit_files, ref_files = discover_files(edit_path, ref_path, exclude_patterns)
    
    # Phase 2: Parsing
    parser = TreeSitterParser()
    all_constructs = []
    for edit_file in edit_files:
        constructs = parser.parse_file(edit_file)
        all_constructs.extend(constructs)
    
    # Phase 3: Analysis
    analyzer = HybridAnalyzer(ref_path, exclude_patterns)
    usage_results = {}
    for construct in all_constructs:
        references = analyzer.find_usages(construct, ref_files)
        usage_results[construct] = references
    
    # Phase 4: Modification
    if not dry_run:
        modifier = LibCSTModifier(project_root)
        modifier.modify_files(usage_results)
    
    return usage_results
```

## 5. CLI Reference

### 5.1. Command Syntax

```bash
python -m uzpy [COMMAND] [OPTIONS]
```

### 5.2. Commands

| Command | Description |
|---------|-------------|
| `run` | Analyze and update docstrings (default). |
| `clean` | Remove all "Used in:" sections. |
| `test` | Run in dry-run mode. |

### 5.3. Constructor Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `edit` | str/Path | Path to analyze and modify | current directory |
| `ref` | str/Path | Reference path for usage search | same as edit |
| `verbose` | bool | Enable detailed logging | False |
| `exclude_patterns` | str/list | Exclude patterns (comma-separated) | None |
| `methods_include` | bool | Include method definitions | True |
| `classes_include` | bool | Include class definitions | True |
| `functions_include` | bool | Include function definitions | True |

### 5.4. Usage Examples

```bash
# Analyze current directory
python -m uzpy run

# Analyze specific path
python -m uzpy run --edit src/myproject/

# Dry run with verbose output
python -m uzpy test --edit src/ --verbose

# Clean all "Used in:" sections
python -m uzpy clean --edit src/
```

## 6. Dependencies

### 6.1. Core Dependencies (from `pyproject.toml`)

- **Python**: 3.10+
- **tree-sitter**: >=0.20.0
- **tree-sitter-python**: >=0.20.0
- **rope**: >=1.7.0
- **jedi**: >=0.19.0
- **libcst**: >=1.0.0
- **fire**: >=0.5.0
- **rich**: >=13.0.0
- **loguru**: >=0.7.0
- **pathspec**: >=0.11.0

## 7. Implementation Details

### 7.1. Error Handling

Graceful degradation is applied at multiple levels:

1. **Parse Errors** – Partial AST parsing continues after syntax errors.
2. **Analyzer Failures** – Falls back from Rope to Jedi or text search.
3. **Modification Errors** – Logs failures but keeps processing other files.
4. **File Access Errors** – Skips problematic files and warns the user.

### 7.2. Analysis Strategies

The hybrid analyzer chooses its approach based on scale:

- **full_hybrid** – For small projects (<50 constructs): combines Rope and Jedi.
- **jedi_primary** – Default for medium projects: fast first pass with smart verification.
- **rope_only** – Used when Jedi fails.

### 7.3. Docstring Update Behavior

Automatically:
- Preserves formatting and indentation.
- Merges old and new "Used in:" entries.
- Skips self-references.
- Shows relative paths from project root.
- Keeps original quote styles.

## 8. Testing

Includes:
- **Unit Tests** – Per-component functionality.
- **Integration Tests** – End-to-end pipeline runs.
- **Discovery Tests** – File scanning under various ignore rules.
- **Parser Tests** – AST node identification accuracy.
- **Modifier Tests** – Formatting preservation and docstring updates.

## 9. Limitations

1. No config file support (e.g., `.uzpy.toml`).
2. CLI lacks advanced output features like tables or progress bars.
3. No performance benchmarks yet.
4. Edge cases may still cause crashes.
5. No watch mode or real-time monitoring.

## 10. Future Enhancements

Planned:
1. **Enhanced CLI** – Use Rich for better terminal UX.
2. **Configuration Files** – Allow settings via `.uzpy.toml`.
3. **Performance Optimization** – Measure and improve speed for large codebases.
4. **Advanced Features** – Watch mode, plugin system, multi-language support.

---

This spec matches the actual implementation as of January 2025. Everything listed here works, or it doesn’t make the cut.