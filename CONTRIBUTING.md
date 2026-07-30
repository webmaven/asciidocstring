# Contributing to AsciiDocstring

Thank you for considering contributing to **AsciiDocstring**! We welcome bug reports, feature requests, documentation improvements, and code contributions.

---

## 1. Development Setup

AsciiDocstring requires Python 3.14+ and follows strict pure-Python portability rules (zero native C/C++ compiled extensions).

```bash
# 1. Clone the repository
git clone https://github.com/webmaven/asciidocstring.git
cd asciidocstring

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install the package in editable mode with development dependencies
pip install -e ".[test,lint]"
```

---

## 2. Development Workflow: Red / Green TDD

We follow strict **Test-Driven Development (TDD)**:

1. Write a focused, failing unit test in `tests/` before touching production code.
2. Run `PYTHONPATH=src pytest` to confirm the test fails (**RED** stage).
3. Write the minimum production code in `src/asciidocstring/` to make the test pass (**GREEN** stage).
4. Refactor as necessary, maintaining 100% test passing and high coverage standards.

---

## 3. Code Quality Standards

Before submitting a Pull Request, ensure all quality checks pass cleanly:

```bash
# Run pytest with coverage tracking
PYTHONPATH=src pytest --cov=src --cov-report=term-missing

# Run Ruff formatting & quality checks
ruff check src/ tests/

# Run MyPy type-safety validation
mypy src/
```

---

## 4. Pull Request Checklist

When opening a Pull Request, please ensure:

- [ ] All tests pass without warnings or errors.
- [ ] New functionality is covered by unit tests.
- [ ] Code is fully type-annotated (`mypy src/` passes in strict mode).
- [ ] `CHANGELOG.adoc` has been updated with a brief description of your changes under `[Unreleased]`.
