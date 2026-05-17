# uzpy Modernization Analysis: Performance & Reliability Improvements

**NOTE: This document represents an initial user-provided proposal for modernizing uzpy. The actual implementation (as of latest commit) followed a refined, agent-generated plan that incorporated many of these ideas but also adapted them based on iterative development. See `CHANGELOG.md` and `README.md` for details on implemented features.**

---

After analyzing the actual uzpy codebase, here are concrete improvements using modern libraries available as of June 2025:

## Current Performance Bottlenecks (Addressed)

1.  **Sequential Processing**: Constructs analyzed one-by-one instead of parallel - **ADDRESSED** (via `ParallelAnalyzer`)
2.  **Rope Analyzer Overhead**: Accurate but slow for large codebases - **ADDRESSED** (via alternative modern analyzers like Pyright (CLI), ast-grep, and Ruff (CLI), orchestrated by `ModernHybridAnalyzer`)
3.  **No Caching**: Every run starts from scratch - **ADDRESSED** (via `CachedParser` and `CachedAnalyzer` using `diskcache`)
4.  **Limited Error Recovery**: Some analyzers fail hard instead of graceful degradation - **IMPROVED** (individual analyzers and pipeline have better error handling, though continuous improvement is ongoing)

## Phase 1: Performance Foundation (Implemented)

### Replace Core Analysis with Modern Tools (Partially Implemented as direct dependencies)

```python
# Add these dependencies: # DONE for diskcache, multiprocessing-logging. Ruff is dev dep, Pyright/ast-grep via CLI/bindings.
dependencies = [
    "ruff>=0.5.0",           # Rust-based analyzer, 100-1000x faster
    "pyright>=1.1.370",      # Fast cross-file analysis (replace Rope)
    "ast-grep>=0.21.0",      # Structural search tool
    "diskcache>=5.6.3",     # Persistent caching
    "multiprocessing-logging>=0.3.4",  # Parallel processing support
]
```

### Parallel Analysis Pipeline (Implemented as `ParallelAnalyzer`)

Replace the sequential construct analysis:
```python
# Current (sequential):
# for construct in constructs:
#     references = analyzer.find_usages(construct, ref_files)

# New (parallel): # Implemented with ParallelAnalyzer wrapping other analyzers
# from multiprocessing import Pool
# from functools import partial

# def analyze_construct_batch(constructs: list[Construct], ref_files: list[Path]) -> dict:
#     with Pool() as pool:
#         analyzer_func = partial(fast_analyzer.find_usages, ref_files=ref_files)
#         results = pool.map(analyzer_func, constructs)
#     return dict(zip(constructs, results))
```

### Caching Layer (Implemented as `CachedParser` and `CachedAnalyzer`)
```python
# import diskcache

# class CachedAnalyzer: # Implemented
#     def __init__(self, cache_dir: Path):
#         self.cache = diskcache.Cache(cache_dir)
        
#     def get_file_hash(self, file_path: Path) -> str:
#         # Hash file content + mtime for cache invalidation
#         stat = file_path.stat()
#         content_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
#         return f"{content_hash}:{stat.st_mtime}"
    
#     def cached_parse(self, file_path: Path) -> list[Construct]: # Implemented as CachedParser
#         cache_key = f"parse:{self.get_file_hash(file_path)}"
#         if cache_key in self.cache:
#             return self.cache[cache_key]
        
#         constructs = self.parser.parse_file(file_path)
#         self.cache[cache_key] = constructs
#         return constructs
```

## Phase 2: Analysis Modernization (Implemented with variations)

### Ruff Integration for Fast Basic Analysis (Implemented as `RuffAnalyzer` using CLI)
```python
# import subprocess
# import json

# class RuffAnalyzer: # Implemented
#     def find_imports_and_calls(self, file_path: Path) -> dict:
#         """Use Ruff's AST analysis for basic usage detection"""
#         result = subprocess.run([
#             "ruff", "check", "--select=F401,F811",
#             "--output-format=json", str(file_path)
#         ], capture_output=True, text=True)
        
#         return json.loads(result.stdout) if result.stdout else {}
```

### Pyright Integration (Replace Rope) (Implemented as `PyrightAnalyzer` using CLI)
```python
# class PyrightAnalyzer: # Implemented
#     def __init__(self, project_root: Path):
#         self.project_root = project_root
        
#     def find_references(self, construct: Construct) -> list[Reference]:
#         """Use Pyright's language server for accurate cross-file analysis"""
#         # Pyright provides much faster analysis than Rope
#         cmd = [
#             "pyright", "--outputjson",
#             f"--pythonpath={self.project_root}",
#             "--files", str(construct.file_path)
#         ]
        
#         result = subprocess.run(cmd, capture_output=True, text=True)
#         # Parse Pyright's JSON output for references
#         return self._parse_pyright_output(result.stdout)
```
**(Note: Actual Pyright CLI usage for reference finding is limited; current implementation reflects this.)**

### ast-grep for Structural Searches (Implemented as `AstGrepAnalyzer` using `ast-grep-py`)
```python
# class AstGrepAnalyzer: # Implemented
#     def find_usage_patterns(self, construct_name: str, search_paths: list[Path]) -> list[Reference]:
#         """Use ast-grep for intuitive pattern matching"""
#         patterns = [
#             f"$A.{construct_name}($$$)",      # Method calls
#             f"{construct_name}($$$)",         # Function calls
#             f"from $M import {construct_name}", # Imports
#         ]
        
#         references = []
#         for pattern in patterns:
#             cmd = ["ast-grep", "--lang=python", f"--pattern={pattern}"] + [str(p) for p in search_paths]
#             result = subprocess.run(cmd, capture_output=True, text=True)
#             references.extend(self._parse_ast_grep_output(result.stdout))
        
#         return references
```

## Phase 3: Modern CLI & Configuration (Implemented as `cli_modern.py`)

### Replace Fire with Typer + Rich + Pydantic (Done)
```python
# from typer import Typer
# from rich.console import Console
# from rich.progress import Progress
# from pydantic_settings import BaseSettings

# class UzpySettings(BaseSettings): # Implemented
#     edit_path: Path = Path.cwd()
#     ref_path: Optional[Path] = None
#     exclude_patterns: list[str] = []
#     parallel_workers: int = 4
#     cache_dir: Path = Path.home() / ".uzpy" / "cache"
    
#     class Config:
#         env_prefix = "UZPY_"
#         env_file = ".uzpy.env"

# app = Typer(name="uzpy", help="Modern Python usage tracker") # Implemented as uzpy-modern
# console = Console()

# @app.command()
# def run( # Implemented
#     edit: Path = typer.Option(Path.cwd(), help="Path to analyze"),
#     config_file: Optional[Path] = typer.Option(None, "--config", "-c"),
#     watch: bool = typer.Option(False, "--watch", "-w"),
#     workers: int = typer.Option(4, "--workers", "-j")
# ):
#     settings = UzpySettings(_env_file=config_file) if config_file else UzpySettings()
    
#     with Progress() as progress:
#         task = progress.add_task("Analyzing...", total=100)
#         # Modern progress tracking
```

### Watch Mode with File Monitoring (Implemented using `watchdog` in `cli_modern.py` and `watcher.py`)
```python
# from watchdog.observers import Observer
# from watchdog.events import FileSystemEventHandler

# class UzpyWatcher(FileSystemEventHandler): # Implemented
#     def __init__(self, analyzer: UzpyAnalyzer): # Signature differs, uses callback
#         self.analyzer = analyzer
        
#     def on_modified(self, event):
#         if event.src_path.endswith('.py'):
#             # Incremental reanalysis
#             self.analyzer.reanalyze_file(Path(event.src_path)) # Callback triggers re-analysis

# @app.command()
# def watch(path: Path = typer.Option(Path.cwd())): # Implemented
#     """Watch for file changes and update analysis in real-time"""
#     observer = Observer()
#     observer.schedule(UzpyWatcher(analyzer), str(path), recursive=True) # Orchestrated by WatcherOrchestrator
#     observer.start()
```

## Phase 4: Advanced Features (Not Implemented in this iteration)

### SQLite/DuckDB for Analytics (Not Implemented)
```python
# import duckdb
# ...
```

### Language Server Protocol Integration (Not Implemented)
```python
# Add LSP support for editor integration
# dependencies.append("pygls>=1.3.0") # Not added yet
# ...
```

## Dependency Updates (Partially Implemented)
```toml
# Modern dependencies for June 2025
# [project.dependencies]
# Core (keep existing)
# tree-sitter = ">=0.20.0"
# tree-sitter-python = ">=0.20.0"
# libcst = ">=1.0.0"

# Performance boosters # Implemented: diskcache, ast-grep-py (for ast-grep), multiprocessing-logging. Ruff/Pyright as CLI.
# ruff = ">=0.5.0"
# pyright = ">=1.1.370"
# ast-grep = ">=0.21.0" # Python binding is ast-grep-py
# diskcache = ">=5.6.3"

# Modern CLI # Implemented: typer, pydantic-settings, watchdog. Rich is indirect via Typer.
# typer = ">=0.12.0"
# rich = ">=13.7.0"
# pydantic-settings = ">=2.3.0"
# watchdog = ">=4.0.1"

# Analytics & Storage # Not implemented in this iteration
# duckdb = ">=0.10.0"
# sqlalchemy = ">=2.0.30"
# msgpack = ">=1.0.8"

# Optional advanced features # Not implemented in this iteration
# pygls = ">=1.3.0"
# ray = ">=2.9.0"
```
**(See `pyproject.toml` for actual dependencies added.)**

## Performance Expectations (Achieved to some extent, formal benchmarks pending)

- **10-100x faster** basic analysis with Ruff integration - (Ruff is fast, but its integration for *reference finding* is indirect)
- **3-5x faster** cross-file analysis replacing Rope with Pyright - (Pyright is fast, but CLI integration for *reference finding* is indirect)
- **5-10x faster** overall with parallel processing and caching - **Implemented and expected.**
- **Real-time updates** with watch mode - **Implemented (experimental).**
- **Better error recovery** with multiple analyzer fallbacks - **Improved.**

This modernization transforms uzpy from a basic tool into a high-performance code intelligence platform while maintaining backward compatibility and core functionality.
**(The implemented version adds these features alongside the existing ones, accessible via `uzpy-modern`.)**
