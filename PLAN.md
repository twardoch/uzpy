# uzpy Implementation Plan

## Project Overview

uzpy is a Python tool that automatically tracks where constructs (functions, classes, methods) are used across codebases and updates their docstrings with usage information. It uses a three-phase pipeline combining Tree-sitter for parsing, Rope and Jedi for reference finding, and LibCST for code modification.

## Architecture

### Core Components

1. **CLI Interface** - Fire-based CLI with Rich formatting
2. **File Discovery** - Efficient Python file discovery with gitignore support
3. **Tree-sitter Parser** - Fast AST parsing with error recovery
4. **Hybrid Analyzer** - Combines Rope and Jedi for optimal reference finding
5. **LibCST Modifier** - Safe docstring modification preserving formatting

### Technology Stack

- **Tree-sitter**: Fast, incremental parsing with excellent error recovery
- **Rope**: Accurate cross-file reference finding and refactoring support
- **Jedi**: Fast symbol resolution with excellent caching
- **LibCST**: Concrete syntax tree for safe code modification
- **Fire**: Automatic CLI generation
- **Rich**: Beautiful terminal output
- **Loguru**: Structured logging

## Implementation Phases

### Phase 1: Foundation ✅ COMPLETED
- [x] Project structure and packaging (pyproject.toml)
- [x] CLI interface with Fire and Rich
- [x] File discovery with gitignore support
- [x] Logging and error handling
- [x] Basic testing framework

### Phase 2: Parsing ✅ COMPLETED
- [x] Tree-sitter Python parser integration
- [x] Construct extraction (functions, classes, methods, modules)
- [x] Docstring parsing and cleaning
- [x] Line number and position tracking
- [x] Fully qualified name building

### Phase 3: Analysis ✅ COMPLETED
- [x] Rope analyzer for accurate reference finding
- [x] Jedi analyzer for fast symbol resolution
- [x] Hybrid analyzer combining both approaches
- [x] Batch processing for efficiency
- [x] Error handling and fallback mechanisms

### Phase 4: Modification 🔄 NEXT
- [ ] LibCST integration for code modification
- [ ] Docstring updating with usage information
- [ ] Formatting preservation
- [ ] Backup and rollback mechanisms
- [ ] Conflict resolution

### Phase 5: Testing & Polish 🔄 NEXT
- [ ] Comprehensive test suite
- [ ] Performance optimization
- [ ] Edge case handling
- [ ] Documentation completion
- [ ] Example projects

### Phase 6: Advanced Features 📋 FUTURE
- [ ] Language Server Protocol support
- [ ] CI/CD integration
- [ ] Visual reporting and analytics
- [ ] Plugin system for extensibility
- [ ] Configuration file support

## Development Workflow

### Code Quality Standards
- Python 3.11+ with modern type hints
- Ruff for linting and formatting
- Pytest for testing
- 100% type coverage with mypy
- Comprehensive docstrings

### Git Workflow
- Feature branches for development
- Pull requests with CI checks
- Semantic versioning
- Automated releases

### Testing Strategy
- Unit tests for individual components
- Integration tests for complete workflows
- Performance benchmarks
- Example project validation

## Key Design Decisions

### Parser Choice: Tree-sitter
- **Pros**: Fast, incremental, excellent error recovery
- **Cons**: More complex setup than ast module
- **Decision**: Speed and robustness for large codebases justified complexity

### Analyzer Strategy: Hybrid Rope + Jedi
- **Rope**: Accurate but slower for complex analysis
- **Jedi**: Fast but may miss edge cases
- **Hybrid**: Use Jedi first, Rope for verification and complex cases

### Modification Tool: LibCST
- **Pros**: Preserves formatting, comments, and exact syntax
- **Cons**: More complex than ast modifications
- **Decision**: Professional tool requires preserving code style

## Current Status

### Completed (v0.1.0)
- Full CLI interface with beautiful output
- Efficient file discovery system
- Complete Tree-sitter parser integration
- Hybrid Rope/Jedi analyzer
- Code quality tools and testing framework

### Working Demo
```bash
uzpy run --edit src/ --dry-run --verbose
```

Shows discovered files, parsed constructs, and analysis summary.

### Next Milestones
1. **v0.2.0**: LibCST docstring modification
2. **v0.3.0**: Complete testing and polish
3. **v1.0.0**: Production-ready release

## Development Environment

### Requirements
- Python 3.11+
- uv for dependency management
- Tree-sitter Python bindings
- Development tools (ruff, pytest, mypy)

### Setup
```bash
git clone <repository>
cd uzpy
uv venv
source .venv/bin/activate
uv pip install -e .[dev,test]
```

### Testing
```bash
python -m pytest tests/
uzpy run --edit . --dry-run
```

## Architecture Decisions

### File Structure
```
uzpy/
├── src/uzpy/
│   ├── cli.py           # Fire-based CLI interface
│   ├── discovery.py     # File discovery with gitignore
│   ├── parser/          # Tree-sitter parsing
│   ├── analyzer/        # Rope/Jedi reference finding
│   └── modifier/        # LibCST code modification
├── tests/               # Test suite
└── examples/            # Example projects
```

### Error Handling Strategy
- Graceful degradation with fallback mechanisms
- Detailed logging for debugging
- User-friendly error messages
- Partial processing when possible

### Performance Considerations
- Lazy loading of heavy dependencies
- Batch processing for efficiency
- Caching of analysis results
- Parallel processing where appropriate

## Future Enhancements

### Language Server Integration
- Real-time usage tracking
- IDE integration
- Interactive documentation

### CI/CD Features
- Pre-commit hooks
- Automated documentation updates
- Usage analytics and reporting

### Extensibility
- Plugin system for custom analyzers
- Configurable output formats
- Integration with documentation tools