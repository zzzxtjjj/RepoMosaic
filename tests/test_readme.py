from pathlib import Path
import re


PROJECT_ROOT = Path(__file__).parents[1]


def test_readmes_have_clickable_language_switches_and_parallel_topics():
    english = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    chinese = (PROJECT_ROOT / "README.zh-CN.md").read_text(encoding="utf-8")

    assert english.startswith("**English** | [简体中文](README.zh-CN.md)")
    assert chinese.startswith("[English](README.md) | **简体中文**")

    for content in (english, chinese):
        for command in (
            "pip install repoatlas",
            "repoatlas auth set",
            "repoatlas auth status",
            "repoatlas auth clear",
            "repoatlas init",
            "repoatlas .",
            "repoatlas . --no-llm",
            "repoatlas-mcp path/to/project",
        ):
            assert command in content
        for output_name in ("map.html", "STRUCTURE.md", "structure.json"):
            assert output_name in content


def test_readme_examples_never_contain_an_api_key_value():
    for filename in ("README.md", "README.zh-CN.md"):
        content = (PROJECT_ROOT / filename).read_text(encoding="utf-8")
        assert re.search(r"REPOATLAS_API_KEY\s*=", content) is None
