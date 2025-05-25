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



# Research 1

## AST Parsing and Docstring Extraction Libraries

* **Python `ast` module (built-in)** – The built-in `ast` module can parse Python source code into an Abstract Syntax Tree, providing access to nodes for functions, classes, etc. This is a foundation for static analysis in Python. Python 3.9 introduced `ast.unparse` to convert an AST back to source code, enabling programmatic code modifications (though this may lose original formatting). The AST is useful for locating definitions and their docstring nodes (the first `ast.Expr` in a function/class body). However, bare AST does not retain comments or exact formatting.

* **Parsers for All Python Versions** – Tools like **`typed_ast`** (now part of `ast` for Python 3.8+) and **`gast`** provide version-agnostic AST parsing. `gast` in particular is used alongside libraries like Beniget to create a unified AST across Python versions. Another parser is **Parso**, the parsing library behind Jedi, which can handle multiple Python versions and even incomplete code. These parsers can extract code structure without executing it, which is essential for this static analysis use-case.

* **Griffe** – *Griffe* is a library focused on **extracting the structure and signatures of an entire Python codebase**. It traverses the AST to build a model of modules, classes, functions, and their docstrings. Griffe can be used to collect all definitions (with docstrings) in a project, which aligns with the “--edit” codebase parsing. It’s intended for documentation and API analysis, and thus can serve to gather constructs and existing docstrings in the code.

## Static Analysis Tools for Finding Symbol Usages

* **Rope** – *Rope* is a Python **refactoring library** that includes features for finding occurrences of names across a codebase. It can statically resolve imports and names to support renaming and other refactorings. In particular, `rope.contrib.findit.find_occurrences()` can find all references to a given function, method, or variable in a project. Rope builds an internal index of the project’s modules and abstracts the Python AST into an object model, which helps it achieve accurate cross-module searches. This makes Rope a strong candidate for locating where a construct is used (similar to IDE “find usages”). *Note:* Rope can also apply the changes (e.g. renaming or adding text to docstrings) while preserving code format to a reasonable extent, since it operates with minimal diffs.

* **Jedi** – *Jedi* is a static analysis and auto-completion library typically used in editors. It has a rich understanding of Python code and can **find references** to definitions. Jedi’s API includes a `Script.get_references()` method that returns all usage locations of a given name (definition). Jedi can resolve imports, handle scopes, and infer types to a degree, giving it high accuracy in identifying where functions or classes are used. It focuses on **“goto definition” and “find references”** functionality. For the `whereused` tool, Jedi could be leveraged to retrieve all references of each symbol defined in the `--edit` codebase within the `--ref` codebase.

* **astroid (Pylint’s AST)** – *astroid* is the AST framework powering Pylint, with support for name resolution and inference. It can be used to walk code, resolve imports, and find where names are used or defined. While astroid doesn’t have a single “find references” call, it provides the building blocks (like scoped name lookup and inference) to track usage of a symbol. It’s useful for building a custom static analyzer that needs to handle Python’s dynamic features (imports, attributes, etc.) in a static way.

* **Beniget (Def-Use Chains)** – *Beniget* analyzes an AST to produce **definition-use chains**. It maps definitions to their uses and vice versa, within a given module’s AST. Using Beniget on each module of the `--ref` codebase can help link every `Name` usage back to the function or class definition it refers to. Beniget works across all Python 3 versions (via gast) and can provide a precise mapping of where each defined symbol is used. This is highly relevant for implementing the “Used in: \[files]” lists, as it directly computes use-def relationships.

* **Call Graph Generators** – Tools like *Pyan* and *PyCG* construct call graphs, effectively identifying which functions call which others (and where). **Pyan** performs a static analysis of Python code to build a directed graph of objects and how they **define or use each other**. It parses the codebase and can output a graph (Graphviz, etc.), but its underlying analysis (though “rather superficial”) can be used to list function usages. **PyCG** is a more advanced, research-based tool that generates call graphs with higher precision and scalability. It handles dynamic features (higher-order functions, imported modules discovery, etc.) and could be used to find usage of functions across modules. These tools demonstrate approaches to static inter-procedural analysis; their algorithms or code could be repurposed to detect usages for `whereused`.

* **Vulture** – *Vulture* finds unused code by static analysis, essentially the complement of `whereused`. It scans a codebase to detect functions and classes that are never referenced. While its goal is identifying dead code, the underlying mechanism is to collect all defined symbols and all used symbols, then report those defined and not used. This means Vulture internally must detect usages of symbols. Its approach (fast static scanning with heuristics) could inform a strategy for `whereused` (for example, using a simple index of names); however, Vulture might not resolve *which* `func()` is being called if names clash. It’s a useful reference for a lightweight static usage analysis.

## Code Indexing and Search Libraries

* **Whoosh (Full-Text Indexing)** – *Whoosh* is a pure-Python full-text indexing library. It allows building an index of text (or code) and querying it efficiently. For a large codebase, one strategy is to index all source files such that each identifier can be quickly searched. For example, you could index tokens or lines and then search for occurrences of a function name. Whoosh supports fielded search, so you might index “identifier: X in file Y” and query for a particular X. This can narrow down candidate files where a symbol appears, which you then filter with AST analysis for true positives. Using an index can improve performance when scanning many files for references.

* **ctags/Etags** – *Universal Ctags* can generate tag files for Python, which list where each class, function, and variable is defined. While ctags mainly indexes definitions, it can be combined with text search to find usages. Some Python-specific enhancers (like **python-ctags** bindings) allow querying the index. In a `whereused` scenario, one could use ctags to map definitions to files, and then perform keyword searches in those files for the symbol’s usage (noting this is textual and may need AST confirmation). Ctags provides a quick way to jump to definitions and could be part of a larger system for cross-referencing symbols.

* **Language Server Protocol (LSP) Implementations** – Python LSP servers (e.g. Microsoft’s *Pyright* or *pylance*, and *python-lsp-server* which uses Jedi) internally maintain an index of the project’s symbols and their locations to provide “Find All References” in editors. While not a library per se, they illustrate architectures that could be mimicked: on project load, parse all files, build a symbol table (mapping each definition to a list of usage locations). For instance, Jedi’s use in an LSP indexes modules so that references can be found quickly across a codebase. Drawing inspiration from these, one could implement a custom indexing scheme for `whereused` that caches symbol definitions and uses.

* **Grepping and Code Search Tools** – Simpler approaches involve using tools like grep, Ack, or ripgrep to scan for occurrences of symbol names. This can be done programmatically (e.g., Python’s `glob` + file reading + regex). While this is quick and easy, it can produce false positives (matches in comments, or different symbols with the same name). It’s best combined with a parsing step. An indexed search (like Whoosh) is essentially an optimized grep. For high accuracy, any search hits should be verified by parsing that file and checking the identifier in context (ensuring it’s a real usage of the target construct, not just a coincidental substring).

## Code Rewriting and Docstring Modification Tools

* **LibCST (Concrete Syntax Tree)** – *LibCST* provides a concrete syntax tree for Python, meaning it parses source code into a tree while **preserving all formatting and comments**. This is ideal for safely modifying code. One can locate a function or class node, then modify its docstring node (which appears as a `SimpleStatementLine` containing a `SimpleString`). LibCST ensures that when you re-export the code, the only changes are the ones you intended – formatting (indentation, spacing) and unrelated code remain untouched. LibCST also includes a **codemod framework** for bulk transformations. For example, one could write a LibCST transformer that finds all FunctionDef/ClassDef in the edit set and appends a bullet to the docstring. Using LibCST would guarantee minimal disruption to the code style.

* **RedBaron (Full Syntax Tree)** – *RedBaron* is built on the Baron parser and represents code as a **Full Syntax Tree (FST)**. Like LibCST, it keeps all original formatting (including whitespace and comments). RedBaron makes it convenient to navigate and modify the code; for instance, you can access `node.value` for a function’s docstring and simply concatenate a new string to it. It was explicitly designed to allow source code modifications with formatting preserved. RedBaron doesn’t perform static analysis itself, but it can be combined with static analysis tools (e.g., using Rope or astroid to find where to make changes, then RedBaron to apply them). For the `whereused` tool, RedBaron could parse the file from `--edit`, and you could then programmatically insert the “Used in…” lines into the docstring nodes.

* **Bowler (Refactoring Toolkit)** – *Bowler* is a refactoring framework from Facebook, originally built on `lib2to3`/Fissix and now moving toward LibCST. It provides a fluent API to select code patterns and modify them. Bowler could be leveraged to insert text into docstrings by writing a custom modification rule. It is designed for large-scale code modifications and ensures the code remains valid after changes. While Bowler’s typical use is things like renaming symbols or fixing syntax, its infrastructure (parsing, applying changes, and an interactive diff tool) could be useful if `whereused` needed to handle many insertions at once in an interactive or reviewable way.

* **AST-to-Code Tools** – If preserving formatting is less of a concern (the question notes we don’t mind docstring style nuances), one could use `ast` in combination with code-generation tools like **`astor`** or the built-in `ast.unparse`. These will regenerate source code from an AST. After using static analysis to determine usages, one approach is: parse the `--edit` file with `ast`, modify the AST nodes’ docstring values (for example, append the usage list to the string literal node), and then unparse it back to code. This will produce correct Python code with the updated docstrings. However, the downside is that original formatting (like exact indentation or quotation style of docstrings) may be altered. Still, it’s a straightforward method if consistency of style is not critical. The **Green Tree Snakes** documentation and others confirm that Python’s AST can be manipulated and then compiled back to source.

* **Rope (for rewriting)** – In addition to finding occurrences, Rope can apply changes to code as part of its refactoring operations. For instance, a rename refactoring will rewrite all references. Rope’s knowledge of the codebase can be repurposed: one could theoretically use Rope’s core to insert text into docstrings for each definition and let it handle the file writing. This might be overkill for simply appending text, but Rope’s ability to **organize imports, preserve formatting, and perform cross-file changes** safely is proven. It could serve as an all-in-one solution: find occurrences and modify files accordingly.

## Related Projects and References

When designing `whereused`, it’s useful to study similar projects:

* **IDEs and LSPs** – IDEs like PyCharm and VS Code have *“Find Usages”* features for Python. These likely use sophisticated static analysis (type inference, etc.) plus indexing. While their implementations aren’t libraries, understanding that our goal is achievable (and the performance tricks they use, like pre-indexing symbols) can guide the choice of libraries above (e.g., using Jedi or building a custom index).

* **Documentation Tools** – Tools such as *Sphinx* with the autodoc or autoapi extensions parse code to generate documentation. *Sphinx-AutoAPI* in particular can scan a codebase and produce an object model of it (somewhat like Griffe). Though they don’t track “where used,” they illustrate robust parsing of code structure, which is the first step of `whereused`. Similarly, *pydoctor* (used in Twisted) builds a code model including which classes/functions are referenced in docstrings. These could be a source of inspiration for parsing and handling multiple files and packages.

* **Code Search Engines** – Projects like *Sourcegraph* or *OpenGrok* enable searching across huge codebases, and they often include language-specific analyzers. For Python, Sourcegraph’s search may use a combination of ctags and text search. While not directly applicable as libraries, they emphasize scalability. If `whereused` needs to run on large projects, using an indexing approach (as noted above) is essential for speed. We might incorporate a lightweight version of this by using Whoosh or SQLite FTS to cache symbol locations.

* **Testing on Large Codebases** – Finally, any chosen approach should be tested on a sizeable codebase to ensure it’s both accurate and performant. For example, using LibCST to parse every file might be slower than using the built-in ast (LibCST trades speed for accuracy in parsing). A hybrid approach could be considered: use simple text search to gather candidate usages, then verify with a fast AST parse (built-in ast) of those files. Balancing these tools will be key to meet the goal of *high accuracy without sacrificing performance*.

Each tool above brings something to the table for implementing `whereused`. By combining **AST parsing** (to get definitions and modify docstrings), **static analysis** (to find where each symbol is used), and **code rewrite libraries** (to insert usage info without breaking code style), one can create a robust utility. The resources cited (documentation and repositories) provide further insight into usage and integration of these libraries in the `whereused` implementation.

**Sources:**

* Python AST library documentation; LibCST overview; RedBaron docs; Griffe documentation.
* Rope documentation and StackOverflow reference for find\_occurrences; Jedi documentation (references); Astroid docs; Beniget README.
* Pyan README; PyCG repository README; Vulture README.
* Whoosh documentation and project info; Universal Ctags info.
* Bowler README and notes on LibCST vs lib2to3; Green Tree Snakes (AST manipulation) guide.

# Research 2

The development of a Python code analysis tool that tracks where constructs are used across codebases requires careful selection of libraries and implementation strategies. Based on extensive research into existing tools and technologies, this report provides detailed recommendations for building your "whereused" tool with optimal performance and accuracy.

## Core Technology Stack Recommendations

### **Primary AST Parser: Tree-sitter Python**

Tree-sitter emerges as the **best overall choice** for the whereused tool based on several critical advantages:

- **Incremental parsing** allows efficient re-analysis when files change (100x faster updates)
- **Error recovery** continues parsing despite syntax errors, crucial for real-world codebases
- **High performance** at 15,000-20,000 lines/second initial parsing
- **Powerful query system** using S-expressions for pattern matching
- **Low memory footprint** with streaming capabilities

The combination of speed, error tolerance, and incremental updates makes Tree-sitter ideal for a tool that needs to continuously track references across potentially large and evolving codebases.

### **Symbol Tracking: Hybrid Approach with Rope and Jedi**

For cross-file reference tracking, combining **Rope** for accuracy with **Jedi** for performance provides the most comprehensive solution:

**Rope** excels at:
- Precise cross-file reference finding with `find_occurrences()` API
- Proper handling of Python's complex import systems
- Inheritance hierarchy tracking
- Confidence scoring for matches

**Jedi** complements with:
- Fast symbol resolution optimized for interactive use
- Excellent caching mechanisms
- Project-wide search capabilities
- Better handling of large codebases

### **Code Modification: LibCST**

For modifying docstrings while preserving formatting, **LibCST** stands out as the clear winner:

- **100% lossless formatting preservation** - critical for maintaining code review friendliness
- **Type-safe API** with full mypy support
- **Proven at scale** by Instagram/Meta
- **Robust handling** of edge cases like missing docstrings or different quote styles

## Implementation Architecture

### Phase-Based Pipeline Design

Based on successful patterns from tools like Snakefood and Pydeps, implement a three-phase pipeline:

```python
class WhereusedPipeline:
    def __init__(self, edit_path, ref_path):
        self.parser = TreeSitterParser()
        self.analyzer = HybridReferenceAnalyzer(rope_project, jedi_project)
        self.modifier = LibCSTDocstringModifier()
    
    def run(self):
        # Phase 1: Parse and index all constructs
        edit_constructs = self.parser.extract_definitions(edit_path)
        ref_index = self.parser.build_reference_index(ref_path)
        
        # Phase 2: Find cross-references
        usage_map = self.analyzer.find_all_usages(edit_constructs, ref_index)
        
        # Phase 3: Modify source files
        self.modifier.add_usage_comments(edit_path, usage_map)
```

### Efficient Cross-Reference Storage

Use a hybrid data structure combining inverted indices with graph representations:

```python
class ReferenceIndex:
    def __init__(self):
        # Fast symbol lookup
        self.symbol_to_definitions = {}  # symbol_name -> [(file, line, type)]
        self.file_to_symbols = {}        # file_path -> set(symbols)
        
        # Graph representation for complex queries
        self.dependency_graph = igraph.Graph(directed=True)
        
        # Incremental update tracking
        self.file_checksums = {}
        self.last_modified = {}
```

## Critical Implementation Details

### Handling Python's Dynamic Features

The research reveals that perfect static analysis of Python is impossible, but practical accuracy is achievable through:

1. **Conservative analysis** - Over-report potential usages rather than miss them
2. **Confidence scoring** - Mark uncertain references (e.g., getattr usage) with lower confidence
3. **Import resolution** - Use Rope's proven algorithms for handling relative imports, star imports, and dynamic imports
4. **Scope tracking** - Combine AST with Python's symtable module for accurate scope resolution

### Performance Optimization Strategy

For large codebases, implement these proven optimizations:

1. **Incremental analysis** using Tree-sitter's capabilities
2. **Parallel file processing** with multiprocessing.Pool
3. **Smart caching** of parsed ASTs with timestamp-based invalidation
4. **Memory-efficient streaming** for files over 10,000 lines

```python
class IncrementalAnalyzer:
    def analyze_with_cache(self, file_path):
        cache_key = self._get_cache_key(file_path)
        if cache_key in self.ast_cache:
            return self.ast_cache[cache_key]
        
        # Use Tree-sitter for parsing
        tree = self.parser.parse_file(file_path)
        self.ast_cache[cache_key] = tree
        return tree
```

### Symbol Resolution Best Practices

Combine multiple approaches for maximum accuracy:

1. **Primary resolution** through Tree-sitter queries:
```python
function_call_query = language.query("""
(call
  function: [
    (identifier) @function_name
    (attribute attribute: (identifier) @method_name)
  ]
)
""")
```

2. **Fallback to Rope** for complex cases involving inheritance or dynamic dispatch
3. **Jedi integration** for real-time updates during development

## Specialized Libraries for Specific Requirements

### File System Traversal

Use **pathlib** with **gitignore_parser** for respecting ignore patterns:
```python
from pathlib import Path
import fnmatch

def find_python_files(root, patterns=['.git', '__pycache__', '*.pyc']):
    for path in Path(root).rglob('*.py'):
        if not any(fnmatch.fnmatch(str(path), p) for p in patterns):
            yield path
```

### Dependency Graph Visualization

For understanding complex relationships, integrate **igraph** for analysis and **GraphViz** for visualization:
- igraph handles graphs with millions of nodes efficiently
- GraphViz produces readable visual output with automatic layout

### Error Handling and Robustness

Implement graceful degradation based on patterns from production tools:
```python
def safe_analyze(file_path):
    try:
        tree = parser.parse_file(file_path)
        return analyze_tree(tree)
    except SyntaxError:
        # Fall back to text-based analysis
        return analyze_with_regex(file_path)
    except Exception as e:
        logging.warning(f"Failed to analyze {file_path}: {e}")
        return {'error': str(e), 'partial_results': []}
```

## Performance Benchmarks and Expectations

Based on empirical data from similar tools:

- **Initial analysis**: 5,000-10,000 lines/second (with caching)
- **Incremental updates**: Near-instantaneous for single file changes
- **Memory usage**: ~1GB per 100,000 lines of code analyzed
- **Accuracy**: 95%+ for static imports, 70-80% for dynamic features

## Integration with Development Workflows

Consider implementing:

1. **Watch mode** using the `watchdog` library for real-time updates
2. **Language Server Protocol** support for IDE integration
3. **CI/CD hooks** for automated documentation updates
4. **Configuration files** supporting `.whereused.toml` for project-specific settings

## Conclusion and Implementation Roadmap

The whereused tool can achieve production-quality results by combining:

1. **Tree-sitter** for fast, error-tolerant parsing
2. **Rope + Jedi** for accurate cross-file reference tracking  
3. **LibCST** for safe code modification
4. **Proven architectural patterns** from tools like Pydeps and Snakefood

Start with a minimal viable product focusing on function and class tracking, then progressively add support for methods, variables, and more complex Python constructs. The modular architecture allows incremental feature development while maintaining performance and accuracy.