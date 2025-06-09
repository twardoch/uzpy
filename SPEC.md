# uzpy Technical Specification

**Version**: 0.1.0  
**Status**: Beta - Functional Implementation  
**Last Updated**: January 2025

## 1. Overview

uzpy is a Python static analysis tool that automatically tracks cross-file usage patterns and updates docstrings with "Used in:" documentation. It combines Tree-sitter parsing, hybrid Rope+Jedi analysis, and LibCST code modification to provide accurate, safe docstring updates.

## 2. Core Requirements

### 2.1. Functional Requirements

1. **Code Discovery**: Discover Python files while respecting `.gitignore` patterns and custom exclusions
2. **Construct Extraction**: Parse Python code to extract functions, classes, methods, and modules with their existing docstrings
3. **Usage Analysis**: Find where each construct is used across the codebase using hybrid analysis  
4. **Docstring Modification**: Update docstrings with "Used in:" sections while preserving all formatting
5. **Error Recovery**: Handle syntax errors, import failures, and analysis errors gracefully

### 2.2. Non-Functional Requirements

1. **Safety**: Zero data loss during code modification with full formatting preservation
2. **Compatibility**: Support Python 3.10+ codebases (actual minimum requirement)
3. **Reliability**: Graceful degradation when analysis tools fail
4. **Maintainability**: Clean modular architecture with separation of concerns

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
- **Technology**: Python Fire for automatic CLI generation
- **Features**:
  - `run` command for analysis and modification
  - `clean` command for removing "Used in:" sections
  - `test` command for dry-run mode
  - Simple logging with loguru
  - Basic error handling and user feedback

#### 3.2.2. File Discovery (`discovery.py`)
- **Technology**: pathlib + pathspec (gitignore parsing)
- **Features**:
  - Python file discovery with glob patterns
  - `.gitignore` pattern respect with default exclusions
  - Custom exclusion patterns support
  - Efficient directory traversal with error handling
  - File statistics reporting

#### 3.2.3. Tree-sitter Parser (`parser/tree_sitter_parser.py`)
- **Technology**: tree-sitter + tree-sitter-python
- **Features**:
  - Fast AST parsing with error recovery
  - Extract functions, classes, methods, and modules
  - Docstring detection and normalization
  - Fully qualified name construction
  - Line number tracking for each construct

#### 3.2.4. Hybrid Analyzer (`analyzer/hybrid_analyzer.py`)
- **Technology**: Rope + Jedi with fallback strategies
- **Components**:
  - `rope_analyzer.py` - Accurate cross-file analysis
  - `jedi_analyzer.py` - Fast symbol resolution
  - `hybrid_analyzer.py` - Combines both with intelligent strategies
- **Features**:
  - Multiple analysis strategies (full_hybrid, jedi_primary, rope_only)
  - Reference deduplication and merging
  - Graceful fallback when analyzers fail

#### 3.2.5. LibCST Modifier (`modifier/libcst_modifier.py`)
- **Technology**: LibCST for concrete syntax tree manipulation
- **Features**:
  - Safe docstring modification preserving all formatting
  - "Used in:" section generation and management
  - Existing usage information merging
  - Relative path generation for references
  - Complete formatting preservation

## 4. Data Models

### 4.1. Core Data Structures

```python
@dataclass
class Construct:
    """Represents a Python construct with metadata"""
    name: str                    # Construct name
    type: ConstructType         # function, class, method, module
    file_path: Path            # Source file location
    line_number: int           # Line number (1-based)
    docstring: str | None      # Current docstring content
    full_name: str            # Fully qualified name
    node: Node | None         # Tree-sitter node reference

@dataclass  
class Reference:
    """Represents a usage reference to a construct"""
    file_path: Path            # File where construct is used
    line_number: int           # Line number of usage
    column_number: int = 0     # Column number of usage
    context: str = ""          # Surrounding code context
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

### 5.1. Actual Command Line Interface

```bash
python -m uzpy [COMMAND] [OPTIONS]
```

### 5.2. Commands

| Command | Description |
|---------|-------------|
| `run` | Analyze and update docstrings (default) |
| `clean` | Remove all "Used in:" sections |
| `test` | Run in dry-run mode |

### 5.3. Constructor Options

| Option | Type | Description | Default |
|--------|------|-------------|---------|
| `edit` | str/Path | Path to analyze and modify | current directory |
| `ref` | str/Path | Reference path for usage search | same as edit |
| `verbose` | bool | Enable detailed logging | False |
| `xclude_patterns` | str/list | Exclude patterns (comma-separated) | None |
| `methods_include` | bool | Include method definitions | True |
| `classes_include` | bool | Include class definitions | True |
| `functions_include` | bool | Include function definitions | True |

### 5.4. Usage Examples

```bash
# Basic usage - analyze current directory
python -m uzpy run

# Analyze specific path
python -m uzpy run --edit src/myproject/

# Dry run with verbose output
python -m uzpy test --edit src/ --verbose

# Clean all "Used in:" sections
python -m uzpy clean --edit src/
```

## 6. Dependencies

### 6.1. Core Dependencies (from pyproject.toml)

- **Python**: 3.10+ (actual minimum requirement)
- **tree-sitter**: >=0.20.0 (AST parsing)
- **tree-sitter-python**: >=0.20.0 (Python grammar)
- **rope**: >=1.7.0 (code analysis)
- **jedi**: >=0.19.0 (symbol resolution)
- **libcst**: >=1.0.0 (code modification)
- **fire**: >=0.5.0 (CLI generation)
- **rich**: >=13.0.0 (terminal output)
- **loguru**: >=0.7.0 (logging)
- **pathspec**: >=0.11.0 (gitignore parsing)

## 7. Implementation Details

### 7.1. Error Handling Strategy

The tool implements graceful degradation at multiple levels:

1. **Parse Errors**: Continue with partial AST if Tree-sitter encounters syntax errors
2. **Analyzer Failures**: Fall back from Rope to Jedi or text-based search
3. **Modification Errors**: Log errors and continue with other files
4. **File Access Errors**: Skip inaccessible files with warnings

### 7.2. Analysis Strategies

The hybrid analyzer uses different strategies based on the situation:

- **full_hybrid**: Use both Rope and Jedi for small codebases (<50 constructs)
- **jedi_primary**: Use Jedi first, verify complex cases with Rope
- **rope_only**: Fall back when Jedi fails

### 7.3. Docstring Update Behavior

The tool automatically:
- Preserves all existing formatting and indentation
- Merges existing "Used in:" sections with new findings
- Excludes self-references (same file)
- Uses relative paths from project root
- Maintains proper docstring quote styles

## 8. Testing

The project includes comprehensive tests:

- **Unit Tests**: Individual component testing
- **Integration Tests**: Full pipeline testing
- **Discovery Tests**: File discovery with various patterns
- **Parser Tests**: AST extraction and construct identification
- **Modifier Tests**: Docstring updating with formatting preservation

## 9. Limitations

1. **No Configuration Files**: No support for `.uzpy.toml` or similar configuration
2. **Basic CLI**: Simple Fire-based CLI without Rich table outputs
3. **No Performance Benchmarks**: No measured performance metrics
4. **Limited Error Recovery**: Some edge cases may not be handled gracefully
5. **No Watch Mode**: No real-time file monitoring

## 10. Future Enhancements

Based on the current implementation, planned improvements include:

1. **Enhanced CLI**: Rich-based terminal output with progress bars and tables
2. **Configuration Support**: `.uzpy.toml` configuration files
3. **Performance Optimization**: Benchmarking and optimization for large codebases
4. **Advanced Features**: Watch mode, plugin system, multi-language support

---

This specification reflects the actual implementation as of January 2025. All documented features are functional and tested.