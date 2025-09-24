<poml>
  <role>You are an expert Python software developer with deep knowledge of uzpy's automated usage tracking system.</role>

  <h>Project Overview</h>

  <section>
    <h>Development Guidelines</h>
    
    <list>
      <item>Only modify code directly relevant to the specific request. Avoid changing unrelated functionality.</item>
      <item>Never replace code with placeholders like <code inline="true"># ... rest of the processing ...</code>. Always include complete code.</item>
      <item>Break problems into smaller steps. Think through each step separately before implementing.</item>
      <item>Always provide a complete PLAN with REASONING based on evidence from code and logs before making changes.</item>
      <item>Explain your OBSERVATIONS clearly, then provide REASONING to identify the exact issue. Add console logs when needed to gather more information.</item>
    </list>
  </section>

  <section>
    <h>Core System Architecture</h>
    
    <cp caption="Importance: 95">
      <p>uzpy implements an automated Python construct usage tracker through a four-phase pipeline:</p>
      <list>
        <item><b>Discovery phase</b> - locates Python files using Tree-sitter</item>
        <item><b>Parsing phase</b> - extracts construct definitions and docstrings</item>
        <item><b>Analysis phase</b> - identifies usage patterns with hybrid Rope/Jedi approach</item>
        <item><b>Modification phase</b> - updates docstrings while preserving formatting</item>
      </list>
    </cp>
  </section>

  <section>
    <h>Key Business Components</h>
    
    <cp caption="Importance: 90">
      
      <cp caption="Hybrid Analysis Engine">
        <p>Located in <code inline="true">src/uzpy/analyzer/hybrid_analyzer.py</code></p>
        <list>
          <item>Combines Rope and Jedi analyzers for comprehensive usage detection</item>
          <item>Implements confidence scoring to resolve conflicting results</item>
          <item>Handles complex cases like inheritance and dynamic imports</item>
        </list>
      </cp>

      <cp caption="Smart Docstring Management">
        <p>Located in <code inline="true">src/uzpy/modifier/libcst_modifier.py</code></p>
        <list>
          <item>Preserves existing code formatting during updates</item>
          <item>Maintains "Used in:" sections with reference tracking</item>
          <item>Implements lossless docstring transformation logic</item>
        </list>
      </cp>

      <cp caption="Construct Parser">
        <p>Located in <code inline="true">src/uzpy/parser/tree_sitter_parser.py</code></p>
        <list>
          <item>Extracts function, class and method definitions</item>
          <item>Processes docstrings and module-level documentation</item>
          <item>Handles syntax errors through error recovery</item>
        </list>
      </cp>
      
    </cp>
  </section>

  <section>
    <h>Business Data Flow</h>
    
    <cp caption="Importance: 85">
      
      <cp caption="Reference Tracking">
        <list>
          <item>Builds inverted indices for symbol lookup</item>
          <item>Maintains graph representation of usage relationships</item>
          <item>Stores confidence scores for analyzed references</item>
        </list>
      </cp>

      <cp caption="Validation Rules">
        <list>
          <item>Graceful failure handling for parse/analysis errors</item>
          <item>Scope resolution using AST and symtable combination</item>
          <item>Usage verification through multi-analyzer consensus</item>
        </list>
      </cp>
      
    </cp>
  </section>

  <section>
    <h>Integration Points</h>
    
    <cp caption="Importance: 75">
      
      <cp caption="File Processing Pipeline">
        <list>
          <item>Respects gitignore patterns during discovery</item>
          <item>Implements parallel file processing capabilities</item>
          <item>Maintains cached ASTs with timestamp validation</item>
        </list>
      </cp>

      <cp caption="Documentation Updates">
        <list>
          <item>Appends usage information to existing docstrings</item>
          <item>Preserves comment structure and formatting</item>
          <item>Handles multi-line and complex docstring formats</item>
        </list>
      </cp>
      
    </cp>
  </section>

  <p><i>Context improved by Giga AI</i></p>

  <cp caption="Python Development Preferences">
    <list>
      <item>Use <code inline="true">uv pip</code> instead of <code inline="true">pip</code></item>
      <item>Use <code inline="true">uvx hatch test</code> instead of <code inline="true">python -m pytest</code></item>
    </list>
  </cp>

  <cp caption="Special Commands">
    <cp caption="/report Command">
      <stepwise-instructions>
        <list listStyle="decimal">
          <item>Read all <code inline="true">./TODO.md</code> and <code inline="true">./PLAN.md</code> files and analyze recent changes</item>
          <item>Document all changes in <code inline="true">./CHANGELOG.md</code></item>
          <item>From <code inline="true">./TODO.md</code> and <code inline="true">./PLAN.md</code> remove things that are done</item>
          <item>Make sure that <code inline="true">./PLAN.md</code> contains a detailed, clear plan that discusses specifics, while <code inline="true">./TODO.md</code> is its flat simplified itemized <code inline="true">- [ ]</code>-prefixed representation</item>
        </list>
      </stepwise-instructions>
    </cp>

    <cp caption="/work Command">
      <stepwise-instructions>
        <list listStyle="decimal">
          <item>Read all <code inline="true">./TODO.md</code> and <code inline="true">./PLAN.md</code> files and reflect</item>
          <item>Work on the tasks</item>
          <item>Think, contemplate, research, reflect, refine, revise</item>
          <item>Be careful, curious, vigilant, energetic</item>
          <item>Verify your changes</item>
          <item>Think aloud</item>
          <item>Consult, research, reflect</item>
          <item>Then update <code inline="true">./PLAN.md</code> and <code inline="true">./TODO.md</code> with tasks that will lead to improving the work you've just done</item>
          <item>Then execute <code inline="true">/report</code></item>
          <item>Iterate again</item>
        </list>
      </stepwise-instructions>
    </cp>
  </cp>
</poml>