from pathlib import Path

import pytest

from repoatlas.core.paths import resolve_repository_file


# 验证正常的仓库相对路径能够解析为仓库内部的绝对路径
def test_resolve_repository_file_accepts_safe_relative_path(
    tmp_path: Path,
):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    source_file = repo_dir / "main.py"
    source_file.write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    resolved = resolve_repository_file(
        repo_dir,
        "main.py",
    )

    assert resolved == source_file.resolve()


# 验证使用 .. 试图访问仓库外部文件时会被拒绝
def test_resolve_repository_file_rejects_path_traversal(
    tmp_path: Path,
):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    outside_file = tmp_path / "secret.txt"
    outside_file.write_text(
        "secret",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="escapes repository root",
    ):
        resolve_repository_file(
            repo_dir,
            "../secret.txt",
        )


# 验证绝对文件路径不能作为仓库内部文件路径传入
def test_resolve_repository_file_rejects_absolute_path(
    tmp_path: Path,
):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()

    outside_file = tmp_path / "secret.txt"

    with pytest.raises(
        ValueError,
        match="must be relative",
    ):
        resolve_repository_file(
            repo_dir,
            outside_file.resolve(),
        )