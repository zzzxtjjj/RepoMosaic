from repomosaic.core.analyzer import analyze_repository
from repomosaic.rendering.renderer import render_structure_markdown
from repomosaic.rendering.visualizer import render_visual_map


def test_static_analysis_to_rendered_outputs(tmp_path):
    """验证从仓库分析到 Markdown 和交互地图生成的完整流程。"""
    repository_path = tmp_path / "repository"
    repository_path.mkdir()
    (repository_path / "main.py").write_text(
        'def run():\n    """Run the sample."""\n    return True\n',
        encoding="utf-8",
    )
    (repository_path / "controller.py").write_text(
        'class Controller:\n'
        '    """Control the sample."""\n\n'
        '    def start(self):\n'
        '        """Start the controller."""\n'
        '        return True\n',
        encoding="utf-8",
    )

    repository = analyze_repository(repository_path)
    markdown = render_structure_markdown(repository)
    output_paths = render_visual_map(repository, tmp_path / "output")

    assert {file_info.path for file_info in repository.files} == {
        "controller.py",
        "main.py",
    }
    assert repository.files[0].classes or repository.files[1].classes
    assert repository.files[0].methods or repository.files[1].methods
    assert repository.files[0].functions or repository.files[1].functions
    assert "Controller" in markdown
    assert "start()" in markdown
    assert "run()" in markdown
    assert "L1–L3" in markdown
    assert output_paths["json"].is_file()
    assert output_paths["html"].is_file()
