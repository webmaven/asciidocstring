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
We target **Python 3.14+** and **Pyodide (WASM) 314.0+**.
* Do **NOT** add any dependencies with native C/C++ compiled extensions.
* Ensure all code runs flawlessly in WASM environments.

### Rule 3: Linting & Typing Standards
Keep the codebase strictly clean and typed:
* Run Ruff: `venv/bin/ruff check src/ tests/`
* Run MyPy: `venv/bin/mypy src/`

---

## 2. Core Architecture

The library processes Python docstrings written in AsciiDoc using a decoupled, two-stage architecture:

1. **Parser & Cleaning Layer (`src/asciidocstring/document.py`):**
   * Uses `inspect.cleandoc` to calculate and strip common leading whitespace from docstrings.
   * Parses the cleaned text into an Abstract Semantic Graph (ASG) using `asciidoctrine.lark_parser.parse_to_ast()`.

2. **AST Processing & Visitors Layer (`src/asciidocstring/visitors.py`):**
   * Subclasses `asciidoctrine.nodes.NodeVisitor`.
   * For docstring rendering, serializes the AST to reStructuredText (`ReSTSerializerVisitor`).
   * For doctests, queries and extracts executable code blocks (`TestBlockExtractorVisitor`).

---

## 3. Reference Commands

```bash
# Set up environment
python3 -m venv venv
venv/bin/pip install -e .

# Run test suite
PYTHONPATH=src venv/bin/pytest

# Run static quality checks
venv/bin/ruff check src/ tests/
mypy src/
```

---

## 4. Known Upstream Limitations & Parser Details

* **Bare-URL Autolinks (Issue [#76](https://github.com/webmaven/asciidoctrine/issues/76)):** `asciidoctrine` does not yet parse bare URLs (such as `https://google.com` without bracketed labels) as `Ref` nodes; they are currently parsed as plain `Text` nodes. Use bracketed links `https://google.com[Google]` where explicit translation is required.


---

## 5. Pre-Release Checklist

Before building, packaging, or uploading a new release to PyPI, every agent MUST execute the following checklist:

1. [ ] **Verify Version String**: Check `src/asciidocstring/__init__.py` and ensure `__version__` has been correctly bumped (e.g., `"0.1.0a2"`).
2. [ ] **Verify Quality Standards**: Run linting and static analysis checks to guarantee no quality errors exist:
   ```bash
   venv/bin/ruff check src/ tests/ && venv/bin/mypy src/
   ```
3. [ ] **Measure Coverage**: Run the test suite and verify coverage does not regress from our **99%** baseline:
   ```bash
   PYTHONPATH=src venv/bin/pytest --cov=src --cov-report=term-missing
   ```
4. [ ] **Update Changelog**: Ensure [CHANGELOG.adoc](file:///Users/michaelbernstein/Documents/GitHub/asciidocstring/CHANGELOG.adoc) is fully updated, listing all newly added, fixed, or modified features.
5. [ ] **Verify Upstream Constraints**: Double-check that [pyproject.toml](file:///Users/michaelbernstein/Documents/GitHub/asciidocstring/pyproject.toml)'s minimum constraints on upstream packages (such as `asciidoctrine`) are correctly set.
6. [ ] **Build Verification**: Run `hatch build` locally and ensure the source distribution (`.tar.gz`) and wheel (`.whl`) are successfully built with no package definition errors.
7. [ ] **PyPI Sanity Check**: Verify that the targeted version doesn't conflict with any active (non-yanked) versions on PyPI.


