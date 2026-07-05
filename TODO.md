# TODO

Flat list of pending work. See `TASKS.md` for detail.

## Follow-ups from the 2026-07-05 recovery

- [ ] Modernize the ast-grep backend: current code targets the removed
  `TreeSitterLang.Python` / `sgql.SGConfig` API, so `AstGrepAnalyzer` is inert.
  Port `find_usages` to the current `ast-grep-py` (`SgRoot(source, "python")`,
  `Config`) and re-enable it in the hybrid stack.
- [ ] Investigate cross-file usage detection: an end-to-end run reported
  "0/3 constructs" for an obviously-used function. Verify the pyright/ruff
  engines are wired into `ModernHybridAnalyzer.find_usages` (currently only ruff
  and the optional traditional fallback are invoked there).
- [ ] Add a benchmark for large codebases (1M+ lines) per the modernization plan.
- [ ] Move or delete the root-level `test_corruption_manual.py` (stray manual
  script; not collected by pytest).

## Standing guidance

Read `TASKS.md` and implement the changes and improvements. Don't remove existing
package integrations; add more as per `TASKS.md`.