# Objective 1

<objective>
`whereused` is supposed to be a Python tool that: 

- takes an --edit path (to a `.py` file, or to a folder which the tool will recursively search for `.py` files). 
- optionally takes a --ref path (to a `.py` file, or to a folder which the tool will recursively search for `.py` files); if not provided, --ref is the same as --edit

The tool then scans the ref codebase and the edit codebase. For each construct (module, function, class and method) in the edit codebase, the tool adds a list of paths relative to the ref folder, so that each path indicates one file in which the given construct is used.

The tool writes the list, prefixed with `Used in:`, into docstring of the given construct (at the end of the existing docstring, or as the new docstring if the construct has no docstring).
</objective>

# Task 1

<task>
Perform extensive research report on the objective. Collect all tools, libraries and other resources that can be used to implement the objective.

Print the report into `/Users/adam/Developer/llm/2505a/whereused/02research.md`
</task>
