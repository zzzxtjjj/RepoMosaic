"""把 RepositoryInfo 导出为 JSON 和可交互的静态知识地图。"""

from html import escape
import json
from pathlib import Path, PureWindowsPath
from urllib.parse import quote

from repoatlas.parser import build_signature
from repoatlas.renderer import DEFAULT_DESCRIPTION, render_structure_markdown
from repoatlas.symbols import ClassInfo, FileInfo, FunctionInfo, RepositoryInfo


TEMPLATE_PATH = Path(__file__).parent / "templates" / "map.html"


def _description(docstring: str) -> str:
    """返回清理后的说明，缺失时使用明确的占位文本。"""
    cleaned = " ".join(docstring.split())
    return cleaned or DEFAULT_DESCRIPTION


def build_vscode_uri(
    root_path: str | Path,
    relative_path: str,
    line: int = 1,
) -> str:
    """生成使用正斜杠和 URI 编码的 VS Code 文件跳转地址。"""
    root_text = str(root_path)
    relative_text = relative_path.replace("\\", "/").lstrip("/")
    windows_root = PureWindowsPath(root_text)

    if windows_root.drive:
        absolute_path = (windows_root / PureWindowsPath(relative_text)).as_posix()
    else:
        absolute_path = (
            Path(root_text).expanduser() / Path(relative_text)
        ).resolve().as_posix()

    encoded_path = quote(absolute_path, safe="/:")
    return f"vscode://file/{encoded_path}:{max(1, line)}"


def _read_source(root_path: str | Path, relative_path: str) -> str:
    """读取可视化所需源码；文件不可用时返回空字符串。"""
    source_path = Path(root_path).expanduser() / Path(relative_path)
    try:
        return source_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _serialize_function(
    function_info: FunctionInfo,
    file_path: str,
    symbol_type: str,
    root_path: str | Path,
) -> dict[str, object]:
    """把函数或方法转换为适合前端消费的字典。"""
    is_method = symbol_type == "method"
    return {
        "type": symbol_type,
        "name": function_info.name,
        "signature": build_signature(function_info, is_method=is_method),
        "path": file_path,
        "start_line": function_info.start_line,
        "end_line": function_info.end_line,
        "parameters": function_info.parameters,
        "class_name": function_info.class_name,
        "docstring": _description(function_info.docstring),
        "vscode_uri": build_vscode_uri(
            root_path,
            file_path,
            function_info.start_line,
        ),
    }


def _serialize_class(
    class_info: ClassInfo,
    file_path: str,
    root_path: str | Path,
) -> dict[str, object]:
    """把类信息转换为 JSON 可序列化结构。"""
    return {
        "type": "class",
        "name": class_info.name,
        "path": file_path,
        "start_line": class_info.start_line,
        "end_line": class_info.end_line,
        "docstring": _description(class_info.docstring),
        "vscode_uri": build_vscode_uri(
            root_path,
            file_path,
            class_info.start_line,
        ),
    }


def _serialize_file(
    file_info: FileInfo,
    root_path: str | Path,
) -> dict[str, object]:
    """完整序列化文件及其全部 classes、functions 和 methods。"""
    return {
        "type": "file",
        "name": Path(file_info.path).name,
        "path": file_info.path.replace("\\", "/"),
        "start_line": 1,
        "end_line": 1,
        "docstring": DEFAULT_DESCRIPTION,
        "source": _read_source(root_path, file_info.path),
        "vscode_uri": build_vscode_uri(root_path, file_info.path),
        "classes": [
            _serialize_class(class_info, file_info.path, root_path)
            for class_info in file_info.classes
        ],
        "functions": [
            _serialize_function(
                function_info,
                file_info.path,
                "function",
                root_path,
            )
            for function_info in file_info.functions
        ],
        "methods": [
            _serialize_function(
                method_info,
                file_info.path,
                "method",
                root_path,
            )
            for method_info in file_info.methods
        ],
    }


def repository_to_dict(repository: RepositoryInfo) -> dict[str, object]:
    """构建可同时用于 JSON 导出和页面渲染的数据模型。"""
    root_text = str(repository.root_path).rstrip("/\\")
    repository_name = Path(root_text).name or root_text or "Repository"
    return {
        "type": "repository",
        "name": repository_name,
        "root_path": str(repository.root_path),
        "files": [
            _serialize_file(file_info, repository.root_path)
            for file_info in repository.files
        ],
    }


def export_repository_json(
    repository: RepositoryInfo,
    output_path: str | Path,
) -> Path:
    """把仓库结构导出为 UTF-8 编码的 structure.json。"""
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(repository_to_dict(repository), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def _embed_json(data: dict[str, object]) -> str:
    """转义嵌入 script 标签的数据，避免内容提前闭合标签。"""
    return (
        json.dumps(data, ensure_ascii=False)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def render_visual_map(
    repository: RepositoryInfo,
    output_dir: str | Path,
) -> dict[str, Path]:
    """生成 STRUCTURE.md、structure.json 和可直接打开的 map.html。"""
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)

    data = repository_to_dict(repository)
    json_path = export_repository_json(repository, destination / "structure.json")

    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    html_content = template.replace(
        "__REPOSITORY_NAME__",
        escape(str(data["name"])),
    ).replace("__REPOSITORY_DATA__", _embed_json(data))

    html_path = destination / "map.html"
    html_path.write_text(html_content, encoding="utf-8")

    markdown_path = destination / "STRUCTURE.md"
    markdown_path.write_text(
        render_structure_markdown(repository),
        encoding="utf-8",
    )

    return {
        "json": json_path,
        "html": html_path,
        "markdown": markdown_path,
    }
