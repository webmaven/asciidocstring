# Agent Rules & Repository Guide: `asciidocstring`

Welcome, fellow agent! This file contains critical context, guidelines, and rules for working with this repository.

---

## 1. Development Rules

### Rule 1: Strict Red / Green TDD
Always write focused, failing tests first in the `tests/` directory before writing or editing production code.
* Verify the **RED** stage by running `PYTHONPATH=src venv/bin/pytest tests/`.
* Write the minimum code required to go **GREEN**.
* Keep the test suite passing throughout.

### Rule 2: Pure Python and Portability
We target **Python 3.10+** and **Pyodide (WASM) 314.0+**.
* Do **NOT** add any dependencies with native C/C++ compiled extensions.
* Ensure all code runs flawlessly in WASM environments.

### Rule 3: Linting & Typing Standards
Keep the codebase strictly clean and typed:
* Run Ruff: `venv/bin/ruff check src/ tests/`
* Run MyPy: `venv/bin/mypy src/`

---

## 2. Core Architecture

The library processes Python docstrings written in AsciiDoc using a decoupled, multi-layer architecture:

1. **Parser & Cleaning Layer (`src/asciidocstring/document.py`):**
   * Uses `inspect.cleandoc` to calculate and strip common leading whitespace from docstrings.
   * Parses the cleaned text into an Abstract Semantic Graph (ASG) using `asciidoctrine.lark_parser.parse_to_ast()`.

2. **AST Processing & Visitors Layer (`src/asciidocstring/visitors.py`):**
   * Subclasses `asciidoctrine.nodes.NodeVisitor`.
   * For docstring rendering, serializes the AST to reStructuredText (`ReSTSerializerVisitor`).
   * For doctests, queries and extracts executable code blocks (`TestBlockExtractorVisitor`).

3. **Semantic Models & Extractor Layer (`src/asciidocstring/semantics.py`, `src/asciidocstring/models.py`):**
   * Subclasses `NodeVisitor` (`SemanticExtractorVisitor`) to traverse the ASG and populate structured semantic dataclasses (`DocstringParam`, `DocstringReturn`, `DocstringYield`, `DocstringRaise`, `DocstringReceive`, `DocstringWarn`, `DocstringAttribute`, `DocstringDeprecated`, `DocstringExample`).
   * Automatically extracts and normalizes parameter types, default values, optional markers, return annotations, and deprecation details.

4. **Griffe Bridge Layer (`src/asciidocstring/griffe_bridge.py`):**
   * Ingests and converts Griffe docstring representations across Google, NumPy, and Sphinx docstring conventions into AsciiDoc markup (`to_asciidoc`) and `AsciiDocStringDocument` instances (`from_griffe`, `from_sections`).

---

## 3. Reference Commands

```bash
# Set up environment
python3 -m venv venv
venv/bin/pip install -e ".[test,lint,griffe]"

# Run test suite
PYTHONPATH=src venv/bin/pytest

# Run static quality checks
venv/bin/ruff check src/ tests/
mypy src/
```

---

## 4. Known Upstream Limitations & Parser Details

* **Bare-URL Autolinks (Issue [#76](https://github.com/webmaven/asciidoctrine/issues/76)):** Resolved in `asciidoctrine>=0.1.0a11`. Bare URLs (such as `https://google.com`) are now correctly parsed as `Ref` nodes and rendered as proper reST hyperlinks.
* **Consecutive Attributed Description Lists (Issue [#96](https://github.com/webmaven/asciidoctrine/issues/96)):** Resolved in `asciidoctrine>=0.2.0a2`. Consecutive description lists with distinct block attributes (e.g. `[parameters]`, `[returns]`) are now parsed as distinct `DescriptionList` blocks in the AST and retain their attributes.
* **Mid-identifier Emphasis Boundary (Issue [#97](https://github.com/webmaven/asciidoctrine/issues/97)):** Resolved in `asciidoctrine>=0.2.0a3`. Identifiers containing underscores (e.g. `some_function_name`) no longer incorrectly trigger constrained inline emphasis, preventing identifiers from being fragmented into text and emphasis AST nodes.
* **Memoized Parser Engine (asciidoctrine 0.2.0a3):** Implemented in `asciidoctrine>=0.2.0a3`. Compiled `Lark` parser instances are now cached across `parse_to_ast` calls, yielding a **~33x speedup** on repeated and batch docstring parsing.
* **Verbatim Block Table Cell Protection (Issue [#116](https://github.com/webmaven/asciidoctrine/issues/116)):** Resolved in `asciidoctrine>=0.2.0a4`. Verbatim blocks (`Listing`, `Literal`, `Passthrough`, `Comment`) containing table delimiters (`|===`) or cell pipes no longer break into invalid table nodes.
* **Inline Monospace Backtick Boundary (Issue [#117](https://github.com/webmaven/asciidoctrine/issues/117)):** Resolved in `asciidoctrine>=0.2.0a4`. Multiple inline code spans (`` `hook_0`, `hook_1`, `hook_2`, `hook_3` ``) on a single line no longer invert span grouping.
* **Block Title Attachment Preceded by Another Block (Issue [#119](https://github.com/webmaven/asciidoctrine/issues/119)):** Resolved in `asciidoctrine>=0.2.0a5`. Block title lines (`.Title`) preceded by another block are now correctly attached to subsequent blocks (listings, admonitions, tables) rather than being parsed as standalone paragraphs.
* **Inline Macros Attached to Preceding Words/Punctuation (Issue [#120](https://github.com/webmaven/asciidoctrine/issues/120)):** Resolved in `asciidoctrine>=0.2.0a5`. Inline macros (`footnote:[...]`, `kbd:[...]`, `pass:[...]`, URI schemes) attached directly to preceding text without whitespace (e.g. `statement.footnote:[Note text]`) now parse correctly.
* **Human-Readable Diagnostics & Graceful XRef Resolution (Feature [#78](https://github.com/webmaven/asciidoctrine/issues/78)):** Resolved in `asciidoctrine>=0.2.0a6`. Lark tokens in syntax errors are translated to human-readable names; unresolved cross-references accumulate warnings instead of raising unhandled `KeyError`.
* **Block Title Whitespace Ambiguity with Dot Lists (Issue [#122](https://github.com/webmaven/asciidoctrine/issues/122)):** Resolved in `asciidoctrine>=0.2.0a6`. Enforces non-whitespace immediately following the dot in block titles (`.Title`), preventing `. item` ordered list lines from being consumed as block titles.
* **Inline Formatting Backslash Escaping (Feature [#113](https://github.com/webmaven/asciidoctrine/issues/113)):** Resolved in `asciidoctrine>=0.2.0a7`. Backslash-escaped inline formatting delimiters (`\*bold*`, `\_italic_`, `\`code\``, `\\__func__`) suppress span creation and emit delimiter characters as plain text.
* **Hanging-Indented List Item Continuation Lines (Issue [#125](https://github.com/webmaven/asciidoctrine/issues/125)):** Resolved in `asciidoctrine>=0.2.0a7`. Contiguous indented lines following list items without blank lines are folded into the list item's principal text, preventing spurious indented literal blocks and keeping lists intact.



---

## 5. Pre-Release Checklist

Before building, packaging, or uploading a new release to PyPI, every agent MUST execute the following checklist:

1. [ ] **Verify Version String**: Check `src/asciidocstring/__init__.py` and ensure `__version__` has been correctly bumped (e.g., `"0.1.0a2"`).
2. [ ] **Verify Quality Standards**: Run linting and static analysis checks to guarantee no quality errors exist:
   ```bash
   venv/bin/ruff check src/ tests/ && venv/bin/mypy src/
   ```
3. [ ] **Measure Coverage**: Run the test suite and verify coverage does not regress from our **100%** baseline:
   ```bash
   PYTHONPATH=src venv/bin/pytest --cov=src --cov-report=term-missing
   ```
4. [ ] **Update Changelog**: Ensure [CHANGELOG.adoc](file:///Users/michaelbernstein/Documents/GitHub/asciidocstring/CHANGELOG.adoc) is fully updated, listing all newly added, fixed, or modified features.
5. [ ] **Verify Upstream Constraints**: Double-check that [pyproject.toml](file:///Users/michaelbernstein/Documents/GitHub/asciidocstring/pyproject.toml)'s minimum constraints on upstream packages (such as `asciidoctrine`) are correctly set.
6. [ ] **Build Verification**: Run `hatch build` locally and ensure the source distribution (`.tar.gz`) and wheel (`.whl`) are successfully built with no package definition errors.
7. [ ] **PyPI Sanity Check**: Verify that the targeted version doesn't conflict with any active (non-yanked) versions on PyPI.


