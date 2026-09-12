from pathlib import Path


# 将仓库内的相对文件路径解析为安全的绝对路径，并阻止访问仓库外部文件
def resolve_repository_file(
    root_path: str | Path,
    file_path: str | Path,
) -> Path:
    root = Path(root_path).expanduser().resolve()
    relative_path = Path(file_path)

    if relative_path.is_absolute():
        raise ValueError(
            f"Repository file path must be relative: {file_path}"
        )

    candidate = (root / relative_path).resolve()

    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise ValueError(
            f"File path escapes repository root: {file_path}"
        ) from error

    return candidate