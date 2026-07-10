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
   * Dynamically appends a trailing `\n` to inputs to avoid `lark.exceptions.UnexpectedEOF` (required by `asciidoctrine`).
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
venv/bin/mypy src/
```
