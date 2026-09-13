# Contributing to RepoMosaic

Thanks for helping improve RepoMosaic.

## Local setup

Create and activate a Python 3.11+ virtual environment, then install the project:

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Run the complete test suite before submitting a change:

```bash
python -m pytest
```

## Development guidelines

- Add or update tests for every behavior change.
- Include focused parser tests when changing the core AST parser.
- Do not commit `__pycache__`, `.pyc` files, virtual environments, or API keys.
- Keep generated output and unrelated formatting changes out of focused pull requests.
