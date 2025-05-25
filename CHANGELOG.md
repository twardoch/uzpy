# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- LibCST integration for docstring modification (planned)
- Comprehensive test suite expansion (planned)
- Performance optimization (planned)

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