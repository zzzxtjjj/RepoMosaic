import json

from repoatlas.symbols import ClassInfo, FileInfo, FunctionInfo, RepositoryInfo
from repoatlas.visualizer import (
    build_vscode_uri,
    export_repository_json,
    render_visual_map,
    repository_to_dict,
)


def make_repository() -> RepositoryInfo:
    """创建包含四种节点类型的最小可视化测试数据。"""
    return RepositoryInfo(
        root_path="/projects/sample",
        files=[
            FileInfo(
                path="repoatlas/robot.py",
                classes=[
                    ClassInfo(
                        name="Robot",
                        start_line=5,
                        end_line=30,
                        docstring="Control the robot.",
                    )
                ],
                functions=[
                    FunctionInfo(
                        name="create_robot",
                        start_line=33,
                        end_line=40,
                        parameters=["config"],
                        docstring="Create a configured robot.",
                    )
                ],
                methods=[
                    FunctionInfo(
                        name="move",
                        start_line=10,
                        end_line=18,
                        parameters=["self", "position", "speed"],
                        docstring="Move to a target position.",
                        class_name="Robot",
                    )
                ],
            )
        ],
    )


def test_export_repository_json_contains_complete_structure(tmp_path):
    output_path = tmp_path / "output" / "structure.json"

    result_path = export_repository_json(make_repository(), output_path)
    data = json.loads(result_path.read_text(encoding="utf-8"))

    assert result_path == output_path
    assert data["type"] == "repository"
    assert data["name"] == "sample"
    assert data["root_path"] == "/projects/sample"
    assert data["files"][0]["path"] == "repoatlas/robot.py"
    assert data["files"][0]["classes"][0]["name"] == "Robot"
    assert data["files"][0]["functions"][0]["name"] == "create_robot"
    assert data["files"][0]["functions"][0]["parameters"] == ["config"]
    assert data["files"][0]["methods"][0]["name"] == "move"
    assert data["files"][0]["methods"][0]["signature"] == "move(position, speed)"


def test_render_visual_map_generates_all_outputs(tmp_path):
    output_dir = tmp_path / "output"

    paths = render_visual_map(make_repository(), output_dir)

    assert paths["json"] == output_dir / "structure.json"
    assert paths["html"] == output_dir / "map.html"
    assert paths["markdown"] == output_dir / "STRUCTURE.md"
    assert all(path.is_file() for path in paths.values())


def test_map_html_contains_repository_and_interactive_nodes(tmp_path):
    paths = render_visual_map(make_repository(), tmp_path / "output")

    html = paths["html"].read_text(encoding="utf-8")

    assert "sample · RepoAtlas" in html
    assert '"root_path": "/projects/sample"' in html
    assert '"path": "repoatlas/robot.py"' in html
    assert '"name": "Robot"' in html
    assert '"name": "create_robot"' in html
    assert '"name": "move"' in html
    assert 'id="detail-panel"' in html
    assert "function selectNode" in html
    assert "Expand all" in html
    assert "Open in VS Code" in html
    assert 'addEventListener("dblclick"' in html
    assert 'id="code-viewer"' in html
    assert "function renderSource" in html


def test_vscode_uris_use_absolute_encoded_paths_and_symbol_lines():
    repository = make_repository()
    repository.root_path = "D:/projects/RepoAtlas Demo"

    data = repository_to_dict(repository)
    file_data = data["files"][0]

    assert file_data["vscode_uri"] == (
        "vscode://file/D:/projects/RepoAtlas%20Demo/repoatlas/robot.py:1"
    )
    assert file_data["classes"][0]["vscode_uri"] == (
        "vscode://file/D:/projects/RepoAtlas%20Demo/repoatlas/robot.py:5"
    )
    assert file_data["functions"][0]["vscode_uri"] == (
        "vscode://file/D:/projects/RepoAtlas%20Demo/repoatlas/robot.py:33"
    )
    assert file_data["methods"][0]["vscode_uri"] == (
        "vscode://file/D:/projects/RepoAtlas%20Demo/repoatlas/robot.py:10"
    )


def test_vscode_uri_encodes_special_characters():
    uri = build_vscode_uri(
        "D:/projects/Repo Atlas",
        "src/parser #1.py",
        42,
    )

    assert uri == "vscode://file/D:/projects/Repo%20Atlas/src/parser%20%231.py:42"


def test_map_styles_highlight_connectors_and_selected_ancestry(tmp_path):
    paths = render_visual_map(make_repository(), tmp_path / "output")
    html = paths["html"].read_text(encoding="utf-8")

    assert "--connector: #6687b8;" in html
    assert "--connector-width: 2px;" in html
    assert "--connector-path-width: 3px;" in html
    assert ".node.ancestor" in html
    assert ".tree-item.active-path" in html
    assert "function highlightAncestry" in html
    assert 'id="source-lines"' in html


def test_empty_repository_html_keeps_repository_root(tmp_path):
    repository = RepositoryInfo(root_path="/projects/empty", files=[])

    paths = render_visual_map(repository, tmp_path / "output")
    html = paths["html"].read_text(encoding="utf-8")

    assert '"type": "repository"' in html
    assert '"name": "empty"' in html
    assert "treeElement.append(createNode(repositoryDescriptor()))" in html
    assert "No Python files were detected." in html
