# Objective 1

<objective>
`whereused` is a Python tool that:

- Takes an --edit path (to a `.py` file or folder; searches recursively for `.py` files)
- Optionally takes a --ref path (same format as --edit); defaults to --edit if not provided

The tool scans both codebases and, for each construct (module, function, class, method) in the edit codebase, adds a list of paths relative to the ref folder showing where that construct is used.

Results are written into docstrings with the prefix `Used in:`, appended to existing docstrings or created as new ones if none exist.
</objective>

# Task 1

<task>
Research and report on tools, libraries, and resources for implementing the objective.

Output the report to `/Users/adam/Developer/llm/2505a/whereused/02research.md`
</task>