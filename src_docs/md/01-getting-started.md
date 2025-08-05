---
# this_file: src_docs/md/01-getting-started.md  
---

# Getting Started

This chapter introduces uzpy through practical examples and walks you through your first usage scenarios.

## What uzpy Does

uzpy analyzes your Python codebase to understand where functions, classes, methods, and modules are used, then automatically updates their docstrings with cross-reference information.

### The Problem uzpy Solves

In large Python projects, it's often difficult to:

- Understand where a function or class is being used
- Track the impact of changes to a piece of code
- Maintain up-to-date documentation about code relationships
- Navigate complex codebases efficiently

### The uzpy Solution

uzpy automates the discovery and documentation of code usage patterns:

1. **Discovers constructs**: Finds all functions, classes, methods, and modules in your codebase
2. **Analyzes usage**: Determines where each construct is referenced or imported
3. **Updates documentation**: Adds "Used in:" sections to docstrings
4. **Maintains freshness**: Keeps cross-references current as your code evolves

## Basic Workflow

Here's a typical uzpy workflow:

### 1. Initial Analysis

Run uzpy on your project to analyze and update docstrings:

```bash
# Analyze the src/ directory, searching the entire project for usages
uzpy run --edit src/ --ref .
```

### 2. Review Changes

uzpy will modify docstrings in-place. Before:

```python
def parse_config(config_path):
    """Parse configuration file and return settings."""
    # implementation...
```

After:

```python
def parse_config(config_path):
    """
    Parse configuration file and return settings.
    
    Used in:
    - src/main.py
    - src/cli.py
    - tests/test_config.py
    """
    # implementation...
```

### 3. Safe Mode (Recommended)

For production code, use the `--safe` flag to prevent syntax corruption:

```bash
uzpy run --edit src/ --ref . --safe
```

### 4. Dry Run

Preview changes without modifying files:

```bash
uzpy run --edit src/ --ref . --dry-run
```

## Common Usage Patterns

### Analyzing a Single File

```bash
# Update docstrings in one file, searching the whole project
uzpy run --edit src/utils.py --ref .
```

### Analyzing Specific Directories

```bash
# Update only core modules, search in src and tests
uzpy run --edit src/core/ --ref src/ --ref tests/
```

### Cleaning Up

Remove all "Used in:" sections:

```bash
uzpy clean --edit src/
```

### Configuration File

Create a `.uzpy.env` file for consistent settings:

```bash
# .uzpy.env
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,*.pyc,build/,dist/
UZPY_USE_CACHE=true
UZPY_ANALYZER_TYPE=modern_hybrid
```

Then run uzpy without arguments:

```bash
uzpy run
```

## Real-World Example

Let's walk through analyzing a small Python project:

### Project Structure

```
my_project/
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── processor.py
│   │   └── utils.py
│   └── cli.py
├── tests/
│   ├── test_processor.py
│   └── test_utils.py
└── main.py
```

### Step 1: Analyze Core Components

```bash
uzpy run --edit src/core/ --ref . --verbose
```

This will:

- Scan `src/core/` for function/class definitions
- Search the entire project (`.`) for where these are used
- Update docstrings in `processor.py` and `utils.py`
- Show detailed logging with `--verbose`

### Step 2: Review Results

uzpy might update `src/core/processor.py`:

```python
class DataProcessor:
    """
    Main data processing class.
    
    Used in:
    - src/cli.py
    - main.py
    - tests/test_processor.py
    """
    
    def process_data(self, data):
        """
        Process incoming data using configured rules.
        
        Used in:
        - src/cli.py
        - tests/test_processor.py
        """
        # implementation...
```

### Step 3: Verify and Commit

1. Review the changes to ensure accuracy
2. Run your tests to verify nothing broke
3. Commit the updated docstrings

## Understanding the Output

When uzpy runs, you'll see output like:

```
INFO: Discovering files in src/core/
INFO: Found 5 Python files to analyze
INFO: Parsing definitions...
INFO: Found 12 constructs to analyze
INFO: Running analysis with modern_hybrid analyzer
INFO: Analyzing construct DataProcessor...
INFO: Found 3 references for DataProcessor
INFO: Updating docstring in src/core/processor.py
INFO: Analysis complete. Modified 2 files.
```

## Next Steps

Now that you understand the basics:

1. **[Install uzpy](02-installation.md)** if you haven't already
2. **[Learn the CLI options](03-command-line-usage.md)** for more advanced usage
3. **[Configure uzpy](04-configuration.md)** for your specific needs
4. **[Explore the architecture](05-architecture-overview.md)** to understand how it works

## Tips for Success

- **Start small**: Begin with a single directory or file
- **Use `--dry-run`** to preview changes before applying them  
- **Enable `--safe` mode** for production codebases
- **Configure exclusions** to skip irrelevant files
- **Use caching** for faster re-analysis of large projects
- **Review changes** before committing to version control

The next chapter covers installation and environment setup in detail.