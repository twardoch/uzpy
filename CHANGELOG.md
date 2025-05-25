# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Comprehensive test suite expansion
- Performance optimization for large codebases
- Configuration file support (.uzpy.toml)
- Custom docstring templates

## [1.0.0] - 2025-01-26

### 🎉 Major Release - Complete Implementation

This release marks the completion of all core uzpy functionality. The tool is now fully functional and production-ready.

### Added

#### LibCST Docstring Modification
- **Complete LibCST integration** for safe code modification
- **Docstring updating** with usage information while preserving formatting
- **Smart construct lookup** by file and name matching
- **Usage section generation** with relative file paths
- **Existing usage info removal** to prevent duplication
- **Error recovery** with graceful degradation on modification failures

#### CLI Integration and User Experience
- **Complete analyzer integration** replacing "implementation in progress" placeholder
- **Reference finding pipeline** with hybrid Rope+Jedi approach
- **Rich progress reporting** with construct-by-construct analysis feedback
- **Modification status reporting** showing successful/failed file updates
- **Verbose mode enhancements** with detailed analysis and modification logs

#### Error Handling and Robustness
- **Comprehensive error handling** throughout the analysis and modification pipeline
- **Graceful fallback mechanisms** when analyzers fail
- **Detailed logging** for debugging and troubleshooting
- **Safe file modification** with rollback on errors
- **Construct hashability** fixes for proper dictionary usage

#### Technical Improvements
- **Reference class** for detailed reference information (file, line, context)
- **Construct class hashability** with proper `__hash__` and `__eq__` methods
- **Improved analyzer lookup** with file-based construct matching
- **LibCST transformer** with proper node handling and docstring detection
- **Project root path handling** for relative path generation in usage sections

### Fixed
- **Construct dictionary usage** by implementing proper hash/equality methods
- **Method name mismatch** (find_references → find_usages) in analyzer integration
- **File discovery** for reference analysis with proper FileDiscovery usage
- **LibCST node matching** for accurate construct identification

### Changed
- **CLI workflow** now complete end-to-end from analysis to modification
- **Usage output format** shows "Used in:" sections with relative file paths
- **Error reporting** more comprehensive with specific failure details
- **Logging levels** optimized for better debugging and user feedback

### Demo Usage
```bash
# Complete analysis and docstring updates
python -m uzpy -e src/myproject/

# Preview changes without modification
python -m uzpy -e src/myproject/ --dry-run --verbose

# Single file analysis
python -m uzpy -e src/myproject/module.py --dry-run
```

### Architecture Complete
The tool now implements the full pipeline:
1. **File Discovery** → Finds Python files with gitignore support
2. **Parsing** → Extracts constructs using Tree-sitter
3. **Analysis** → Finds references using hybrid Rope+Jedi approach
4. **Modification** → Updates docstrings using LibCST while preserving formatting

## [0.1.0] - 2025-01-25

### Added
- **Project Foundation**
  - Complete Python packaging with pyproject.toml
  - Modern dependency management with uv
  - Development tools (ruff, pytest, mypy, autoflake, pyupgrade)
  - Semantic versioning with hatch-vcs

- **CLI Interface** 
  - Fire-based automatic CLI generation
  - Rich terminal output with beautiful tables
  - Configuration display and validation
  - Dry-run mode for safe testing
  - Verbose logging with loguru
  - Comprehensive error handling

- **File Discovery System**
  - Efficient Python file discovery with pathspec
  - Gitignore pattern support with default exclusions
  - Custom exclude patterns
  - Recursive directory traversal
  - Permission and error handling
  - File statistics and reporting

- **Tree-sitter Parser Integration**
  - Fast Python AST parsing with Tree-sitter
  - Construct extraction (functions, classes, methods, modules)
  - Docstring parsing and normalization
  - Line number and position tracking
  - Fully qualified name building
  - Error recovery for broken syntax
  - Parse statistics and reporting

- **Hybrid Reference Analyzer**
  - Rope analyzer for accurate cross-file reference finding
  - Jedi analyzer for fast symbol resolution with caching
  - Hybrid analyzer combining both for optimal results
  - Batch processing for efficiency
  - Multiple analysis strategies (full_hybrid, jedi_primary, rope_only)
  - Fallback mechanisms and error handling

- **Code Quality and Testing**
  - Comprehensive ruff configuration for linting and formatting
  - Python 3.11+ modern syntax with type hints
  - Automated import optimization
  - Basic test suite with pytest
  - CLI testing framework

- **Documentation**
  - Professional README with usage examples
  - Detailed implementation plan (PLAN.md)
  - Progress tracking (PROGRESS.md)
  - Comprehensive TODO list for future development

### Changed
- Upgraded to modern Python syntax (3.11+ union types, list/dict generics)
- Optimized imports and removed unused dependencies
- Standardized code formatting across all modules

### Technical Details
- **Architecture**: Three-phase pipeline (Parse → Analyze → Modify)
- **Dependencies**: tree-sitter, rope, jedi, fire, rich, loguru, pathspec
- **Performance**: Efficient file discovery, batch processing, hybrid analysis
- **Error Handling**: Graceful degradation with detailed logging
- **Extensibility**: Modular design ready for future enhancements

### Demo Usage
```bash
# Analyze single file with dry-run
uzpy run --edit src/uzpy/cli.py --dry-run

# Analyze directory with verbose output  
uzpy run --edit src/ --ref . --dry-run --verbose

# Get help
uzpy run --help
```

### Development
- Set up with `uv venv && source .venv/bin/activate && uv pip install -e .`
- Test with `python -m pytest tests/`
- Format with `ruff format . && ruff check --fix .`

## [0.0.1] - 2025-01-25

### Added
- Initial project structure
- Basic package configuration