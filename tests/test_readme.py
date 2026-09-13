from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parents[1]


def test_readmes_have_clickable_language_switches_and_parallel_topics():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert english.startswith("**English** | [简体中文](README.zh-CN.md)")
    assert chinese.startswith("[English](README.md) | **简体中文**")

    for content in (english, chinese):
        assert "RepoMosaic" in content
        assert "uv tool install repomosaic" in content
        for command in (
            "pip install repomosaic",
            "repomosaic auth set",
            "repomosaic auth status",
            "repomosaic auth clear",
            "repomosaic init",
            "repomosaic .",
            "repomosaic . --no-llm",
            "repomosaic-mcp path/to/project",
        ):
            assert command in content
        for output_name in ("map.html", "STRUCTURE.md", "structure.json"):
            assert output_name in content

        assert "RepoAtlas" not in content
        assert "repoatlas" not in content
        assert "REPOATLAS" not in content


def test_readme_examples_never_contain_an_api_key_value():
    for filename in ("README.md", "README.zh-CN.md"):
        content = (PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert re.search(r"REPOMOSAIC_API_KEY\s*=", content) is None
