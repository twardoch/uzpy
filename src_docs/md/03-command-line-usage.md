---
# this_file: src_docs/md/03-command-line-usage.md
---

# Command Line Usage

This chapter provides comprehensive documentation for uzpy's command-line interface, covering all commands, options, and usage patterns.

## CLI Overview

uzpy provides a modern CLI built with Typer. The main command is `uzpy`, which is an alias for `uzpy-modern`. A legacy CLI is also available as `uzpy-legacy`.

```bash
uzpy [COMMAND] [OPTIONS]
```

## Global Options

These options are available for all commands:

| Option | Description | Default |
|--------|-------------|---------|
| `--config`, `-c` | Path to configuration file | `.uzpy.env` |
| `--verbose`, `-v` | Enable verbose DEBUG logging | `false` |
| `--log-level` | Set logging level | `INFO` |
| `--help` | Show help message | - |
| `--version` | Show version information | - |

## Commands

### `run` - Analyze and Update Docstrings

The primary command for analyzing code and updating docstrings.

```bash
uzpy run [OPTIONS]
```

#### Core Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--edit` | `-e` | Path to files/directories to modify | ✓ |
| `--ref` | `-r` | Path(s) to search for usages | ✓ |
| `--dry-run` | | Preview changes without modifying files | |
| `--safe` | | Use safe modifier to prevent syntax corruption | |

#### Examples

**Basic usage:**
```bash
# Update src/ directory, search entire project
uzpy run --edit src/ --ref .
```

**Safe mode (recommended for production):**
```bash
uzpy run --edit src/ --ref . --safe
```

**Preview changes:**
```bash
uzpy run --edit src/ --ref . --dry-run
```

**Single file:**
```bash
uzpy run --edit src/utils.py --ref .
```

**Multiple reference paths:**
```bash
uzpy run --edit src/core/ --ref src/ --ref tests/
```

#### Advanced Options

| Option | Description | Default |
|--------|-------------|---------|
| `--exclude` | Additional exclude patterns | |
| `--analyzer` | Choose analyzer type | `modern_hybrid` |
| `--no-cache` | Disable caching | |
| `--parallel` | Enable parallel processing | |
| `--timeout` | Analysis timeout per construct (seconds) | `30` |

**Advanced examples:**

```bash
# Use specific analyzer
uzpy run --edit src/ --ref . --analyzer jedi

# Disable caching
uzpy run --edit src/ --ref . --no-cache

# Custom exclusions
uzpy run --edit src/ --ref . --exclude "**/*_test.py"

# Set timeout
uzpy run --edit src/ --ref . --timeout 60
```

### `clean` - Remove Usage Sections

Remove "Used in:" sections from docstrings.

```bash
uzpy clean [OPTIONS]
```

#### Options

| Option | Short | Description | Required |
|--------|-------|-------------|----------|
| `--edit` | `-e` | Path to files/directories to clean | ✓ |
| `--dry-run` | | Preview changes without modifying files | |

#### Examples

```bash
# Remove all "Used in:" sections from src/
uzpy clean --edit src/

# Preview cleanup
uzpy clean --edit src/ --dry-run

# Clean specific file
uzpy clean --edit src/utils.py
```

### `cache` - Cache Management

Manage uzpy's analysis cache.

```bash
uzpy cache [SUBCOMMAND]
```

#### Subcommands

**Clear cache:**
```bash
uzpy cache clear
```

**Show cache statistics:**
```bash
uzpy cache stats
```

Example output:
```
Cache Statistics:
- Parser cache: 1,234 entries (45.2 MB)
- Analyzer cache: 567 entries (12.8 MB)
- Total disk usage: 58.0 MB
- Cache directory: /home/user/.cache/uzpy
```

### `watch` - File Monitoring (Experimental)

Monitor files for changes and automatically re-run analysis.

```bash
uzpy watch [OPTIONS]
```

#### Options

| Option | Short | Description |
|--------|-------|-------------|
| `--path` | `-p` | Directory to watch (overrides config) |
| `--debounce` | | Debounce delay in seconds | `2.0` |

#### Examples

```bash
# Watch configured edit_path
uzpy watch

# Watch specific directory
uzpy watch --path src/

# Custom debounce delay
uzpy watch --path src/ --debounce 5.0
```

## Configuration File

Create a `.uzpy.env` file to avoid repeating options:

```bash
# .uzpy.env
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/
UZPY_USE_CACHE=true
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_LOG_LEVEL=INFO
UZPY_SAFE_MODE=true
```

Then run commands without options:

```bash
# Uses settings from .uzpy.env
uzpy run

# Override specific settings
uzpy run --analyzer jedi --verbose
```

## Analyzer Types

Choose different analysis engines based on your needs:

### `modern_hybrid` (Default)

Multi-tiered approach using modern tools:
- **ruff** for basic checks
- **ast-grep** for structural matching  
- **pyright** for type-aware analysis

```bash
uzpy run --edit src/ --ref . --analyzer modern_hybrid
```

**Pros:**
- Most accurate for modern Python codebases
- Fast with good caching
- Type-aware analysis

**Cons:**
- Requires more dependencies
- May be slower on first run

### `hybrid`

Traditional hybrid approach:
- **jedi** for fast symbol resolution
- **rope** for robust static analysis

```bash
uzpy run --edit src/ --ref . --analyzer hybrid
```

**Pros:**
- Reliable and well-tested
- Good balance of speed and accuracy
- Fewer external dependencies

**Cons:**
- Less accurate for complex type relationships
- May miss some modern Python patterns

### `jedi`

Fast analysis using only Jedi:

```bash
uzpy run --edit src/ --ref . --analyzer jedi
```

**Pros:**
- Very fast
- Minimal dependencies
- Good for large codebases

**Cons:**
- May miss complex references
- Less accurate than hybrid approaches

### `rope`

Robust analysis using only Rope:

```bash
uzpy run --edit src/ --ref . --analyzer rope
```

**Pros:**
- Very thorough analysis
- Handles complex refactoring scenarios
- Good for precise results

**Cons:**
- Slower than other options
- May have higher memory usage

### `pyright`

Type-aware analysis using Microsoft's Pyright:

```bash
uzpy run --edit src/ --ref . --analyzer pyright
```

**Pros:**
- Excellent type awareness
- Modern Python feature support
- Cross-file analysis

**Cons:**
- Requires Node.js ecosystem
- May be slower for large codebases

## Environment Variables

All CLI options can be set via environment variables:

| Environment Variable | CLI Option | Example |
|---------------------|------------|---------|
| `UZPY_EDIT_PATH` | `--edit` | `src/` |
| `UZPY_REF_PATH` | `--ref` | `.` |
| `UZPY_EXCLUDE_PATTERNS` | `--exclude` | `**/*.pyc,build/` |
| `UZPY_ANALYZER_TYPE` | `--analyzer` | `modern_hybrid` |
| `UZPY_USE_CACHE` | `--no-cache` | `true`/`false` |
| `UZPY_SAFE_MODE` | `--safe` | `true`/`false` |
| `UZPY_VERBOSE` | `--verbose` | `true`/`false` |
| `UZPY_LOG_LEVEL` | `--log-level` | `DEBUG` |
| `UZPY_TIMEOUT` | `--timeout` | `60` |

Set environment variables:

```bash
# In shell
export UZPY_EDIT_PATH="src/"
export UZPY_REF_PATH="."
export UZPY_SAFE_MODE="true"

# Run with environment settings
uzpy run
```

## Output and Logging

### Log Levels

| Level | Description | Example Use |
|-------|-------------|-------------|
| `DEBUG` | Detailed debugging information | Development and troubleshooting |
| `INFO` | General information about progress | Normal operation |
| `WARNING` | Warning messages about potential issues | Production monitoring |
| `ERROR` | Error messages for failures | Error tracking |
| `CRITICAL` | Critical errors that stop execution | System failures |

### Verbose Output

Enable verbose logging to see detailed analysis progress:

```bash
uzpy run --edit src/ --ref . --verbose
```

Example verbose output:
```
DEBUG: Loading configuration from .uzpy.env
DEBUG: Edit paths: ['src/']
DEBUG: Reference paths: ['.']
DEBUG: Using analyzer: modern_hybrid
INFO: Discovering files in src/
DEBUG: Found file: src/__init__.py
DEBUG: Found file: src/core.py
DEBUG: Found file: src/utils.py
INFO: Found 3 Python files to analyze
INFO: Parsing definitions...
DEBUG: Parsing src/core.py
DEBUG: Found function: process_data at line 15
DEBUG: Found class: DataProcessor at line 45
INFO: Found 12 constructs to analyze
INFO: Running analysis with modern_hybrid analyzer
DEBUG: Analyzing construct process_data from src/core.py
DEBUG: Found reference in src/main.py at line 23
DEBUG: Found reference in tests/test_core.py at line 12
INFO: Found 2 references for process_data
INFO: Updating docstring in src/core.py
INFO: Analysis complete. Modified 1 file.
```

### Dry Run Output

Preview changes with `--dry-run`:

```bash
uzpy run --edit src/ --ref . --dry-run
```

Example dry run output:
```
INFO: DRY RUN MODE - No files will be modified
INFO: Would update src/core.py:
--- Original docstring ---
"""Process data using configured rules."""

--- New docstring ---
"""
Process data using configured rules.

Used in:
- src/main.py
- tests/test_core.py
"""

INFO: DRY RUN: Would modify 1 file
```

## Error Handling

### Common Errors

**File not found:**
```
ERROR: Path 'nonexistent.py' not found
```

**Permission denied:**
```
ERROR: Permission denied writing to 'src/core.py'
```

**Syntax error in target file:**
```
ERROR: Failed to parse 'src/broken.py': invalid syntax at line 15
```

**Analysis timeout:**
```
WARNING: Analysis of 'complex_function' timed out after 30 seconds
```

### Exit Codes

| Code | Meaning |
|------|---------|
| `0` | Success |
| `1` | General error |
| `2` | File not found |
| `3` | Permission error |
| `4` | Syntax error |
| `5` | Analysis error |

## Performance Tips

### Large Codebases

For large projects (1000+ files):

```bash
# Enable parallel processing
uzpy run --edit src/ --ref . --parallel

# Use caching (enabled by default)
uzpy run --edit src/ --ref . --no-cache false

# Increase timeout for complex analysis
uzpy run --edit src/ --ref . --timeout 120

# Exclude unnecessary files
uzpy run --edit src/ --ref . --exclude "**/test_*"
```

### Incremental Analysis

Analyze only changed files by excluding unchanged directories:

```bash
# Only analyze core modules
uzpy run --edit src/core/ --ref .

# Exclude large test directories
uzpy run --edit src/ --ref . --exclude "tests/integration/**"
```

## Shell Integration

### Bash Completion

Enable command completion:

```bash
# Add to ~/.bashrc
eval "$(_UZPY_COMPLETE=bash_source uzpy)"
```

### Aliases

Create convenient aliases:

```bash
# Add to shell config
alias uzpy-safe='uzpy run --safe --verbose'
alias uzpy-preview='uzpy run --dry-run --verbose'
alias uzpy-clean='uzpy clean --dry-run'
```

### Scripts

Create scripts for common workflows:

```bash
#!/bin/bash
# uzpy-project.sh
set -e

echo "Running uzpy analysis on project..."
uzpy run --edit src/ --ref . --safe --verbose

echo "Running tests..."
python -m pytest

echo "Checking for syntax errors..."
python -m py_compile src/**/*.py

echo "Analysis complete!"
```

## Next Steps

Now that you understand the CLI:

1. **[Configure uzpy](04-configuration.md)** for your specific needs
2. **[Learn the architecture](05-architecture-overview.md)** to understand how it works
3. **[Use the API](06-api-reference.md)** for programmatic access

The next chapter covers advanced configuration options and customization.