from pathlib import Path

from repoatlas.core.paths import resolve_repository_file


IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}


def scan_repository(repo_path: str | Path) -> list[str]:
    """
    Scan a repository and return file paths relative
    to the repository root.
    """

    repo = Path(repo_path).expanduser().resolve()

    if not repo.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo}")

    if not repo.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo}")

    files: list[str] = []

    for path in repo.rglob("*"):

        if not path.is_file():
            continue

        relative_path = path.relative_to(repo)

        if any(part in IGNORED_DIRS for part in relative_path.parts):
            continue

        try:
            resolve_repository_file(repo, relative_path)
        except ValueError:
            # 跳过解析后指向仓库外部的文件符号链接。
            continue

        # 不管用户是 Windows、macOS 还是 Linux，都统一得到 / 风格的路径
        files.append(relative_path.as_posix())

    return files
