from repomosaic.core.symbols import ClassInfo, FileInfo, FunctionInfo, RepositoryInfo
import repomosaic.rendering.renderer as renderer_module
from repomosaic.rendering.renderer import (
    build_source_link,
    render_mindmap,
    render_structure_markdown,
    render_symbol_link,
)


def make_repository() -> RepositoryInfo:
    """创建覆盖类、方法和普通函数的最小渲染测试数据。"""
    return RepositoryInfo(
        root_path="/projects/sample",
        files=[
            FileInfo(
                path="repomosaic/parser.py",
                classes=[
                    ClassInfo(
                        name="Robot",
                        start_line=10,
                        end_line=50,
                        docstring="Control the robot.",
                    )
                ],
                functions=[
                    FunctionInfo(
                        name="parse_python_file",
                        start_line=60,
                        end_line=110,
                        parameters=["file_path"],
                        docstring="Parse a Python file.",
                    ),
                    FunctionInfo(
                        name="extract_function_info",
                        start_line=113,
                        end_line=126,
                        parameters=["node"],
                        docstring="Extract function information.",
                    ),
                ],
                methods=[
                    FunctionInfo(
                        name="move",
                        start_line=20,
                        end_line=35,
                        parameters=["self", "position", "speed"],
                        docstring="Move the robot to a target position.",
                        class_name="Robot",
                    ),
                    FunctionInfo(
                        name="stop",
                        start_line=37,
                        end_line=42,
                        parameters=["self"],
                        docstring="Stop the robot.",
                        class_name="Robot",
                    ),
                ],
            )
        ],
    )


def test_render_mindmap_contains_repository_symbols_and_lines():
    result = render_mindmap(make_repository())

    assert "mindmap" in result
    assert "Repository" in result
    assert "repomosaic/parser.py" in result
    assert "parse_python_file(file_path)" in result
    assert "Robot" in result
    assert "move(position, speed)" in result
    assert "stop()" in result
    assert "extract_function_info(node)" in result
    assert "L60–L110" in result
    assert "L20–L35" in result


def test_render_structure_markdown_is_complete_and_linked():
    result = render_structure_markdown(make_repository())

    assert result.startswith("# Repository Knowledge Map")
    assert "```mermaid" in result
    assert "## [repomosaic/parser.py](repomosaic/parser.py)" in result
    assert "\n##\n" not in result
    assert "Symbols: 1 class · 2 functions · 2 methods" in result
    assert "Detected" not in result
    assert "### Classes" in result
    assert (
        "#### [Robot](repomosaic/parser.py#L10-L50) · L10–L50"
        in result
    )
    assert "\n####\n" not in result
    assert "[move(position, speed)](repomosaic/parser.py#L20-L35)" in result
    assert "[stop()](repomosaic/parser.py#L37-L42)" in result
    assert "### Functions" in result
    assert "[parse_python_file(file_path)](repomosaic/parser.py#L60-L110)" in result
    assert (
        "[extract_function_info(node)](repomosaic/parser.py#L113-L126)"
        in result
    )
    assert "Parse a Python file." in result
    assert "Extract function information." in result
    assert "Move the robot to a target position." in result
    assert "Stop the robot." in result


def test_missing_docstring_uses_explicit_fallback():
    repository = make_repository()
    repository.files[0].functions[0].docstring = ""

    result = render_structure_markdown(repository)

    assert "No description available." in result


def test_every_class_has_heading_before_docstring_and_methods():
    repository = make_repository()
    repository.files[0].classes.append(
        ClassInfo(
            name="Controller",
            start_line=52,
            end_line=58,
            docstring="Coordinate robot actions.",
        )
    )

    markdown = render_structure_markdown(repository)

    robot_section = (
        "#### [Robot](repomosaic/parser.py#L10-L50) · L10–L50\n\n"
        "Control the robot.\n\nMethods:"
    )
    controller_section = (
        "#### [Controller](repomosaic/parser.py#L52-L58) · L52–L58\n\n"
        "Coordinate robot actions.\n\nMethods:"
    )
    assert robot_section in markdown
    assert controller_section in markdown
    assert markdown.count("\n#### [") == len(repository.files[0].classes)
    assert "\n####\n" not in markdown


def test_mindmap_truncates_description_but_details_keep_it_complete():
    repository = make_repository()
    long_docstring = "A" * 140
    repository.files[0].functions[0].docstring = long_docstring

    mindmap = render_mindmap(repository)
    markdown = render_structure_markdown(repository)

    assert long_docstring not in mindmap
    assert "A" * 99 + "…" in mindmap
    assert long_docstring in markdown


# 验证 Markdown 源码链接会根据输出目录生成正确的相对路径
def test_build_source_link_relative_to_output_directory(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    source_dir = repo_dir / "repomosaic" / "core"
    source_dir.mkdir(parents=True)

    source_file = source_dir / "parser.py"
    source_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    output_dir = repo_dir / "repomosaic_output"
    output_dir.mkdir()

    link = build_source_link(
        repository_root=repo_dir,
        file_path="repomosaic/core/parser.py",
        output_dir=output_dir,
    )

    assert link == "../repomosaic/core/parser.py"


# 验证输出目录嵌套更深时，源码链接仍能正确回到仓库文件
def test_build_source_link_from_nested_output_directory(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    source_file = repo_dir / "main.py"
    source_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    output_dir = repo_dir / "docs" / "generated"
    output_dir.mkdir(parents=True)

    link = build_source_link(
        repository_root=repo_dir,
        file_path="main.py",
        output_dir=output_dir,
    )

    assert link == "../../main.py"


def test_build_source_link_encodes_special_path_characters(tmp_path):
    repo_dir = tmp_path / "repo"
    output_dir = repo_dir / "docs"
    output_dir.mkdir(parents=True)

    cases = {
        "my package/parser.py": "../my%20package/parser.py",
        "module#old.py": "../module%23old.py",
        "module(test).py": "../module%28test%29.py",
        "模块.py": "../%E6%A8%A1%E5%9D%97.py",
    }

    for file_path, expected in cases.items():
        assert build_source_link(repo_dir, file_path, output_dir) == expected


def test_render_symbol_link_appends_anchor_after_encoded_filename():
    link = render_symbol_link(
        "../my package/module#old(test).py",
        "module#old(test).py",
        10,
        20,
    )

    assert link == (
        "[module#old(test).py]"
        "(../my%20package/module%23old%28test%29.py#L10-L20)"
    )


def test_render_symbol_link_escapes_markdown_label_brackets():
    link = render_symbol_link("module.py", "module[old].py")

    assert link == r"[module\[old\].py](module.py)"


def test_build_source_link_uses_file_uri_when_relative_path_is_unavailable(
    tmp_path,
    monkeypatch,
):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    source_file = repo_dir / "my package" / "parser.py"
    source_file.parent.mkdir()
    source_file.write_text("value = 1\n", encoding="utf-8")
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    def raise_cross_drive_error(*args, **kwargs):
        raise ValueError("path is on a different drive")

    monkeypatch.setattr(renderer_module.os.path, "relpath", raise_cross_drive_error)

    link = build_source_link(repo_dir, "my package/parser.py", output_dir)

    assert link.startswith("file:///")
    assert link.endswith("/repo/my%20package/parser.py")
