# TODO

## High Priority Tasks

- [ ] Complete CLI integration with hybrid analyzer to find references  
  - Replace "Analyzer implementation in progress..." placeholder in cli.py:137
  - Integrate HybridAnalyzer to find where constructs are used
  - Process analysis results and prepare for modification

- [ ] Implement docstring modification using LibCST modifier
  - Create modifier implementation in modifier/ directory
  - Update docstrings with usage information
  - Preserve code formatting and style

## Medium Priority Tasks

- [ ] Add progress reporting and summary statistics for analysis
  - Show progress bars during reference finding
  - Display analysis results in rich tables
  - Report modifications made and files changed

- [ ] Add error handling and fallback mechanisms for analysis failures
  - Handle analyzer errors gracefully
  - Provide detailed error messages
  - Continue processing when possible

## Testing and Validation

- [ ] Test analyzer integration with various Python codebases
- [ ] Validate docstring modifications preserve formatting
- [ ] Test dry-run mode functionality
- [ ] Add comprehensive test coverage

## Current Status

The foundation is complete:
- ✅ File discovery with gitignore support
- ✅ Tree-sitter parser for construct extraction 
- ✅ Hybrid analyzer (Rope + Jedi) implementation
- ✅ CLI interface with rich formatting
- ❌ **Missing**: CLI integration with analyzer (line 137 in cli.py)
- ❌ **Missing**: LibCST modifier for docstring updates

## Test Command

```bash
python -m uzpy -e src/uzpy/
```