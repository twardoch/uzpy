---
# this_file: src_docs/md/08-performance-optimization.md
---

# Performance Optimization

This chapter covers techniques for optimizing uzpy's performance, especially for large codebases. Learn about caching strategies, parallel processing, analyzer selection, and system-level optimizations.

## Performance Overview

uzpy's performance depends on several factors:

- **Codebase size**: Number of files and lines of code
- **Construct density**: Functions/classes per file
- **Reference complexity**: How interconnected the code is
- **Analyzer choice**: Different analyzers have different performance characteristics
- **System resources**: CPU cores, memory, disk I/O

### Typical Performance Characteristics

| Codebase Size | Files | Constructs | Time (Cold) | Time (Cached) |
|---------------|-------|------------|-------------|---------------|
| Small | <100 | <500 | 5-15s | 1-3s |
| Medium | 100-1000 | 500-5000 | 30s-3m | 5-20s |
| Large | 1000-10000 | 5000-50000 | 3-15m | 30s-2m |
| Very Large | >10000 | >50000 | 15m+ | 2-10m |

## Caching Optimization

Caching is the most effective performance optimization for uzpy.

### Multi-Layer Caching Strategy

```python
# Optimal caching configuration
UZPY_USE_CACHE=true

# Parser cache (fastest hits)
UZPY_CACHE_PARSER_ENABLED=true
UZPY_PARSER_CACHE_SIZE=2000

# Analyzer cache (expensive operations)
UZPY_CACHE_ANALYZER_ENABLED=true
UZPY_ANALYZER_CACHE_SIZE=1000

# Cache compression for large results
UZPY_CACHE_COMPRESS=true

# Longer TTL for stable codebases
UZPY_CACHE_TTL=86400  # 24 hours
```

### Cache Warming

Pre-populate cache for faster subsequent runs:

```python
# cache_warming.py
from pathlib import Path
from uzpy.pipeline import run_analysis_and_modification

def warm_cache(project_root: Path):
    """Pre-populate uzpy cache for faster analysis."""
    
    print("Warming cache...")
    
    # Run analysis with caching enabled
    run_analysis_and_modification(
        edit_path=project_root / "src",
        ref_path=project_root,
        use_cache=True,
        dry_run=True,  # Don't modify files
        parallel=True   # Use all cores
    )
    
    print("Cache warmed successfully")

# Usage
warm_cache(Path("."))
```

### Intelligent Cache Invalidation

Optimize cache invalidation to minimize re-analysis:

```python
# smart_cache.py
from pathlib import Path
from typing import Set
import hashlib

class SmartCacheManager:
    """Intelligent cache management for incremental analysis."""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.file_hashes = {}
    
    def get_changed_files(self, project_root: Path) -> Set[Path]:
        """Get files that have changed since last analysis."""
        changed_files = set()
        
        for py_file in project_root.rglob("*.py"):
            current_hash = self._file_hash(py_file)
            cached_hash = self.file_hashes.get(py_file)
            
            if current_hash != cached_hash:
                changed_files.add(py_file)
                self.file_hashes[py_file] = current_hash
        
        return changed_files
    
    def _file_hash(self, file_path: Path) -> str:
        """Calculate file content hash."""
        return hashlib.md5(file_path.read_bytes()).hexdigest()
    
    def invalidate_related_cache(self, changed_files: Set[Path]):
        """Invalidate cache entries related to changed files."""
        # Implementation would invalidate analyzer cache for 
        # constructs that might be affected by file changes
        pass

# Usage for incremental analysis
def incremental_analysis(project_root: Path):
    """Run analysis only on changed files."""
    
    cache_manager = SmartCacheManager(Path("~/.cache/uzpy"))
    changed_files = cache_manager.get_changed_files(project_root)
    
    if not changed_files:
        print("No files changed, skipping analysis")
        return
    
    print(f"Analyzing {len(changed_files)} changed files")
    
    # Invalidate related cache entries
    cache_manager.invalidate_related_cache(changed_files)
    
    # Run analysis only on changed files
    run_analysis_and_modification(
        edit_path=list(changed_files),
        ref_path=project_root,
        use_cache=True
    )
```

## Parallel Processing Optimization

Leverage multi-core systems for faster analysis.

### Optimal Parallel Configuration

```python
# Parallel processing settings
UZPY_PARALLEL_ENABLED=true

# Use most CPU cores, leave 1-2 for system
UZPY_PARALLEL_MAX_WORKERS=6  # For 8-core system

# Optimize chunk size for your data
UZPY_PARALLEL_CHUNK_SIZE=20

# Increase timeout for parallel operations
UZPY_PARALLEL_TIMEOUT=600  # 10 minutes
```

### Custom Parallel Strategy

```python
# parallel_optimizer.py
import multiprocessing as mp
from pathlib import Path
from typing import List, Tuple
from uzpy.types import Construct, Reference
from uzpy.analyzer.base import BaseAnalyzer

class OptimizedParallelAnalyzer:
    """Optimized parallel analysis with smart work distribution."""
    
    def __init__(self, base_analyzer: BaseAnalyzer, max_workers: int = None):
        self.base_analyzer = base_analyzer
        self.max_workers = max_workers or mp.cpu_count() - 1
    
    def analyze_constructs(
        self, 
        constructs: List[Construct], 
        search_paths: List[Path]
    ) -> dict[Construct, List[Reference]]:
        """Analyze constructs in parallel with optimized batching."""
        
        # Group constructs by complexity for balanced work distribution
        batches = self._create_balanced_batches(constructs)
        
        with mp.Pool(self.max_workers) as pool:
            # Process batches in parallel
            batch_results = pool.starmap(
                self._analyze_batch,
                [(batch, search_paths) for batch in batches]
            )
        
        # Merge results
        results = {}
        for batch_result in batch_results:
            results.update(batch_result)
        
        return results
    
    def _create_balanced_batches(
        self, 
        constructs: List[Construct]
    ) -> List[List[Construct]]:
        """Create balanced batches based on estimated complexity."""
        
        # Estimate complexity (simple heuristic)
        construct_complexity = []
        for construct in constructs:
            complexity = self._estimate_complexity(construct)
            construct_complexity.append((construct, complexity))
        
        # Sort by complexity (descending)
        construct_complexity.sort(key=lambda x: x[1], reverse=True)
        
        # Distribute into balanced batches
        batches = [[] for _ in range(self.max_workers)]
        batch_loads = [0] * self.max_workers
        
        for construct, complexity in construct_complexity:
            # Add to least loaded batch
            min_batch_idx = batch_loads.index(min(batch_loads))
            batches[min_batch_idx].append(construct)
            batch_loads[min_batch_idx] += complexity
        
        return [batch for batch in batches if batch]  # Remove empty batches
    
    def _estimate_complexity(self, construct: Construct) -> int:
        """Estimate analysis complexity for a construct."""
        complexity = 1
        
        # More complex for classes (have methods)
        if construct.construct_type == "class":
            complexity *= 3
        
        # More complex for common names (more potential matches)
        if len(construct.name) < 5:
            complexity *= 2
        
        return complexity
    
    def _analyze_batch(
        self, 
        batch: List[Construct], 
        search_paths: List[Path]
    ) -> dict[Construct, List[Reference]]:
        """Analyze a batch of constructs."""
        results = {}
        
        for construct in batch:
            try:
                references = self.base_analyzer.find_references(
                    construct, search_paths
                )
                results[construct] = references
            except Exception as e:
                print(f"Error analyzing {construct.full_name}: {e}")
                results[construct] = []
        
        return results
```

### Memory-Efficient Parallel Processing

```python
# memory_efficient_parallel.py
from pathlib import Path
from typing import Iterator, List
from uzpy.types import Construct

class MemoryEfficientProcessor:
    """Process large numbers of constructs without memory issues."""
    
    def __init__(self, chunk_size: int = 100):
        self.chunk_size = chunk_size
    
    def process_in_chunks(
        self, 
        constructs: List[Construct], 
        search_paths: List[Path]
    ) -> Iterator[dict[Construct, List[Reference]]]:
        """Process constructs in memory-efficient chunks."""
        
        for i in range(0, len(constructs), self.chunk_size):
            chunk = constructs[i:i + self.chunk_size]
            
            # Process chunk
            chunk_results = self._process_chunk(chunk, search_paths)
            
            yield chunk_results
            
            # Force garbage collection between chunks
            import gc
            gc.collect()
    
    def _process_chunk(
        self, 
        chunk: List[Construct], 
        search_paths: List[Path]
    ) -> dict[Construct, List[Reference]]:
        """Process a single chunk of constructs."""
        
        from uzpy.analyzer import ModernHybridAnalyzer
        analyzer = ModernHybridAnalyzer()
        
        results = {}
        for construct in chunk:
            references = analyzer.find_references(construct, search_paths)
            results[construct] = references
        
        return results

# Usage for very large codebases
def process_large_codebase(constructs: List[Construct], search_paths: List[Path]):
    """Process very large codebase efficiently."""
    
    processor = MemoryEfficientProcessor(chunk_size=50)
    all_results = {}
    
    for chunk_results in processor.process_in_chunks(constructs, search_paths):
        all_results.update(chunk_results)
        
        # Optional: save intermediate results
        print(f"Processed {len(all_results)} constructs so far...")
    
    return all_results
```

## Analyzer Selection Optimization

Choose the right analyzer for your performance needs.

### Performance Comparison

| Analyzer | Speed | Accuracy | Memory | Best For |
|----------|-------|----------|--------|----------|
| `ruff` | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | Quick checks, CI |
| `jedi` | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Large codebases |
| `ast_grep` | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | Pattern matching |
| `rope` | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | Thorough analysis |
| `pyright` | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | Type-heavy code |
| `modern_hybrid` | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | General purpose |

### Adaptive Analyzer Selection

```python
# adaptive_analyzer.py
from pathlib import Path
from uzpy.analyzer import (
    JediAnalyzer, 
    RopeAnalyzer, 
    ModernHybridAnalyzer
)

class AdaptiveAnalyzer:
    """Choose analyzer based on codebase characteristics."""
    
    def __init__(self):
        self.file_count_threshold = 1000
        self.construct_count_threshold = 5000
    
    def select_analyzer(
        self, 
        file_paths: List[Path], 
        construct_count: int
    ) -> BaseAnalyzer:
        """Select optimal analyzer based on codebase size."""
        
        file_count = len(file_paths)
        
        # For very large codebases, use fastest analyzer
        if (file_count > self.file_count_threshold or 
            construct_count > self.construct_count_threshold):
            print("Large codebase detected, using Jedi analyzer")
            return JediAnalyzer()
        
        # For medium codebases, use hybrid
        elif file_count > 100 or construct_count > 500:
            print("Medium codebase detected, using Modern Hybrid analyzer")
            return ModernHybridAnalyzer()
        
        # For small codebases, use thorough analysis
        else:
            print("Small codebase detected, using Rope analyzer")
            return RopeAnalyzer()

# Usage
def optimized_analysis(edit_paths: List[Path], ref_paths: List[Path]):
    """Run analysis with optimal analyzer selection."""
    
    from uzpy.discovery import FileDiscovery
    from uzpy.parser import CachedParser, TreeSitterParser
    
    # Discover files and constructs
    discovery = FileDiscovery()
    files = discovery.discover_python_files(edit_paths)
    
    parser = CachedParser(TreeSitterParser())
    all_constructs = []
    for file_path in files:
        constructs = parser.parse_file(file_path)
        all_constructs.extend(constructs)
    
    # Select optimal analyzer
    adaptive = AdaptiveAnalyzer()
    analyzer = adaptive.select_analyzer(files, len(all_constructs))
    
    # Run analysis
    results = {}
    for construct in all_constructs:
        references = analyzer.find_references(construct, ref_paths)
        results[construct] = references
    
    return results
```

### Tiered Analysis Strategy

```python
# tiered_analysis.py
from uzpy.analyzer import JediAnalyzer, RopeAnalyzer

class TieredAnalyzer:
    """Use fast analyzer first, fall back to thorough analyzer."""
    
    def __init__(self):
        self.fast_analyzer = JediAnalyzer()
        self.thorough_analyzer = RopeAnalyzer()
        self.min_references_threshold = 1
    
    def find_references(
        self, 
        construct: Construct, 
        search_paths: List[Path]
    ) -> List[Reference]:
        """Use tiered analysis strategy."""
        
        # Try fast analyzer first
        fast_refs = self.fast_analyzer.find_references(construct, search_paths)
        
        # If we found enough references, use fast results
        if len(fast_refs) >= self.min_references_threshold:
            return fast_refs
        
        # Otherwise, use thorough analyzer
        print(f"Using thorough analysis for {construct.name}")
        thorough_refs = self.thorough_analyzer.find_references(construct, search_paths)
        
        # Merge results (fast + thorough)
        all_refs = fast_refs + thorough_refs
        return self._deduplicate_references(all_refs)
    
    def _deduplicate_references(self, references: List[Reference]) -> List[Reference]:
        """Remove duplicate references."""
        seen = set()
        unique_refs = []
        
        for ref in references:
            key = (ref.file_path, ref.line_number)
            if key not in seen:
                seen.add(key)
                unique_refs.append(ref)
        
        return unique_refs
```

## File System Optimization

Optimize file system operations for better performance.

### Exclusion Pattern Optimization

```python
# Optimize exclusion patterns for speed
UZPY_EXCLUDE_PATTERNS=\
**/__pycache__/**,\
**/.git/**,\
**/venv/**,\
**/env/**,\
**/.venv/**,\
**/node_modules/**,\
**/build/**,\
**/dist/**,\
**/*.pyc,\
**/*.pyo,\
**/*.so,\
**/migrations/**,\
**/static/**,\
**/media/**

# Use more specific patterns to reduce filesystem traversal
# Good: src/migrations/** 
# Bad: **/migrations/**
```

### SSD and I/O Optimization

```python
# io_optimization.py
from pathlib import Path
import asyncio
import aiofiles

class AsyncFileProcessor:
    """Asynchronous file processing for better I/O performance."""
    
    async def read_files_async(self, file_paths: List[Path]) -> dict[Path, str]:
        """Read multiple files asynchronously."""
        
        async def read_file(file_path: Path) -> Tuple[Path, str]:
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    return file_path, content
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                return file_path, ""
        
        # Read all files concurrently
        tasks = [read_file(path) for path in file_paths]
        results = await asyncio.gather(*tasks)
        
        return dict(results)

# Usage for I/O bound operations
async def fast_file_processing(file_paths: List[Path]):
    """Process files with optimized I/O."""
    
    processor = AsyncFileProcessor()
    file_contents = await processor.read_files_async(file_paths)
    
    # Process contents
    for file_path, content in file_contents.items():
        # Your processing logic here
        pass
```

## Memory Optimization

Manage memory usage for large codebases.

### Memory-Efficient Data Structures

```python
# memory_optimization.py
from typing import Iterator
import sys

class MemoryEfficientAnalysis:
    """Memory-optimized analysis for very large codebases."""
    
    def __init__(self, max_memory_mb: int = 1024):
        self.max_memory_mb = max_memory_mb
        self.current_memory_mb = 0
    
    def analyze_with_memory_limit(
        self, 
        constructs: List[Construct], 
        search_paths: List[Path]
    ) -> Iterator[Tuple[Construct, List[Reference]]]:
        """Analyze constructs with memory limits."""
        
        for construct in constructs:
            # Check memory usage
            if self._get_memory_usage() > self.max_memory_mb:
                print("Memory limit reached, garbage collecting...")
                self._force_gc()
            
            # Analyze single construct
            references = self._analyze_single_construct(construct, search_paths)
            
            yield construct, references
    
    def _get_memory_usage(self) -> int:
        """Get current memory usage in MB."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        return process.memory_info().rss // (1024 * 1024)
    
    def _force_gc(self):
        """Force garbage collection and clear caches."""
        import gc
        
        # Clear internal caches
        self._clear_internal_caches()
        
        # Force garbage collection
        gc.collect()
    
    def _clear_internal_caches(self):
        """Clear internal caches to free memory."""
        # Clear parser caches, analyzer caches, etc.
        pass
    
    def _analyze_single_construct(
        self, 
        construct: Construct, 
        search_paths: List[Path]
    ) -> List[Reference]:
        """Analyze single construct with minimal memory footprint."""
        
        from uzpy.analyzer import JediAnalyzer
        
        # Use lightweight analyzer
        analyzer = JediAnalyzer()
        references = analyzer.find_references(construct, search_paths)
        
        # Clear analyzer to free memory
        del analyzer
        
        return references

# Usage for memory-constrained environments
def memory_efficient_analysis(constructs: List[Construct], search_paths: List[Path]):
    """Run analysis with memory constraints."""
    
    analyzer = MemoryEfficientAnalysis(max_memory_mb=512)
    results = {}
    
    for construct, references in analyzer.analyze_with_memory_limit(constructs, search_paths):
        if references:
            results[construct] = references
        
        # Optional: save intermediate results to disk
        if len(results) % 100 == 0:
            print(f"Processed {len(results)} constructs")
    
    return results
```

## Profiling and Monitoring

Monitor and profile uzpy performance to identify bottlenecks.

### Performance Profiling

```python
# performance_profiler.py
import time
import cProfile
import pstats
from pathlib import Path

class UzpyProfiler:
    """Profile uzpy performance to identify bottlenecks."""
    
    def profile_analysis(self, edit_path: Path, ref_path: Path):
        """Profile full analysis with detailed statistics."""
        
        profiler = cProfile.Profile()
        
        # Start profiling
        profiler.enable()
        
        # Run analysis
        from uzpy.pipeline import run_analysis_and_modification
        results = run_analysis_and_modification(
            edit_path=edit_path,
            ref_path=ref_path,
            use_cache=True
        )
        
        # Stop profiling
        profiler.disable()
        
        # Analyze results
        stats = pstats.Stats(profiler)
        stats.sort_stats('cumulative')
        
        print("Top 20 functions by cumulative time:")
        stats.print_stats(20)
        
        # Save detailed profile
        stats.dump_stats('uzpy_profile.prof')
        
        return results
    
    def time_components(self, edit_path: Path, ref_path: Path):
        """Time individual components."""
        
        from uzpy.discovery import FileDiscovery
        from uzpy.parser import CachedParser, TreeSitterParser
        from uzpy.analyzer import ModernHybridAnalyzer
        
        timings = {}
        
        # Time discovery
        start = time.time()
        discovery = FileDiscovery()
        edit_files = discovery.discover_python_files([edit_path])
        ref_files = discovery.discover_python_files([ref_path])
        timings['discovery'] = time.time() - start
        
        # Time parsing
        start = time.time()
        parser = CachedParser(TreeSitterParser())
        all_constructs = []
        for file_path in edit_files:
            constructs = parser.parse_file(file_path)
            all_constructs.extend(constructs)
        timings['parsing'] = time.time() - start
        
        # Time analysis
        start = time.time()
        analyzer = ModernHybridAnalyzer()
        results = {}
        for construct in all_constructs[:10]:  # Sample first 10
            references = analyzer.find_references(construct, ref_files)
            results[construct] = references
        timings['analysis'] = time.time() - start
        
        # Print timings
        for component, duration in timings.items():
            print(f"{component}: {duration:.2f}s")
        
        return timings

# Usage
profiler = UzpyProfiler()
profiler.profile_analysis(Path("src/"), Path("."))
profiler.time_components(Path("src/"), Path("."))
```

### Real-time Monitoring

```python
# monitoring.py
import time
import psutil
import threading
from pathlib import Path

class PerformanceMonitor:
    """Monitor uzpy performance in real-time."""
    
    def __init__(self):
        self.monitoring = False
        self.stats = {
            'cpu_percent': [],
            'memory_mb': [],
            'disk_io': []
        }
    
    def start_monitoring(self):
        """Start performance monitoring in background thread."""
        self.monitoring = True
        thread = threading.Thread(target=self._monitor_loop)
        thread.daemon = True
        thread.start()
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        self._print_summary()
    
    def _monitor_loop(self):
        """Monitor system resources in background."""
        process = psutil.Process()
        
        while self.monitoring:
            # Collect metrics
            cpu_percent = process.cpu_percent()
            memory_mb = process.memory_info().rss // (1024 * 1024)
            disk_io = process.io_counters()
            
            self.stats['cpu_percent'].append(cpu_percent)
            self.stats['memory_mb'].append(memory_mb)
            self.stats['disk_io'].append(disk_io.read_bytes + disk_io.write_bytes)
            
            time.sleep(1)  # Sample every second
    
    def _print_summary(self):
        """Print monitoring summary."""
        if not self.stats['cpu_percent']:
            return
        
        print("\nPerformance Summary:")
        print(f"  CPU: avg {sum(self.stats['cpu_percent'])/len(self.stats['cpu_percent']):.1f}%, "
              f"max {max(self.stats['cpu_percent']):.1f}%")
        print(f"  Memory: avg {sum(self.stats['memory_mb'])/len(self.stats['memory_mb']):.0f}MB, "
              f"max {max(self.stats['memory_mb']):.0f}MB")
        
        disk_io_mb = [io / (1024*1024) for io in self.stats['disk_io']]
        print(f"  Disk I/O: {sum(disk_io_mb):.1f}MB total")

# Usage with context manager
class MonitoredAnalysis:
    """Context manager for monitored analysis."""
    
    def __init__(self):
        self.monitor = PerformanceMonitor()
    
    def __enter__(self):
        self.monitor.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monitor.stop_monitoring()

# Usage
with MonitoredAnalysis():
    results = run_analysis_and_modification(
        edit_path=Path("src/"),
        ref_path=Path("."),
        parallel=True
    )
```

## System-Level Optimization

Optimize the entire system for uzpy performance.

### Environment Tuning

```bash
# System optimization for uzpy

# 1. Increase file descriptor limits
ulimit -n 8192

# 2. Use faster Python implementation (if available)
# PyPy can be significantly faster for CPU-intensive operations

# 3. SSD optimization
# Ensure project files are on SSD storage

# 4. Disable unnecessary services during analysis
# Stop antivirus real-time scanning for project directory

# 5. Set CPU governor to performance mode (Linux)
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

### Docker Optimization

```dockerfile
# Dockerfile for optimized uzpy environment
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uzpy with performance dependencies
RUN pip install --no-cache-dir uzpy[all]

# Optimize Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Increase memory limits
ENV UZPY_MAX_MEMORY_MB=2048
ENV UZPY_CACHE_MAX_MEMORY_MB=1024

# Enable parallel processing
ENV UZPY_PARALLEL_ENABLED=true
ENV UZPY_PARALLEL_MAX_WORKERS=4

# Set working directory
WORKDIR /workspace

# Run uzpy
CMD ["uzpy", "run", "--edit", "src/", "--ref", ".", "--parallel"]
```

## Best Practices Summary

### For Small Projects (<100 files)
- Use default settings
- Enable all analyzers for accuracy
- Cache is helpful but not critical

### For Medium Projects (100-1000 files)
- Enable caching
- Use `modern_hybrid` analyzer
- Consider parallel processing
- Optimize exclusion patterns

### For Large Projects (1000+ files)
- Mandatory caching with large cache sizes
- Use `jedi` analyzer for speed
- Enable parallel processing with many workers
- Aggressive exclusion patterns
- Consider incremental analysis

### For Very Large Projects (10000+ files)
- Custom analyzer selection based on file patterns
- Memory-efficient processing with chunking
- Asynchronous I/O operations
- Distributed processing (if available)
- Continuous monitoring and profiling

## Next Steps

With optimized performance:

1. **[Troubleshoot remaining issues](09-troubleshooting.md)** when things don't work as expected
2. **Monitor production usage** to identify new optimization opportunities
3. **Share optimization strategies** with the uzpy community

The final chapter covers troubleshooting common issues and debugging techniques.