from pathlib import Path

from repoatlas.core.scanner import scan_repository
from repoatlas.core.parser import parse_python_file
from repoatlas.core.symbols import RepositoryInfo, FileInfo


# 分析整个代码仓库：扫描文件，并解析其中所有 Python 文件，最终生成 RepositoryInfo
def analyze_repository(repo_path: str | Path) -> RepositoryInfo:
    repo = Path(repo_path)

    scanned_files = scan_repository(repo)

    parsed_files: list[FileInfo] = []

    for relative_path in scanned_files:

        # 不是 Python 文件就跳过
        if Path(relative_path).suffix != ".py":
            continue

        # 相对路径 + 仓库根目录 = 文件完整路径
        full_path = repo / relative_path

        # 用完整路径读取并解析文件
        file_info = parse_python_file(full_path)

        # FileInfo 中只保存相对于仓库根目录的路径 给 RepoAtlas 保存、展示、生成链接
        file_info.path = relative_path
        parsed_files.append(file_info)

    return RepositoryInfo(
        root_path=repo.as_posix(),
        files=parsed_files,
    )
