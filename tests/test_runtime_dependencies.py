import ast
from pathlib import Path
import tomllib


def test_production_package_does_not_import_pytest():
    package_root = Path(__file__).parents[1] / "repomosaic"
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


def test_keyring_is_a_normal_runtime_dependency():
    project_root = Path(__file__).parents[1]
    metadata = tomllib.loads(
        (project_root / "pyproject.toml").read_text(encoding="utf-8")
    )

    dependencies = metadata["project"]["dependencies"]
    assert any(dependency.startswith("keyring") for dependency in dependencies)


def test_distribution_and_console_scripts_use_repomosaic_identity():
    project_root = Path(__file__).parents[1]
    metadata = tomllib.loads(
        (project_root / "pyproject.toml").read_text(encoding="utf-8")
    )

    assert metadata["project"]["name"] == "repomosaic"
    assert metadata["project"]["scripts"] == {
        "repomosaic": "repomosaic.cli:main",
        "repomosaic-mcp": "repomosaic.mcp_server:main",
    }
