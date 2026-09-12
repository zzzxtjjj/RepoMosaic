import json

import pytest

from repoatlas.core.symbols import ClassInfo, FileInfo, FunctionInfo, RepositoryInfo
from repoatlas.rendering.visualizer import (
    build_vscode_uri,
    export_repository_json,
    render_visual_map,
    repository_to_dict,
)
from repoatlas.semantic.models import SemanticSummary


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


def make_summaries() -> list[SemanticSummary]:
    """创建覆盖文件、类、函数和方法的双语摘要。"""
    return [
        SemanticSummary(
            target_type="file",
            file_path="repoatlas/robot.py",
            name="repoatlas/robot.py",
            summary="Defines the robot model and factory.",
            language="en",
        ),
        SemanticSummary(
            target_type="file",
            file_path="repoatlas/robot.py",
            name="repoatlas/robot.py",
            summary="定义机器人模型和工厂函数。",
            language="zh-CN",
        ),
        SemanticSummary(
            target_type="class",
            file_path="repoatlas/robot.py",
            name="Robot",
            start_line=5,
            summary="Represents a controllable robot.",
            language="en",
        ),
        SemanticSummary(
            target_type="function",
            file_path="repoatlas/robot.py",
            name="create_robot",
            start_line=33,
            summary="Builds a robot from configuration.",
            language="en",
        ),
        SemanticSummary(
            target_type="function",
            file_path="repoatlas/robot.py",
            name="create_robot",
            start_line=33,
            summary="根据配置创建机器人。",
            language="zh-CN",
        ),
        SemanticSummary(
            target_type="method",
            file_path="repoatlas/robot.py",
            name="move",
            start_line=10,
            class_name="Robot",
            summary="Moves the robot to a requested position.",
            language="en",
        ),
        SemanticSummary(
            target_type="method",
            file_path="repoatlas/robot.py",
            name="move",
            start_line=10,
            class_name="OtherRobot",
            summary="This summary belongs to another class.",
            language="en",
        ),
    ]


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
    assert data["files"][0]["semantic_summary"] is None
    assert data["files"][0]["classes"][0]["semantic_summary"] is None
    assert data["files"][0]["functions"][0]["semantic_summary"] is None
    assert data["files"][0]["methods"][0]["semantic_summary"] is None


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
    assert "Open File in VS Code" in html
    assert 'addEventListener("dblclick"' not in html
    assert 'id="code-viewer"' in html
    assert "function renderSource" in html
    assert 'id="semantic-summary"' in html
    assert "AI Summary" in html
    assert "semanticSummary.hidden = !node.semantic_summary" in html


def test_only_file_nodes_expose_vscode_uri():
    repository = make_repository()
    repository.root_path = "D:/projects/RepoAtlas Demo"

    data = repository_to_dict(repository)
    file_data = data["files"][0]

    assert file_data["vscode_uri"] == (
        "vscode://file/D:/projects/RepoAtlas%20Demo/repoatlas/robot.py:1"
    )
    assert "vscode_uri" not in file_data["classes"][0]
    assert "vscode_uri" not in file_data["functions"][0]
    assert "vscode_uri" not in file_data["methods"][0]


def test_semantic_summaries_match_file_class_function_and_method():
    data = repository_to_dict(make_repository(), summaries=make_summaries())
    file_data = data["files"][0]

    assert file_data["semantic_summary"] == "Defines the robot model and factory."
    assert file_data["classes"][0]["semantic_summary"] == (
        "Represents a controllable robot."
    )
    assert file_data["functions"][0]["semantic_summary"] == (
        "Builds a robot from configuration."
    )
    assert file_data["methods"][0]["semantic_summary"] == (
        "Moves the robot to a requested position."
    )


def test_method_summary_matching_includes_class_name():
    summaries = [
        summary
        for summary in make_summaries()
        if summary.target_type == "method" and summary.class_name == "OtherRobot"
    ]

    method_data = repository_to_dict(
        make_repository(),
        summaries=summaries,
    )["files"][0]["methods"][0]

    assert method_data["semantic_summary"] is None


def test_semantic_summary_language_selection():
    repository = make_repository()
    summaries = make_summaries()

    english = repository_to_dict(repository, summaries=summaries, language="en")
    chinese = repository_to_dict(repository, summaries=summaries, language="zh-CN")

    assert english["files"][0]["semantic_summary"] == (
        "Defines the robot model and factory."
    )
    assert chinese["files"][0]["semantic_summary"] == "定义机器人模型和工厂函数。"
    assert english["files"][0]["functions"][0]["semantic_summary"] == (
        "Builds a robot from configuration."
    )
    assert chinese["files"][0]["functions"][0]["semantic_summary"] == (
        "根据配置创建机器人。"
    )


def test_render_visual_map_embeds_selected_language_summary(tmp_path):
    paths = render_visual_map(
        make_repository(),
        tmp_path / "output",
        summaries=make_summaries(),
        language="zh-CN",
    )

    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    html = paths["html"].read_text(encoding="utf-8")

    assert data["files"][0]["semantic_summary"] == "定义机器人模型和工厂函数。"
    assert "定义机器人模型和工厂函数。" in html
    assert "根据配置创建机器人。" in html


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

    assert "--connector: #4f74ad;" in html
    assert "--connector-trunk: #315f9e;" in html
    assert "--connector-symbol: #6574b8;" in html
    assert "--connector-active: #1d4ed8;" in html
    assert "--connector-width: 2.5px;" in html
    assert "--connector-trunk-width: 3px;" in html
    assert "--connector-path-width: 4px;" in html
    assert 'path.dataset.targetType = edge.child.node.type' in html
    assert ".node.ancestor" in html
    assert ".connector.active-path" in html
    assert "function highlightAncestry" in html
    assert 'id="source-lines"' in html


def test_fit_view_keeps_small_graph_readable_and_large_graph_fittable(tmp_path):
    html = render_visual_map(make_repository(), tmp_path / "output")["html"].read_text(
        encoding="utf-8"
    )

    assert "const FIT_MAX_SCALE = 1.12" in html
    assert "DEFAULT_MIN_SCALE = .82" in html
    assert "READABLE_NODE_LIMIT = 80" in html
    assert "FIT_PADDING_X = 36" in html
    assert "FIT_PADDING_Y = 48" in html
    assert "return Math.min(FIT_MAX_SCALE" in html
    assert "centerView(fittedScale())" in html
    assert "visible.length <= READABLE_NODE_LIMIT" in html
    assert "Math.max(DEFAULT_MIN_SCALE, scale)" in html
    assert '$("reset-view").addEventListener("click", resetView)' in html
    assert "requestAnimationFrame(resetView)" in html

    # sample_repo 形态在常见左侧视口中应接近正常阅读比例。
    small_fit = min(1.12, (920 - 36) / 1076, (650 - 48) / 648)
    assert 0.8 <= small_fit <= 1.12

    # 大图仍可低于 readable maximum 缩小，保证完整图能 Fit View。
    large_fit = min(1.12, (920 - 36) / 4000, (650 - 48) / 5000)
    assert large_fit < 0.5


def test_empty_repository_html_keeps_repository_root(tmp_path):
    repository = RepositoryInfo(root_path="/projects/empty", files=[])

    paths = render_visual_map(repository, tmp_path / "output")
    html = paths["html"].read_text(encoding="utf-8")

    assert '"type": "repository"' in html
    assert '"name": "empty"' in html
    assert 'record({ type: "repository"' in html
    assert "No Python files were detected." in html


def test_file_source_documentation_is_separate_from_ai_summary(tmp_path):
    repository = make_repository()
    repository.files[0].module_docstring = "Original documentation.\n\n保持原始语言。"
    paths = render_visual_map(repository, tmp_path, make_summaries(), "en")
    data = json.loads(paths["json"].read_text(encoding="utf-8"))
    file_data = data["files"][0]
    assert file_data["module_docstring"] == "Original documentation.\n\n保持原始语言。"
    assert file_data["docstring"] == file_data["module_docstring"]
    assert file_data["semantic_summary"] == "Defines the robot model and factory."
    html = paths["html"].read_text(encoding="utf-8")
    assert 'node.type === "file" ? node.module_docstring : node.docstring' in html
    assert html.index('id="detail-description"') < html.index('id="semantic-summary"')
    assert html.index('id="semantic-summary"') < html.index('id="code-viewer"')


def test_missing_source_description_is_not_invented():
    repository = make_repository()
    repository.files[0].functions[0].docstring = ""
    file_data = repository_to_dict(repository)["files"][0]
    assert file_data["module_docstring"] == ""
    assert file_data["docstring"] == ""
    assert file_data["functions"][0]["docstring"] == ""
    assert file_data["semantic_summary"] is None


def test_full_source_and_symbol_ranges_are_preserved(tmp_path):
    repository = make_repository()
    repository.root_path = str(tmp_path)
    source_path = tmp_path / "repoatlas" / "robot.py"
    source_path.parent.mkdir()
    source = "\n".join("    # source line " + str(n) for n in range(1, 45)) + "\n"
    source_path.write_text(source, encoding="utf-8")
    file_data = repository_to_dict(repository)["files"][0]
    assert file_data["source"] == source
    assert file_data["start_line"] == 1
    assert file_data["end_line"] == 44
    assert file_data["methods"][0]["start_line"] == 10
    assert file_data["methods"][0]["end_line"] == 18


def test_repository_serialization_rejects_source_outside_root(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    outside_file = tmp_path / "outside.py"
    outside_file.write_text("secret = True\n", encoding="utf-8")
    repository = RepositoryInfo(
        root_path=repo_dir.as_posix(),
        files=[
            FileInfo(
                path="../outside.py",
                functions=[],
                classes=[],
                methods=[],
            )
        ],
    )

    with pytest.raises(ValueError, match="escapes repository root"):
        repository_to_dict(repository)


def test_light_canvas_contains_offline_navigation_controls(tmp_path):
    html = render_visual_map(make_repository(), tmp_path)["html"].read_text(encoding="utf-8")
    for hook in ("repository-search", "search-results", "knowledge-canvas", "graph-stage",
                 "connectors", "fit-view", "reset-view", "zoom-in", "zoom-out",
                 "focus-selected", "toggle-details"):
        assert 'id="' + hook + '"' in html
    for node_type in ("file", "class", "function", "method"):
        assert 'data-filter="' + node_type + '"' in html
    assert "color-scheme: light" in html
    assert "No source description." in html
    assert '<section class="semantic-summary" id="semantic-summary" hidden>' in html
    assert "<script src=" not in html
    assert "<link " not in html
