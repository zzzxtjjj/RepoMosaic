from pathlib import Path
from repomosaic.core.parser import build_signature
from repomosaic.core.symbols import (
    ClassInfo,
    FunctionInfo,
    RepositoryInfo,
)
from repomosaic.core.analyzer import analyze_repository
from repomosaic.core.paths import resolve_repository_file


# 将一个 class/function/method 转换成统一的 Agent symbol 字典
def _serialize_symbol(
    file_path: str,
    kind: str,
    symbol: ClassInfo | FunctionInfo,
) -> dict:
    """将 RepoMosaic 内部 symbol 转换成适合 Agent 使用的结构化数据。"""

    # 1. 默认情况下，qualified name 就等于 symbol 本身的名字
    qualified_name = symbol.name

    # 2. 方法需要带上类名，例如 RobotController.move
    if kind == "method" and isinstance(symbol, FunctionInfo):
        if symbol.class_name is not None:
            qualified_name = f"{symbol.class_name}.{symbol.name}"

    # 3. 根据 symbol 类型生成用于展示的 signature
    if kind == "class":
        signature = symbol.name

    elif kind == "method" and isinstance(symbol, FunctionInfo):
        method_signature = build_signature(
            symbol,
            is_method=True,
        )

        if symbol.class_name is not None:
            signature = f"{symbol.class_name}.{method_signature}"
        else:
            signature = method_signature

    elif kind == "function" and isinstance(symbol, FunctionInfo):
        signature = build_signature(symbol)

    else:
        signature = symbol.name

    # 4. 构造统一的 Agent-facing symbol
    result = {
        "kind": kind,
        "name": symbol.name,
        "qualified_name": qualified_name,
        "path": file_path,
        "signature": signature,
        "start_line": symbol.start_line,
        "end_line": symbol.end_line,
        "docstring": symbol.docstring,
        "ref": {
            "path": file_path,
            "kind": kind,
            "name": symbol.name,
            "start_line": symbol.start_line,
        },
    }

    return result


# 将整个 RepositoryInfo 转换成适合 Agent 快速浏览的仓库结构
def get_repository_structure(
    repository: RepositoryInfo,
) -> dict:
    """返回紧凑、稳定、不包含源码的仓库结构。"""

    files = []

    # 为了让每次返回顺序一致，先按文件路径排序
    sorted_files = sorted(
        repository.files,
        key=lambda file_info: file_info.path,
    )

    for file_info in sorted_files:
        symbols = []

        # ClassInfo -> Agent symbol
        for class_info in file_info.classes:
            symbols.append(
                _serialize_symbol(
                    file_path=file_info.path,
                    kind="class",
                    symbol=class_info,
                )
            )

        # 顶层 FunctionInfo -> Agent symbol
        for function_info in file_info.functions:
            symbols.append(
                _serialize_symbol(
                    file_path=file_info.path,
                    kind="function",
                    symbol=function_info,
                )
            )

        # Method FunctionInfo -> Agent symbol
        for method_info in file_info.methods:
            symbols.append(
                _serialize_symbol(
                    file_path=file_info.path,
                    kind="method",
                    symbol=method_info,
                )
            )

        # 同一个文件里的 symbol 按源码出现顺序排列
        symbols.sort(
            key=lambda item: (
                item["start_line"],
                item["kind"],
                item["qualified_name"],
            )
        )

        files.append(
            {
                "path": file_info.path,
                "module_docstring": file_info.module_docstring,
                "symbols": symbols,
            }
        )

    repository_name = Path(repository.root_path).name

    return {
        "repository": repository_name,
        "files": files,
    }


# 计算一个 symbol 与查询词的匹配优先级；数字越小，匹配越好
def _get_match_rank(
    query: str,
    symbol: dict,
) -> int | None:
    """返回 symbol 对查询词的匹配等级，不匹配时返回 None。"""

    name = symbol["name"]
    qualified_name = symbol["qualified_name"]

    candidates = [
        name,
        qualified_name,
    ]

    # 0：大小写完全一致
    if query in candidates:
        return 0

    normalized_query = query.casefold()
    normalized_candidates = [
        candidate.casefold()
        for candidate in candidates
    ]

    # 1：忽略大小写后完全一致
    if normalized_query in normalized_candidates:
        return 1

    # 2：前缀匹配
    if any(
        candidate.startswith(normalized_query)
        for candidate in normalized_candidates
    ):
        return 2

    # 3：子串匹配
    if any(
        normalized_query in candidate
        for candidate in normalized_candidates
    ):
        return 3

    return None


# 在仓库中按名称搜索 class/function/method，并按匹配质量排序
def find_symbol(
    repository: RepositoryInfo,
    query: str,
    kind: str | None = None,
    path: str | None = None,
    limit: int = 50,
) -> dict:
    """搜索仓库中的 symbol，并返回排序后的匹配结果。"""

    query = query.strip()

    if not query:
        raise ValueError("query must not be empty")

    allowed_kinds = {
        "class",
        "function",
        "method",
    }

    if kind is not None and kind not in allowed_kinds:
        raise ValueError(
            f"Unsupported symbol kind: {kind}"
        )

    if limit <= 0:
        raise ValueError("limit must be greater than 0")

    normalized_path = None
    if path is not None:
        normalized_path = path.replace("\\", "/")

    structure = get_repository_structure(repository)

    ranked_matches = []

    for file_info in structure["files"]:
        for symbol in file_info["symbols"]:

            # kind 过滤
            if kind is not None and symbol["kind"] != kind:
                continue

            # path 过滤
            if (
                normalized_path is not None
                and symbol["path"] != normalized_path
            ):
                continue

            rank = _get_match_rank(
                query,
                symbol,
            )

            # None 表示完全不匹配
            if rank is None:
                continue

            ranked_matches.append(
                (
                    rank,
                    symbol,
                )
            )

    ranked_matches.sort(
        key=lambda item: (
            item[0],
            item[1]["path"],
            item[1]["start_line"],
            item[1]["qualified_name"],
        )
    )

    truncated = len(ranked_matches) > limit

    matches = [
        symbol
        for _, symbol in ranked_matches[:limit]
    ]

    return {
        "query": query,
        "matches": matches,
        "truncated": truncated,
    }


# 根据 symbol ref 在当前仓库中重新定位目标，并安全返回该 symbol 的源码
def get_symbol_source(
    repository_root: str | Path,
    symbol_ref: dict,
) -> dict:
    """根据结构化 symbol ref 返回当前仓库中的真实源码。"""

    required_fields = {
        "path",
        "kind",
        "name",
        "start_line",
    }

    missing_fields = required_fields - symbol_ref.keys()

    if missing_fields:
        missing_text = ", ".join(sorted(missing_fields))
        raise ValueError(
            f"symbol ref is missing required fields: {missing_text}"
        )

    kind = symbol_ref["kind"]

    if kind not in {
        "class",
        "function",
        "method",
    }:
        raise ValueError(
            f"Unsupported symbol kind: {kind}"
        )

    # 重新分析当前仓库，避免依赖旧的 RepositoryInfo
    repository = analyze_repository(repository_root)

    target_symbol = None

    for file_info in repository.files:

        if file_info.path != symbol_ref["path"]:
            continue

        if kind == "class":
            candidates = file_info.classes

        elif kind == "function":
            candidates = file_info.functions

        else:
            candidates = file_info.methods

        for candidate in candidates:

            if candidate.name != symbol_ref["name"]:
                continue

            if candidate.start_line != symbol_ref["start_line"]:
                continue

            # method 还需要额外核对 class_name
            if kind == "method":
                expected_class_name = symbol_ref.get(
                    "class_name"
                )

                if (
                    expected_class_name is not None
                    and candidate.class_name
                    != expected_class_name
                ):
                    continue

            target_symbol = candidate
            break

        if target_symbol is not None:
            break

    if target_symbol is None:
        raise ValueError(
            "Symbol reference is stale or no longer exists. "
            "Call find_symbol again."
        )

    source_path = resolve_repository_file(
        repository.root_path,
        symbol_ref["path"],
    )

    source_lines = source_path.read_text(
        encoding="utf-8",
    ).splitlines()

    source = "\n".join(
        source_lines[
            target_symbol.start_line - 1:
            target_symbol.end_line
        ]
    )

    serialized = _serialize_symbol(
        file_path=symbol_ref["path"],
        kind=kind,
        symbol=target_symbol,
    )

    return {
        "symbol": {
            "path": serialized["path"],
            "kind": serialized["kind"],
            "name": serialized["name"],
            "qualified_name": serialized[
                "qualified_name"
            ],
            "signature": serialized["signature"],
            "start_line": serialized["start_line"],
            "end_line": serialized["end_line"],
        },
        "source": source,
    }