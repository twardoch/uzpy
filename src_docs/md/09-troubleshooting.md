---
# this_file: src_docs/md/09-troubleshooting.md
---

# Troubleshooting

This chapter covers common issues, debugging techniques, and solutions for uzpy problems. Learn how to diagnose and fix issues with analysis, file modifications, and performance.

## Common Issues and Solutions

### Installation Issues

#### Issue: ImportError for tree-sitter

```
ImportError: No module named 'tree_sitter'
```

**Cause**: Tree-sitter bindings not properly installed or compiled.

**Solutions**:

```bash
# Solution 1: Reinstall tree-sitter
uv pip uninstall tree-sitter tree-sitter-python
uv pip install tree-sitter tree-sitter-python

# Solution 2: Force recompilation
uv pip install --force-reinstall --no-cache-dir tree-sitter tree-sitter-python

# Solution 3: Install build dependencies (Linux)
sudo apt-get install build-essential
uv pip install tree-sitter tree-sitter-python

# Solution 4: Use pre-compiled wheels
uv pip install --only-binary=all tree-sitter tree-sitter-python
```

#### Issue: Permission errors during installation

```
PermissionError: [Errno 13] Permission denied: '/usr/local/lib/python3.11/site-packages/'
```

**Solutions**:

```bash
# Solution 1: Use virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or .venv\Scripts\activate  # Windows
uv pip install uzpy

# Solution 2: User installation
uv pip install --user uzpy

# Solution 3: Fix permissions (macOS/Linux)
sudo chown -R $(whoami) /usr/local/lib/python3.11/site-packages/
```

#### Issue: Dependency conflicts

```
ERROR: pip's dependency resolver does not currently have a solution
```

**Solution**:

```bash
# Create fresh environment
python -m venv .venv-uzpy
source .venv-uzpy/bin/activate
uv pip install uzpy[all]

# Or use specific versions
uv pip install 'uzpy==1.3.1' 'jedi==0.19.1' 'rope==1.7.0'
```

### File Discovery Issues

#### Issue: No Python files found

```
INFO: Found 0 Python files to analyze
```

**Debugging**:

```bash
# Check if files exist
find /path/to/project -name "*.py" | head -10

# Test with verbose logging
uzpy run --edit src/ --ref . --verbose

# Check exclusion patterns
uzpy run --edit src/ --ref . --exclude "" --verbose
```

**Common causes**:

1. **Wrong path**: Verify edit and ref paths exist
2. **Overly broad exclusions**: Check `UZPY_EXCLUDE_PATTERNS`
3. **Permission issues**: Ensure read access to directories

**Solutions**:

```bash
# Solution 1: Use absolute paths
uzpy run --edit /absolute/path/to/src --ref /absolute/path/to/project

# Solution 2: Check current directory
pwd
ls -la src/

# Solution 3: Minimal exclusions
uzpy run --edit src/ --ref . --exclude "**/__pycache__/**"

# Solution 4: Test with single file
uzpy run --edit src/main.py --ref .
```

#### Issue: Files excluded unexpectedly

**Debugging**:

```python
# test_discovery.py
from uzpy.discovery import FileDiscovery
from pathlib import Path

# Test discovery with your patterns
discovery = FileDiscovery(
    exclude_patterns=["**/__pycache__/**", "*.pyc"]
)

files = discovery.discover_python_files([Path("src/")])
print(f"Found {len(files)} files:")
for file in files[:10]:  # Show first 10
    print(f"  {file}")

# Test specific file
test_file = Path("src/problematic_file.py")
print(f"Is Python file: {discovery.is_python_file(test_file)}")
```

### Parsing Issues

#### Issue: Syntax errors in target files

```
ERROR: Failed to parse 'src/broken.py': invalid syntax at line 15
```

**Debugging**:

```bash
# Check file syntax manually
python -m py_compile src/broken.py

# Use safe mode to handle syntax errors
uzpy run --edit src/ --ref . --safe

# Skip problematic files temporarily
uzpy run --edit src/ --ref . --exclude "**/broken.py"
```

**Solutions**:

```python
# Fix syntax errors in the file
# Or exclude broken files from analysis

# .uzpy.env
UZPY_EXCLUDE_PATTERNS=**/__pycache__/**,**/broken.py,**/legacy/**
```

#### Issue: Encoding errors

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0x... in position ...
```

**Solutions**:

```python
# Identify files with encoding issues
# encoding_check.py
from pathlib import Path
import chardet

def check_encoding(file_path: Path):
    """Check file encoding."""
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        return f"Error: {e}"

# Check all Python files
for py_file in Path("src").rglob("*.py"):
    encoding = check_encoding(py_file)
    if encoding != 'utf-8':
        print(f"{py_file}: {encoding}")
```

**Fix encoding issues**:

```bash
# Convert files to UTF-8
iconv -f ISO-8859-1 -t UTF-8 problematic_file.py > fixed_file.py

# Or exclude problematic files
uzpy run --edit src/ --ref . --exclude "**/problematic_file.py"
```

### Analysis Issues

#### Issue: Analysis timeouts

```
WARNING: Analysis of 'complex_function' timed out after 30 seconds
```

**Solutions**:

```bash
# Increase timeout
uzpy run --edit src/ --ref . --timeout 120

# Use faster analyzer
uzpy run --edit src/ --ref . --analyzer jedi

# Enable parallel processing
uzpy run --edit src/ --ref . --parallel
```

**Configuration**:

```bash
# .uzpy.env
UZPY_TIMEOUT=120
UZPY_ANALYZER_TYPE=jedi
UZPY_PARALLEL_ENABLED=true
```

#### Issue: No references found for obvious usage

**Debugging**:

```python
# debug_analysis.py
from pathlib import Path
from uzpy.parser import TreeSitterParser
from uzpy.analyzer import JediAnalyzer, RopeAnalyzer

def debug_missing_references():
    """Debug why references aren't found."""
    
    # Parse construct
    parser = TreeSitterParser()
    constructs = parser.parse_file(Path("src/mymodule.py"))
    
    target_construct = None
    for c in constructs:
        if c.name == "my_function":
            target_construct = c
            break
    
    if not target_construct:
        print("Construct not found in parsing!")
        return
    
    print(f"Found construct: {target_construct.full_name}")
    
    # Try different analyzers
    analyzers = {
        "jedi": JediAnalyzer(),
        "rope": RopeAnalyzer()
    }
    
    search_paths = [Path(".")]
    
    for name, analyzer in analyzers.items():
        print(f"\n--- {name.upper()} ANALYZER ---")
        try:
            refs = analyzer.find_references(target_construct, search_paths)
            print(f"Found {len(refs)} references:")
            for ref in refs[:5]:  # Show first 5
                print(f"  {ref.file_path}:{ref.line_number}")
        except Exception as e:
            print(f"Error: {e}")

debug_missing_references()
```

**Common causes**:

1. **Import issues**: Analyzer can't resolve imports
2. **Dynamic usage**: Code uses dynamic imports or `getattr`
3. **Complex inheritance**: Multiple inheritance confuses analysis
4. **Generated code**: Code generated at runtime

**Solutions**:

```bash
# Try different analyzers
uzpy run --edit src/ --ref . --analyzer rope
uzpy run --edit src/ --ref . --analyzer modern_hybrid

# Ensure all dependencies are installed
uv pip install -e .  # Install project in development mode

# Check Python path
export PYTHONPATH=/path/to/project:$PYTHONPATH
```

#### Issue: Analyzer crashes

```
ERROR: Analyzer failed with exception: ...
```

**Debugging**:

```bash
# Enable debug logging
uzpy run --edit src/ --ref . --log-level DEBUG

# Try with single file
uzpy run --edit src/single_file.py --ref . --verbose

# Use safe fallback analyzer
uzpy run --edit src/ --ref . --analyzer jedi
```

**Create fallback strategy**:

```python
# robust_analysis.py
from uzpy.analyzer import JediAnalyzer, RopeAnalyzer, RuffAnalyzer

class RobustAnalyzer:
    """Analyzer with multiple fallbacks."""
    
    def __init__(self):
        self.analyzers = [
            JediAnalyzer(),
            RopeAnalyzer(), 
            RuffAnalyzer()
        ]
    
    def find_references(self, construct, search_paths):
        """Try analyzers in order until one works."""
        
        for i, analyzer in enumerate(self.analyzers):
            try:
                refs = analyzer.find_references(construct, search_paths)
                if refs:  # If we found references, use them
                    return refs
            except Exception as e:
                print(f"Analyzer {i+1} failed: {e}")
                continue
        
        print(f"All analyzers failed for {construct.name}")
        return []
```

### Modification Issues

#### Issue: File modification failures

```
ERROR: Failed to modify file: Permission denied
```

**Solutions**:

```bash
# Check file permissions
ls -la src/problematic_file.py

# Fix permissions
chmod 644 src/problematic_file.py

# Use dry run to test
uzpy run --edit src/ --ref . --dry-run

# Check disk space
df -h
```

#### Issue: Syntax corruption after modification

```
ERROR: Modified file has syntax errors
```

**Solutions**:

```bash
# Always use safe mode for production
uzpy run --edit src/ --ref . --safe

# Enable backup
UZPY_BACKUP_ENABLED=true uzpy run --edit src/ --ref .

# Test with single file first
uzpy run --edit src/simple_file.py --ref . --safe --dry-run
```

**Recovery**:

```bash
# Restore from git
git checkout -- src/corrupted_file.py

# Restore from backup (if enabled)
cp src/corrupted_file.py.uzpy-backup src/corrupted_file.py
```

#### Issue: Docstring formatting problems

**Before (problematic)**:
```python
def my_function():
    '''Single quotes cause issues.'''
    pass
```

**After uzpy**:
```python
def my_function():
    '''Single quotes cause issues.
    
    Used in:
    - main.py
    '''  # <- Mixing quote styles!
    pass
```

**Solutions**:

```bash
# Use safe mode to handle quotes properly
uzpy run --edit src/ --ref . --safe

# Configure quote preservation
UZPY_SAFE_PRESERVE_QUOTES=true
```

### Performance Issues

#### Issue: Very slow analysis

**Diagnosis**:

```python
# profile_slow_analysis.py
import cProfile
from uzpy.pipeline import run_analysis_and_modification
from pathlib import Path

def profile_analysis():
    """Profile slow analysis to find bottlenecks."""
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    results = run_analysis_and_modification(
        edit_path=Path("src/"),
        ref_path=Path("."),
        analyzer_type="modern_hybrid"
    )
    
    profiler.disable()
    profiler.print_stats(sort='cumulative', limit=20)
    
    return results

profile_analysis()
```

**Solutions**:

```bash
# Use faster analyzer
uzpy run --edit src/ --ref . --analyzer jedi

# Enable caching
uzpy run --edit src/ --ref . --no-cache false

# Exclude large directories
uzpy run --edit src/ --ref . --exclude "**/tests/**,**/migrations/**"

# Enable parallel processing
uzpy run --edit src/ --ref . --parallel
```

#### Issue: High memory usage

**Monitoring**:

```python
# memory_monitor.py
import psutil
import os
from uzpy.pipeline import run_analysis_and_modification
from pathlib import Path

def monitor_memory():
    """Monitor memory usage during analysis."""
    
    process = psutil.Process(os.getpid())
    
    print(f"Initial memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    
    results = run_analysis_and_modification(
        edit_path=Path("src/"),
        ref_path=Path("."),
        use_cache=True
    )
    
    print(f"Final memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    
    return results

monitor_memory()
```

**Solutions**:

```bash
# Reduce cache size
UZPY_PARSER_CACHE_SIZE=500
UZPY_ANALYZER_CACHE_SIZE=250

# Use memory-efficient analyzer
uzpy run --edit src/ --ref . --analyzer jedi

# Process in chunks
# (Use custom script with chunked processing)
```

### Caching Issues

#### Issue: Stale cache entries

```
INFO: Using cached result, but code has changed
```

**Solutions**:

```bash
# Clear cache
uzpy cache clear

# Check cache status
uzpy cache stats

# Disable cache temporarily
uzpy run --edit src/ --ref . --no-cache

# Force cache refresh
rm -rf ~/.cache/uzpy/
```

#### Issue: Cache permission errors

```
ERROR: Cannot write to cache directory
```

**Solutions**:

```bash
# Fix cache directory permissions
chmod -R 755 ~/.cache/uzpy/

# Use alternative cache directory
export UZPY_CACHE_DIR=/tmp/uzpy-cache
mkdir -p $UZPY_CACHE_DIR

# Disable caching
export UZPY_USE_CACHE=false
```

### Configuration Issues

#### Issue: Configuration not loaded

```
WARNING: Configuration file .uzpy.env not found
```

**Debugging**:

```bash
# Check current directory
pwd
ls -la .uzpy.env

# Test with explicit config
uzpy run --config /path/to/config.env --edit src/ --ref .

# Check environment variables
env | grep UZPY_
```

**Solutions**:

```bash
# Create config file
cat > .uzpy.env << EOF
UZPY_EDIT_PATH=src/
UZPY_REF_PATH=.
UZPY_ANALYZER_TYPE=modern_hybrid
UZPY_USE_CACHE=true
EOF

# Use environment variables directly
export UZPY_EDIT_PATH=src/
export UZPY_REF_PATH=.
uzpy run
```

#### Issue: Invalid configuration values

```
ERROR: Invalid analyzer type: 'typo_analyzer'
```

**Valid values**:

```bash
# Valid analyzer types
UZPY_ANALYZER_TYPE=modern_hybrid  # Default
UZPY_ANALYZER_TYPE=hybrid
UZPY_ANALYZER_TYPE=jedi
UZPY_ANALYZER_TYPE=rope
UZPY_ANALYZER_TYPE=pyright
UZPY_ANALYZER_TYPE=ast_grep
UZPY_ANALYZER_TYPE=ruff

# Valid log levels
UZPY_LOG_LEVEL=DEBUG
UZPY_LOG_LEVEL=INFO     # Default
UZPY_LOG_LEVEL=WARNING
UZPY_LOG_LEVEL=ERROR
UZPY_LOG_LEVEL=CRITICAL
```

## Debugging Techniques

### Enable Detailed Logging

```bash
# Maximum verbosity
uzpy run --edit src/ --ref . --log-level DEBUG --verbose

# Component-specific logging
export UZPY_LOG_PARSER=DEBUG
export UZPY_LOG_ANALYZER=DEBUG
export UZPY_LOG_MODIFIER=INFO
```

### Test with Minimal Examples

Create minimal test cases to isolate issues:

```python
# minimal_test.py
from pathlib import Path

# Create minimal test files
test_dir = Path("test_minimal")
test_dir.mkdir(exist_ok=True)

# Simple source file
(test_dir / "source.py").write_text("""
def test_function():
    \"\"\"A test function.\"\"\"
    return 42
""")

# Simple usage file
(test_dir / "usage.py").write_text("""
from source import test_function

result = test_function()
""")

# Test uzpy on minimal example
from uzpy.pipeline import run_analysis_and_modification

results = run_analysis_and_modification(
    edit_path=test_dir / "source.py",
    ref_path=test_dir,
    dry_run=True,
    verbose=True
)

print(f"Results: {len(results)}")
for construct, refs in results.items():
    print(f"  {construct.name}: {len(refs)} references")
```

### Incremental Testing

Test components individually:

```python
# test_components.py
from pathlib import Path
from uzpy.discovery import FileDiscovery
from uzpy.parser import TreeSitterParser
from uzpy.analyzer import JediAnalyzer

def test_discovery():
    """Test file discovery."""
    discovery = FileDiscovery()
    files = discovery.discover_python_files([Path("src/")])
    print(f"Discovery: {len(files)} files")
    return files

def test_parsing(files):
    """Test parsing."""
    parser = TreeSitterParser()
    all_constructs = []
    
    for file_path in files[:5]:  # Test first 5 files
        try:
            constructs = parser.parse_file(file_path)
            all_constructs.extend(constructs)
            print(f"Parsed {file_path}: {len(constructs)} constructs")
        except Exception as e:
            print(f"Parse error {file_path}: {e}")
    
    return all_constructs

def test_analysis(constructs, search_paths):
    """Test analysis."""
    analyzer = JediAnalyzer()
    
    for construct in constructs[:3]:  # Test first 3 constructs
        try:
            refs = analyzer.find_references(construct, search_paths)
            print(f"Analyzed {construct.name}: {len(refs)} references")
        except Exception as e:
            print(f"Analysis error {construct.name}: {e}")

# Run incremental tests
files = test_discovery()
if files:
    constructs = test_parsing(files)
    if constructs:
        test_analysis(constructs, [Path(".")])
```

### Interactive Debugging

```python
# interactive_debug.py
import pdb
from uzpy.pipeline import run_analysis_and_modification
from pathlib import Path

def debug_analysis():
    """Interactive debugging session."""
    
    # Set breakpoint
    pdb.set_trace()
    
    # Run analysis step by step
    results = run_analysis_and_modification(
        edit_path=Path("src/"),
        ref_path=Path("."),
        dry_run=True
    )
    
    return results

# Run with debugger
debug_analysis()
```

## Error Recovery

### Automatic Recovery Strategies

```python
# recovery_strategies.py
from pathlib import Path
import shutil
from uzpy.pipeline import run_analysis_and_modification

class RecoveryManager:
    """Manage error recovery for uzpy operations."""
    
    def __init__(self, backup_dir: Path = Path("uzpy_backups")):
        self.backup_dir = backup_dir
        self.backup_dir.mkdir(exist_ok=True)
    
    def safe_analysis(self, edit_path: Path, ref_path: Path):
        """Run analysis with automatic recovery."""
        
        # Create backup
        backup_id = self._create_backup(edit_path)
        
        try:
            # Run analysis
            results = run_analysis_and_modification(
                edit_path=edit_path,
                ref_path=ref_path,
                safe_mode=True
            )
            
            print("Analysis completed successfully")
            return results
            
        except Exception as e:
            print(f"Analysis failed: {e}")
            
            # Attempt recovery
            self._recover_from_backup(backup_id)
            
            # Try with fallback settings
            return self._fallback_analysis(edit_path, ref_path)
    
    def _create_backup(self, edit_path: Path) -> str:
        """Create backup of files to be modified."""
        import time
        
        backup_id = f"backup_{int(time.time())}"
        backup_path = self.backup_dir / backup_id
        
        if edit_path.is_file():
            shutil.copy2(edit_path, backup_path)
        else:
            shutil.copytree(edit_path, backup_path)
        
        print(f"Created backup: {backup_path}")
        return backup_id
    
    def _recover_from_backup(self, backup_id: str):
        """Recover files from backup."""
        backup_path = self.backup_dir / backup_id
        
        if backup_path.exists():
            print(f"Recovering from backup: {backup_path}")
            # Recovery logic here
        else:
            print("No backup available for recovery")
    
    def _fallback_analysis(self, edit_path: Path, ref_path: Path):
        """Try analysis with fallback settings."""
        
        print("Attempting fallback analysis...")
        
        try:
            # Try with safest settings
            return run_analysis_and_modification(
                edit_path=edit_path,
                ref_path=ref_path,
                analyzer_type="jedi",
                use_cache=False,
                safe_mode=True,
                dry_run=True  # Don't modify files
            )
        except Exception as e:
            print(f"Fallback analysis also failed: {e}")
            return {}

# Usage
recovery = RecoveryManager()
results = recovery.safe_analysis(Path("src/"), Path("."))
```

### Manual Recovery

```bash
# Git-based recovery
git status
git diff  # See what uzpy changed
git checkout -- problematic_file.py  # Restore single file
git reset --hard HEAD  # Restore all files (CAREFUL!)

# Backup-based recovery (if enabled)
cp src/file.py.uzpy-backup src/file.py

# Incremental recovery
uzpy clean --edit src/  # Remove all "Used in:" sections
# Then re-run analysis with safer settings
```

## Getting Help

### Community Resources

1. **GitHub Issues**: [github.com/twardoch/uzpy/issues](https://github.com/twardoch/uzpy/issues)
2. **Documentation**: [Read the full documentation](https://twardoch.github.io/uzpy/)
3. **Discussions**: Use GitHub Discussions for questions

### Reporting Bugs

When reporting bugs, include:

```bash
# System information
uzpy --version
python --version
uname -a  # Linux/macOS
# or
systeminfo  # Windows

# Configuration
cat .uzpy.env
env | grep UZPY_

# Error reproduction
uzpy run --edit src/ --ref . --log-level DEBUG --verbose > uzpy_debug.log 2>&1
```

### Creating Minimal Reproducible Examples

```bash
# Create minimal test case
mkdir uzpy_bug_report
cd uzpy_bug_report

# Create minimal files that reproduce the issue
cat > src.py << EOF
def problem_function():
    """Function that causes issues."""
    pass
EOF

cat > usage.py << EOF
from src import problem_function
problem_function()
EOF

# Run uzpy with verbose output
uzpy run --edit src.py --ref . --verbose > bug_output.log 2>&1

# Include all files when reporting
tar -czf uzpy_bug_report.tar.gz src.py usage.py bug_output.log .uzpy.env
```

## Advanced Debugging

### Custom Debug Scripts

```python
# advanced_debug.py
import logging
from pathlib import Path
from uzpy.discovery import FileDiscovery
from uzpy.parser import TreeSitterParser
from uzpy.analyzer import ModernHybridAnalyzer

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('uzpy_debug.log'),
        logging.StreamHandler()
    ]
)

def comprehensive_debug(edit_path: Path, ref_path: Path):
    """Comprehensive debugging of uzpy components."""
    
    logger = logging.getLogger("uzpy_debug")
    
    # 1. Test discovery
    logger.info("=== TESTING DISCOVERY ===")
    discovery = FileDiscovery()
    
    try:
        edit_files = discovery.discover_python_files([edit_path])
        ref_files = discovery.discover_python_files([ref_path])
        logger.info(f"Edit files: {len(edit_files)}")
        logger.info(f"Ref files: {len(ref_files)}")
        
        for f in edit_files[:5]:
            logger.debug(f"Edit file: {f}")
            
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return
    
    # 2. Test parsing
    logger.info("=== TESTING PARSING ===")
    parser = TreeSitterParser()
    all_constructs = []
    
    for file_path in edit_files:
        try:
            constructs = parser.parse_file(file_path)
            all_constructs.extend(constructs)
            logger.debug(f"Parsed {file_path}: {len(constructs)} constructs")
            
            for c in constructs[:3]:  # Log first 3 constructs
                logger.debug(f"  Construct: {c.full_name} ({c.construct_type})")
                
        except Exception as e:
            logger.error(f"Parse error {file_path}: {e}")
    
    logger.info(f"Total constructs: {len(all_constructs)}")
    
    # 3. Test analysis
    logger.info("=== TESTING ANALYSIS ===")
    analyzer = ModernHybridAnalyzer()
    
    for construct in all_constructs[:10]:  # Test first 10 constructs
        try:
            logger.debug(f"Analyzing {construct.full_name}...")
            refs = analyzer.find_references(construct, ref_files)
            logger.info(f"  Found {len(refs)} references")
            
            for ref in refs[:3]:  # Log first 3 references
                logger.debug(f"    Ref: {ref.file_path}:{ref.line_number}")
                
        except Exception as e:
            logger.error(f"Analysis error {construct.full_name}: {e}")
    
    logger.info("=== DEBUG COMPLETE ===")

# Run comprehensive debug
comprehensive_debug(Path("src/"), Path("."))
```

This comprehensive troubleshooting guide should help you diagnose and fix most issues with uzpy. Remember to start with the most common solutions and gradually move to more advanced debugging techniques when needed.

## Summary

With this troubleshooting guide, you should be able to:

1. **Diagnose common issues** quickly using the provided solutions
2. **Debug complex problems** using systematic debugging techniques  
3. **Recover from errors** using backup and recovery strategies
4. **Get help** from the community when needed
5. **Report bugs effectively** with proper information

The uzpy documentation is now complete, covering everything from basic usage to advanced troubleshooting. Each chapter builds upon the previous ones to give you comprehensive knowledge of uzpy's capabilities and how to use them effectively.