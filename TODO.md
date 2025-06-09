# TODO

✅ **COMPLETELY FIXED**: Exclusion patterns now work correctly at all levels!

The issue had **three** parts that needed to be fixed:

## 1. File Discovery Pattern Matching Bug
- **Problem**: The `_is_excluded` method in `discovery.py` was using absolute paths instead of relative paths for pattern matching with pathspec
- **Fix**: 
  - Store root_path in FileDiscovery during `find_python_files`
  - Convert paths to relative paths before pattern matching  
  - Support both simple patterns (`_private`) and glob patterns (`_private/**`)

## 2. CLI Reference File Discovery Bug
- **Problem**: The `run()` method was creating a new `FileDiscovery` instance without passing exclusion patterns when getting reference files for the analyzer (line 182)
- **Fix**: Pass `self.xclude_patterns` to the FileDiscovery instance for reference files

## 3. Rope Analyzer Internal Discovery Bug
- **Problem**: Rope's `Project` class internally discovers and analyzes ALL files in the project directory, regardless of the files we pass to `find_usages()`
- **Fix**: 
  - Modified `RopeAnalyzer` to accept `exclude_patterns` parameter
  - Configure Rope's `ignored_resources` preference to exclude `_private*` patterns
  - Pass exclusion patterns from CLI → HybridAnalyzer → RopeAnalyzer

## Changes Made:
- **discovery.py**: Fixed relative path pattern matching
- **cli.py**: Pass exclusion patterns to reference file discovery AND analyzer
- **rope_analyzer.py**: Accept and use exclusion patterns for Rope project initialization
- **hybrid_analyzer.py**: Pass exclusion patterns to RopeAnalyzer

## Result:
The command now works correctly without any `_private` directory analysis:
```bash
uzpy run -e "/Users/adam/Developer/vcs/github.twardoch/pub/twat-packages/_good/twat/plugins/repos" -x _private,.venv
```

Tests added to verify all levels of exclusion work in `tests/test_discovery.py`.