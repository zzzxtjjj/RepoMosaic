"""把仓库静态分析结果渲染为人类可读的 Markdown 代码地图。"""
import os
from pathlib import Path
from repomosaic.core.paths import resolve_repository_file
import re
from urllib.parse import quote
from repomosaic.core.parser import build_signature
from repomosaic.core.symbols import FileInfo, FunctionInfo, RepositoryInfo


DEFAULT_DESCRIPTION = "No description available."


def _encode_markdown_target(target: str) -> str:
    """编码链接路径，同时保留目录分隔符、盘符和已有转义。"""
    normalized = target.replace("\\", "/")
    return quote(normalized, safe="/:%")


def _escape_markdown_label(label: str) -> str:
    """转义链接显示文字中会破坏 Markdown 结构的字符。"""
    return label.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")


def sanitize_mermaid_text(text: str) -> str:
    """清理 Mermaid 节点文字，避免换行和特殊字符破坏语法。"""
    cleaned = " ".join(str(text).split())
    return (
        cleaned.replace("&", "&amp;")
        .replace('"', "&quot;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("[", "(")
        .replace("]", ")")
    )


def truncate_description(description: str, max_length: int = 100) -> str:
    """把多行说明压缩为适合思维导图展示的单行短文本。"""
    cleaned = " ".join(description.split())
    if len(cleaned) <= max_length:
        return cleaned
    return cleaned[: max_length - 1].rstrip() + "…"


def render_line_range(start_line: int, end_line: int) -> str:
    """统一生成紧凑、易扫描的行号范围。"""
    return f"L{start_line}–L{end_line}"


def render_symbol_link(
    file_path: str,
    label: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """生成 GitHub Markdown 相对链接，便于以后替换其他链接策略。"""
    target = _encode_markdown_target(file_path)
    if start_line is not None:
        target += f"#L{start_line}"
        if end_line is not None and end_line != start_line:
            target += f"-L{end_line}"
    return f"[{_escape_markdown_label(label)}]({target})"


def _node_id(prefix: str, *parts: object) -> str:
    """为 Mermaid 节点创建只含安全字符的稳定标识。"""
    raw = "_".join(str(part) for part in parts)
    safe = re.sub(r"[^a-zA-Z0-9_]", "_", raw)
    return f"{prefix}_{safe}"


def _mindmap_node(indent: int, node_id: str, label: str) -> str:
    return f'{" " * indent}{node_id}["{sanitize_mermaid_text(label)}"]'


def _append_symbol_nodes(
    lines: list[str],
    symbols: list[FunctionInfo],
    category_id: str,
    is_method: bool,
) -> None:
    """向 Mermaid 分类节点追加签名、行号和可选说明。"""
    for index, symbol in enumerate(symbols):
        symbol_id = _node_id(category_id, index, symbol.name)
        signature = build_signature(symbol, is_method=is_method)
        lines.append(_mindmap_node(8, symbol_id, signature))
        lines.append(
            _mindmap_node(
                10,
                _node_id(symbol_id, "lines"),
                render_line_range(symbol.start_line, symbol.end_line),
            )
        )
        if symbol.docstring.strip():
            lines.append(
                _mindmap_node(
                    10,
                    _node_id(symbol_id, "description"),
                    truncate_description(symbol.docstring),
                )
            )


def render_mindmap(repository: RepositoryInfo) -> str:
    """根据 RepositoryInfo 生成 Mermaid repository knowledge map。"""
    lines = ["```mermaid", "mindmap", '  root(("Repository"))']

    for file_index, file_info in enumerate(repository.files):
        file_id = _node_id("file", file_index, file_info.path)
        lines.append(_mindmap_node(4, file_id, file_info.path))

        if file_info.classes:
            category_id = _node_id(file_id, "classes")
            lines.append(_mindmap_node(6, category_id, "Classes"))
            for class_index, class_info in enumerate(file_info.classes):
                class_id = _node_id(category_id, class_index, class_info.name)
                lines.append(_mindmap_node(8, class_id, class_info.name))
                lines.append(
                    _mindmap_node(
                        10,
                        _node_id(class_id, "lines"),
                        render_line_range(class_info.start_line, class_info.end_line),
                    )
                )
                if class_info.docstring.strip():
                    lines.append(
                        _mindmap_node(
                            10,
                            _node_id(class_id, "description"),
                            truncate_description(class_info.docstring),
                        )
                    )

        if file_info.functions:
            category_id = _node_id(file_id, "functions")
            lines.append(_mindmap_node(6, category_id, "Functions"))
            _append_symbol_nodes(lines, file_info.functions, category_id, False)

        if file_info.methods:
            category_id = _node_id(file_id, "methods")
            lines.append(_mindmap_node(6, category_id, "Methods"))
            _append_symbol_nodes(lines, file_info.methods, category_id, True)

    lines.append("```")
    return "\n".join(lines)


def _description(docstring: str) -> str:
    cleaned = " ".join(docstring.split())
    return cleaned or DEFAULT_DESCRIPTION


def _format_symbol_count(count: int, singular: str, plural: str) -> str:
    """根据数量生成自然的单复数 symbol 统计。"""
    label = singular if count == 1 else plural
    return f"{count} {label}"


def _render_symbol_metadata(file_info: FileInfo) -> str:
    """生成文件级结构统计，不把统计信息冒充功能说明。"""
    parts = [
        _format_symbol_count(len(file_info.classes), "class", "classes"),
        _format_symbol_count(len(file_info.functions), "function", "functions"),
        _format_symbol_count(len(file_info.methods), "method", "methods"),
    ]
    return f"Symbols: {' · '.join(parts)}"


# 渲染单个 Python 文件的完整 symbol 明细
def _render_file_details(
    file_info: FileInfo,
    source_link: str,
) -> list[str]:
    """渲染单个 Python 文件的完整 symbol 明细。"""

    path = file_info.path

    # path 用于显示给用户看；
    # source_link 用于真正的 Markdown 点击跳转。
    lines = [
        f"## {render_symbol_link(source_link, path)}",
        "",
    ]

    lines.append(_render_symbol_metadata(file_info))

    lines.extend(["", "### Classes", ""])

    if not file_info.classes:
        lines.append("No classes detected.")
    else:
        for class_info in file_info.classes:
            class_link = render_symbol_link(
                source_link,
                class_info.name,
                class_info.start_line,
                class_info.end_line,
            )

            lines.extend(
                [
                    (
                        f"#### {class_link} · "
                        f"{render_line_range(class_info.start_line, class_info.end_line)}"
                    ),
                    "",
                    _description(class_info.docstring),
                ]
            )

            class_methods = [
                method
                for method in file_info.methods
                if method.class_name == class_info.name
            ]

            lines.extend(["", "Methods:", ""])

            if not class_methods:
                lines.append("No methods detected.")

            for method in class_methods:
                signature = build_signature(
                    method,
                    is_method=True,
                )

                method_link = render_symbol_link(
                    source_link,
                    signature,
                    method.start_line,
                    method.end_line,
                )

                lines.extend(
                    [
                        (
                            f"- {method_link} · "
                            f"{render_line_range(method.start_line, method.end_line)}"
                        ),
                        f"  - {_description(method.docstring)}",
                    ]
                )

    lines.extend(["", "### Functions", ""])

    if not file_info.functions:
        lines.append("No functions detected.")

    for function in file_info.functions:
        signature = build_signature(function)

        function_link = render_symbol_link(
            source_link,
            signature,
            function.start_line,
            function.end_line,
        )

        lines.extend(
            [
                (
                    f"- {function_link} · "
                    f"{render_line_range(function.start_line, function.end_line)}"
                ),
                "",
                f"  - {_description(function.docstring)}",
            ]
        )

    known_classes = {
        class_info.name
        for class_info in file_info.classes
    }

    unmatched_methods = [
        method
        for method in file_info.methods
        if method.class_name not in known_classes
    ]

    if unmatched_methods:
        lines.extend(["", "### Methods", ""])

        for method in unmatched_methods:
            signature = build_signature(
                method,
                is_method=True,
            )

            method_link = render_symbol_link(
                source_link,
                signature,
                method.start_line,
                method.end_line,
            )

            lines.extend(
                [
                    (
                        f"- {method_link} · "
                        f"{render_line_range(method.start_line, method.end_line)}"
                    ),
                    f"  - {_description(method.docstring)}",
                ]
            )

    return lines


def render_structure_markdown(repository: RepositoryInfo, 
                              output_dir: str | Path | None = None
                              ) -> str:
    """生成包含全局思维导图和逐文件明细的完整 STRUCTURE.md。"""
    lines = [
        "# Repository Knowledge Map",
        "",
        f"Repository: `{repository.root_path}`",
        "",
        render_mindmap(repository),
        "",
        "---",
    ]

    for file_info in repository.files:
        if output_dir is not None:
            source_link = build_source_link(
                repository.root_path,
                file_info.path,
                output_dir,
            )
        else:
            source_link = file_info.path

        lines.extend(
            [
                "",
                *_render_file_details(
                    file_info,
                    source_link,
                ),
                "",
                "---",
            ]
        )

    if repository.files:
        lines.pop()
    else:
        lines.extend(["", DEFAULT_DESCRIPTION])

    return "\n".join(lines).rstrip() + "\n"



# 根据 Markdown 输出目录和仓库文件路径，生成可点击的相对源码链接
def build_source_link(
    repository_root: str | Path,
    file_path: str,
    output_dir: str | Path,
) -> str:

    source_path = resolve_repository_file(
        repository_root,
        file_path
    )

    output_root = Path(output_dir).expanduser().resolve()
    
    try:
        relative_path = os.path.relpath(
            source_path,
            start=output_root,
        )
    except ValueError:
        # Windows 不同盘符无法生成相对路径，回退到有效的 file URI。
        return _encode_markdown_target(source_path.as_uri())

    return _encode_markdown_target(Path(relative_path).as_posix())
