from repoatlas.scanner import scan_repository
import pytest

def test_scan_repository(tmp_path):
    
    main_file = tmp_path / "main.py"
    main_file.write_text("print('hello')", encoding="utf-8")
   
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    utils_file = src_dir / "utils.py"
    utils_file.write_text("def add(a, b): return a + b", encoding="utf-8")
   
    git_dir = tmp_path / ".git"
    git_dir.mkdir()

    git_file = git_dir / "config"
    git_file.write_text("git config", encoding="utf-8")

    result = scan_repository(tmp_path)

    # 判断文件是否在result里面
    assert "main.py" in result
    assert "src/utils.py" in result
    assert ".git/config" not in result


def test_nonexistent_repository(tmp_path):
    missing_path = tmp_path / "not_exist"

    with pytest.raises(FileNotFoundError):
        scan_repository(missing_path)


def test_repository_path_is_file(tmp_path):
    fake_repo = tmp_path / "fake_repo.py"
    fake_repo.write_text("..", encoding="utf-8")

    with pytest.raises(NotADirectoryError):
        scan_repository(fake_repo)
