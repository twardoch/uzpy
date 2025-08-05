---
# this_file: src_docs/md/04-configuration.md
---

# Configuration

This chapter covers uzpy's extensive configuration system, including configuration files, environment variables, and advanced customization options.

## Configuration Overview

uzpy uses a hierarchical configuration system:

1. **Default values** (built into uzpy)
2. **Configuration file** (`.uzpy.env`)
3. **Environment variables** (`UZPY_*`)
4. **Command-line arguments** (highest priority)

Each level can override the previous ones, giving you flexible control over uzpy's behavior.

## Configuration File

### Basic .uzpy.env File

Create a `.uzpy.env` file in your project root:

```bash
# Basic uzpy configuration
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/
UZPY_USE_CACHE=true
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_SAFE_MODE=true
UZPY_LOG_LEVEL=INFO
```

### Custom Configuration File

Use a custom configuration file location:

```bash
# Custom config file
uzpy run --config /path/to/my-config.env

# Environment variable
export UZPY_CONFIG_FILE=/path/to/my-config.env
```

### Multiple Configuration Files

Layer configurations for different environments:

```bash
# Base configuration: .uzpy.env
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_USE_CACHE=true

# Development overrides: .uzpy.dev.env  
UZPY_LOG_LEVEL=DEBUG
UZPY_VERBOSE=true
UZPY_ANALYZER_TYPE=jedi

# Production overrides: .uzpy.prod.env
UZPY_LOG_LEVEL=WARNING
UZPY_SAFE_MODE=true
UZPY_ANALYZER_TYPE=modern_hybrid
```

Load specific config:
```bash
uzpy run --config .uzpy.dev.env
```

## Core Configuration Options

### Path Configuration

| Setting | Description | Example | Default |
|---------|-------------|---------|---------|
| `UZPY_EDIT_PATH` | Path(s) to analyze and modify | `src/,lib/` | (required) |
| `UZPY_REF_PATH` | Path(s) to search for usages | `.,tests/` | (required) |
| `UZPY_EXCLUDE_PATTERNS` | Comma-separated exclusion patterns | `**/*.pyc,build/` | See below |

**Path examples:**

```bash
# Single paths
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.

# Multiple paths (comma-separated)
UZPY_EDIT_PATH=src/,lib/,utils/
UZPY_REF_PATH=.,tests/,examples/

# Specific files
UZPY_EDIT_PATH=src/core.py,src/utils.py
UZPY_REF_PATH=src/,tests/
```

### Exclusion Patterns

Default exclusions (you can add to these):

```bash
UZPY_EXCLUDE_PATTERNS=\
**/__pycache__/**,\
**/.pytest_cache/**,\
**/.mypy_cache/**,\
**/.git/**,\
**/venv/**,\
**/env/**,\
**/.venv/**,\
**/build/**,\
**/dist/**,\
**/*.egg-info/**,\
**/.tox/**,\
**/.nox/**,\
**/*.pyc,\
**/*.pyo,\
**/*.pyd,\
**/.DS_Store
```

**Custom exclusions:**

```bash
# Add project-specific exclusions
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/,docs/,migrations/,*.min.js

# Exclude test files
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,**/test_*,**/tests/**

# Exclude large generated files
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,**/generated/**,**/proto/**
```

## Analyzer Configuration

### Analyzer Selection

| Analyzer | Description | Best For |
|----------|-------------|----------|
| `modern_hybrid` | Multi-tier modern tools | General use, accuracy |
| `hybrid` | Traditional jedi + rope | Reliability, compatibility |
| `jedi` | Fast Jedi-only analysis | Speed, large codebases |
| `rope` | Thorough Rope analysis | Precision, refactoring |
| `pyright` | Type-aware analysis | Type-heavy codebases |
| `ast_grep` | Structural pattern matching | Simple pattern finding |
| `ruff` | Basic ruff-based analysis | Minimal dependencies |

```bash
# Set default analyzer
UZPY_ANALYZER_TYPE=modern_hybrid

# Override for specific runs
uzpy run --analyzer jedi
```

### Modern Hybrid Analyzer

Fine-tune the modern hybrid analyzer:

```bash
# Modern hybrid configuration
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_MODERN_HYBRID_RUFF_THRESHOLD=100
UZPY_MODERN_HYBRID_ASTGREP_THRESHOLD=50
UZPY_MODERN_HYBRID_PYRIGHT_THRESHOLD=10
UZPY_MODERN_HYBRID_SHORT_CIRCUIT=true
```

| Setting | Description | Default |
|---------|-------------|---------|
| `RUFF_THRESHOLD` | Max files before skipping ruff | `100` |
| `ASTGREP_THRESHOLD` | Max files before skipping ast-grep | `50` |
| `PYRIGHT_THRESHOLD` | Max files before skipping pyright | `10` |
| `SHORT_CIRCUIT` | Stop at first successful analyzer | `true` |

### Hybrid Analyzer

Configure traditional hybrid analyzer:

```bash
UZPY_ANALYZER_TYPE=hybrid
UZPY_HYBRID_JEDI_THRESHOLD=200
UZPY_HYBRID_ROPE_THRESHOLD=100
UZPY_HYBRID_PREFER_JEDI=true
```

### Individual Analyzers

Configure specific analyzers:

```bash
# Jedi analyzer
UZPY_JEDI_FOLLOW_IMPORTS=true
UZPY_JEDI_AUTO_IMPORT_MODULES=true

# Rope analyzer  
UZPY_ROPE_PROJECT_ROOT=.
UZPY_ROPE_IGNORE_SYNTAX_ERRORS=true

# Pyright analyzer
UZPY_PYRIGHT_CONFIG_FILE=pyrightconfig.json
UZPY_PYRIGHT_TYPE_CHECK_MODE=basic
```

## Caching Configuration

### Cache Settings

```bash
# Enable/disable caching
UZPY_USE_CACHE=true

# Cache directories
UZPY_CACHE_DIR=~/.cache/uzpy
UZPY_PARSER_CACHE_SIZE=1000
UZPY_ANALYZER_CACHE_SIZE=500

# Cache expiration
UZPY_CACHE_TTL=86400  # 24 hours in seconds
```

### Cache Management

```bash
# Per-analyzer cache settings
UZPY_CACHE_PARSER_ENABLED=true
UZPY_CACHE_ANALYZER_ENABLED=true
UZPY_CACHE_COMPRESS=true

# Memory limits
UZPY_CACHE_MAX_MEMORY_MB=512
UZPY_CACHE_EVICTION_POLICY=lru
```

## Performance Configuration

### Parallel Processing

```bash
# Enable parallel analysis
UZPY_PARALLEL_ENABLED=true
UZPY_PARALLEL_MAX_WORKERS=4

# Process pool configuration
UZPY_PARALLEL_CHUNK_SIZE=10
UZPY_PARALLEL_TIMEOUT=300
```

### Analysis Timeouts

```bash
# Global timeout per construct (seconds)
UZPY_TIMEOUT=30

# Per-analyzer timeouts
UZPY_JEDI_TIMEOUT=10
UZPY_ROPE_TIMEOUT=20
UZPY_PYRIGHT_TIMEOUT=45
```

### Memory Management

```bash
# Memory limits
UZPY_MAX_MEMORY_MB=1024
UZPY_MAX_FILE_SIZE_MB=10

# Garbage collection
UZPY_GC_FREQUENCY=100
UZPY_GC_ENABLED=true
```

## Modification Configuration

### Safe Mode

```bash
# Enable safe modifications (recommended)
UZPY_SAFE_MODE=true

# Safe modifier settings
UZPY_SAFE_PRESERVE_QUOTES=true
UZPY_SAFE_VALIDATE_SYNTAX=true
UZPY_SAFE_BACKUP_ENABLED=false
```

### Docstring Formatting

```bash
# Docstring style
UZPY_DOCSTRING_STYLE=google  # google, numpy, sphinx, plain
UZPY_DOCSTRING_MAX_LINE_LENGTH=79
UZPY_DOCSTRING_INDENT_SIZE=4

# Usage section formatting
UZPY_USAGE_SECTION_TITLE="Used in:"
UZPY_USAGE_RELATIVE_PATHS=true
UZPY_USAGE_SORT_PATHS=true
UZPY_USAGE_GROUP_BY_TYPE=false
```

### File Modification

```bash
# Backup settings
UZPY_BACKUP_ENABLED=false
UZPY_BACKUP_SUFFIX=.uzpy-backup
UZPY_BACKUP_DIR=backups/

# Modification behavior
UZPY_PRESERVE_FORMATTING=true
UZPY_NORMALIZE_WHITESPACE=false
UZPY_UPDATE_EXISTING_SECTIONS=true
UZPY_MERGE_DUPLICATE_REFERENCES=true
```

## Logging Configuration

### Log Levels and Output

```bash
# Basic logging
UZPY_LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
UZPY_VERBOSE=false

# Log output
UZPY_LOG_FILE=uzpy.log
UZPY_LOG_FORMAT=text  # text, json
UZPY_LOG_ROTATION=true
UZPY_LOG_MAX_SIZE_MB=10
```

### Detailed Logging

```bash
# Component-specific logging
UZPY_LOG_PARSER=INFO
UZPY_LOG_ANALYZER=DEBUG
UZPY_LOG_MODIFIER=WARNING
UZPY_LOG_CACHE=ERROR

# Performance logging
UZPY_LOG_TIMING=true
UZPY_LOG_MEMORY=false
UZPY_LOG_STATS=true
```

## Watch Mode Configuration

```bash
# File watching
UZPY_WATCH_ENABLED=true
UZPY_WATCH_DEBOUNCE=2.0
UZPY_WATCH_RECURSIVE=true

# Watch patterns
UZPY_WATCH_PATTERNS=**/*.py
UZPY_WATCH_IGNORE_PATTERNS=**/__pycache__/**,**/.git/**

# Watch behavior
UZPY_WATCH_AUTO_RUN=true
UZPY_WATCH_NOTIFY=true
```

## Environment-Specific Configurations

### Development Environment

```bash
# .uzpy.dev.env
UZPY_LOG_LEVEL=DEBUG
UZPY_VERBOSE=true
UZPY_ANALYZER_TYPE=jedi
UZPY_USE_CACHE=false
UZPY_SAFE_MODE=false
UZPY_PARALLEL_ENABLED=false
```

### Production Environment

```bash
# .uzpy.prod.env
UZPY_LOG_LEVEL=WARNING
UZPY_VERBOSE=false
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_USE_CACHE=true
UZPY_SAFE_MODE=true
UZPY_PARALLEL_ENABLED=true
UZPY_BACKUP_ENABLED=true
```

### CI/CD Environment

```bash
# .uzpy.ci.env
UZPY_LOG_LEVEL=INFO
UZPY_VERBOSE=true
UZPY_ANALYZER_TYPE=hybrid
UZPY_USE_CACHE=false
UZPY_SAFE_MODE=true
UZPY_PARALLEL_ENABLED=true
UZPY_TIMEOUT=60
```

## Project-Specific Configuration

### Monorepo Configuration

For large monorepos with multiple Python packages:

```bash
# .uzpy.env
UZPY_EDIT_PATH=packages/core/,packages/utils/,packages/api/
UZPY_REF_PATH=packages/,tests/,scripts/
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,**/node_modules/**,**/build/**
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_PARALLEL_ENABLED=true
UZPY_PARALLEL_MAX_WORKERS=8
```

### Library Project

For Python libraries:

```bash
# .uzpy.env  
UZPY_EDIT_PATH=src/mylib/
UZPY_REF_PATH=src/,tests/,examples/,docs/
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,build/,dist/,*.egg-info/
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_SAFE_MODE=true
UZPY_DOCSTRING_STYLE=sphinx
```

### Application Project

For Python applications:

```bash
# .uzpy.env
UZPY_EDIT_PATH=app/,lib/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,static/,media/,migrations/
UZPY_ANALYZER_TYPE=hybrid
UZPY_SAFE_MODE=true
UZPY_WATCH_ENABLED=true
```

## Configuration Validation

### Validate Configuration

Check your configuration:

```bash
# Test configuration loading
uzpy run --dry-run --verbose

# Check for configuration errors
uzpy config validate  # (if this command exists)
```

### Common Configuration Issues

**Path resolution:**
```bash
# Use absolute paths if relative paths cause issues
UZPY_EDIT_PATH=/full/path/to/src/
UZPY_REF_PATH=/full/path/to/project/
```

**Pattern conflicts:**
```bash
# Ensure exclusion patterns don't conflict with edit paths
UZPY_EDIT_PATH=src/
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**  # Don't exclude src/
```

**Analyzer availability:**
```bash
# Verify analyzer dependencies are installed
UZPY_ANALYZER_TYPE=modern_hybrid  # Requires pyright, ast-grep
UZPY_ANALYZER_TYPE=jedi          # Minimal dependencies
```

## Configuration Templates

### Template Generation

Create configuration templates for common scenarios:

```bash
# Generate basic template
cat > .uzpy.env << EOF
# uzpy configuration
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/
UZPY_USE_CACHE=true
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_SAFE_MODE=true
UZPY_LOG_LEVEL=INFO
EOF
```

### Team Configuration

Share configuration across team members:

```bash
# .uzpy.team.env (checked into version control)
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/
UZPY_USE_CACHE=true
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_SAFE_MODE=true

# .uzpy.env (local overrides, in .gitignore)
UZPY_LOG_LEVEL=DEBUG
UZPY_VERBOSE=true
```

## Next Steps

With uzpy configured for your project:

1. **[Understand the architecture](05-architecture-overview.md)** to see how components work together
2. **[Use the API](06-api-reference.md)** for programmatic access
3. **[Extend uzpy](07-extending-uzpy.md)** with custom analyzers or modifiers

The next chapter provides an in-depth look at uzpy's architecture and design.