import ast
from pathlib import Path


def test_production_package_does_not_import_pytest():
    package_root = Path(__file__).parents[1] / "repoatlas"
    offenders = []

    for source_path in package_root.rglob("*.py"):
        tree = ast.parse(source_path.read_text(encoding="utf-8"))

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_names = [node.module]
            else:
                continue

            if any(name == "pytest" or name.startswith("pytest.") for name in imported_names):
                offenders.append(source_path.relative_to(package_root).as_posix())

    assert offenders == []
