from repoatlas.cli import main


def test_cli_generates_repository_outputs(tmp_path):
    """验证 CLI 能分析小仓库并创建完整输出目录。"""
    repository = tmp_path / "sample_repo"
    repository.mkdir()
    (repository / "main.py").write_text(
        'def greet(name):\n    """Return a greeting."""\n    return f"Hello {name}"\n',
        encoding="utf-8",
    )
    output_dir = tmp_path / "generated"

    exit_code = main([str(repository), "--output-dir", str(output_dir), "--no-llm"])

    assert exit_code == 0
    assert output_dir.is_dir()
    assert (output_dir / "STRUCTURE.md").is_file()
    assert (output_dir / "structure.json").is_file()
    assert (output_dir / "map.html").is_file()
    markdown = (output_dir / "STRUCTURE.md").read_text(encoding="utf-8")
    assert "main.py" in markdown
    assert "greet(name)" in markdown


def test_cli_returns_nonzero_for_invalid_repository(tmp_path, capsys):
    """验证非法仓库路径返回非零状态和清晰错误。"""
    missing_path = tmp_path / "missing"

    exit_code = main([str(missing_path)])

    assert exit_code != 0
    assert "RepoAtlas error:" in capsys.readouterr().err
