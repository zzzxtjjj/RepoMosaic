from repomosaic.core.analyzer import analyze_repository
from pathlib import Path


# 测试整个仓库分析流程：扫描仓库中的 Python 文件，并返回对应的 FileInfo 结果
def test_analyze_repository(tmp_path):
    # 创建一个简单的 Python 文件
    main_file = tmp_path / "main.py"
    main_file.write_text(
        """
def hello(name):
    \"\"\"Say hello.\"\"\"
    return f"Hello {name}"
""",
        encoding="utf-8",
    )

    # 创建一个子目录和另一个 Python 文件
    src_dir = tmp_path / "src"
    src_dir.mkdir()

    robot_file = src_dir / "robot.py"
    robot_file.write_text(
        """
class Robot:
    \"\"\"Control the robot.\"\"\"

    def move(self, target):
        \"\"\"Move to the target.\"\"\"
        pass
""",
        encoding="utf-8",
    )

    # 创建一个非 Python 文件
    readme_file = tmp_path / "README.md"
    readme_file.write_text("# Sample Project", encoding="utf-8")

    result = analyze_repository(tmp_path)

    # 应该只解析两个 Python 文件
    assert len(result.files) == 2

    # 检查保存的是相对路径，而不是电脑上的完整路径
    file_paths = [file_info.path for file_info in result.files]

    assert "main.py" in file_paths
    assert "src/robot.py" in file_paths
    assert "README.md" not in file_paths

    # 找到 main.py 的分析结果
    main_info = next(
        file_info
        for file_info in result.files
        if file_info.path == "main.py"
    )

    assert main_info.functions[0].name == "hello"
    assert main_info.functions[0].parameters == ["name"]
    assert main_info.functions[0].docstring == "Say hello."

    # 找到 robot.py 的分析结果
    robot_info = next(
        file_info
        for file_info in result.files
        if file_info.path == "src/robot.py"
    )

    assert robot_info.classes[0].name == "Robot"
    assert robot_info.methods[0].name == "move"
    assert robot_info.methods[0].class_name == "Robot"
    assert robot_info.methods[0].parameters == ["self", "target"]


# 验证 RepositoryInfo 保存的是稳定的绝对仓库根路径，而不是依赖当前工作目录的相对路径
def test_analyze_repository_stores_absolute_root_path(
    tmp_path,
    monkeypatch,
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text(
        """
def hello():
    return "hello"
""".strip(),
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    repository = analyze_repository("sample_repo")

    root_path = Path(repository.root_path)

    assert root_path.is_absolute()
    assert root_path == repo_dir.resolve()