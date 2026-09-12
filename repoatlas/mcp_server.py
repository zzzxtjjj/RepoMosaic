"""RepoAtlas Agent API 的本地 stdio MCP 适配器。"""

import argparse
from collections.abc import Callable, Sequence
from pathlib import Path
import sys
from typing import Any, Literal, TypeVar

from repoatlas import agent_api
from repoatlas.core.analyzer import analyze_repository


SymbolKind = Literal["class", "function", "method"]
ToolResult = TypeVar("ToolResult")

EXPECTED_TOOL_ERRORS = (
    ValueError,
    FileNotFoundError,
    NotADirectoryError,
    OSError,
    SyntaxError,
    UnicodeError,
)


class MCPDependencyError(RuntimeError):
    """表示用户尚未安装可选 MCP SDK。"""


def _validate_repository_path(repository_path: str | Path) -> Path:
    """校验并固定 MCP server 唯一可访问的 repository root。"""
    root = Path(repository_path).expanduser().resolve()

    if not root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repository_path}")
    if not root.is_dir():
        raise NotADirectoryError(
            f"Repository path is not a directory: {repository_path}"
        )

    return root


class RepoAtlasMCPAdapter:
    """把固定仓库上的三个 MCP 操作委托给现有 Agent API。"""

    def __init__(self, repository_path: str | Path) -> None:
        self._repository_root = _validate_repository_path(repository_path)

    @property
    def repository_root(self) -> Path:
        """返回内部绑定路径；该值不会进入工具响应。"""
        return self._repository_root

    def get_repository_structure(self) -> dict[str, object]:
        """分析绑定仓库并返回不含完整源码的紧凑结构。"""
        repository = analyze_repository(self._repository_root)
        return agent_api.get_repository_structure(repository)

    def find_symbol(
        self,
        query: str,
        kind: SymbolKind | None = None,
        path: str | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        """在绑定仓库中搜索 symbol，保留 Agent API 的排序规则。"""
        repository = analyze_repository(self._repository_root)
        return agent_api.find_symbol(
            repository,
            query=query,
            kind=kind,
            path=path,
            limit=limit,
        )

    def get_symbol_source(self, symbol: dict[str, object]) -> dict[str, object]:
        """用 Agent API 返回的结构化 ref 安全地重新定位源码。"""
        return agent_api.get_symbol_source(
            repository_root=self._repository_root,
            symbol_ref=symbol,
        )


def _load_mcp_sdk() -> tuple[type[Any], type[Exception]]:
    """延迟加载可选 MCP SDK，避免影响普通 RepoAtlas 安装。"""
    try:
        from mcp.server import MCPServer
        from mcp.server.mcpserver.exceptions import ToolError
    except ImportError as error:
        raise MCPDependencyError(
            'MCP support is not installed. Install it with: pip install "repoatlas[mcp]"'
        ) from error

    return MCPServer, ToolError


def _clean_error_message(error: Exception, repository_root: Path) -> str:
    """移除工具错误中的绑定仓库绝对路径。"""
    message = str(error).strip() or error.__class__.__name__
    root_variants = {
        str(repository_root),
        repository_root.as_posix(),
        str(repository_root).replace("\\", "/"),
        str(repository_root).replace("/", "\\"),
    }
    for root_text in sorted(root_variants, key=len, reverse=True):
        if root_text:
            message = message.replace(root_text, "<repository>")
    return message


def _run_tool(
    operation: Callable[[], ToolResult],
    tool_error_type: type[Exception],
    repository_root: Path,
) -> ToolResult:
    """把预期输入/文件错误转换为 SDK 可识别的干净工具错误。"""
    try:
        return operation()
    except EXPECTED_TOOL_ERRORS as error:
        raise tool_error_type(
            _clean_error_message(error, repository_root)
        ) from error


def create_mcp_server(repository_path: str | Path) -> Any:
    """为单一 repository 创建恰好包含三个工具的 MCP server。"""
    adapter = RepoAtlasMCPAdapter(repository_path)
    server_type, tool_error_type = _load_mcp_sdk()
    server = server_type(
        "RepoAtlas",
        instructions=(
            "Inspect the repository bound when this local server started. "
            "Use find_symbol before get_symbol_source."
        ),
    )

    @server.tool()
    def get_repository_structure() -> dict[str, object]:
        """Return compact repository files and symbols without full source."""
        return _run_tool(
            adapter.get_repository_structure,
            tool_error_type,
            adapter.repository_root,
        )

    @server.tool()
    def find_symbol(
        query: str,
        kind: SymbolKind | None = None,
        path: str | None = None,
        limit: int = 50,
    ) -> dict[str, object]:
        """Find classes, functions, or methods in the bound repository."""
        return _run_tool(
            lambda: adapter.find_symbol(query, kind, path, limit),
            tool_error_type,
            adapter.repository_root,
        )

    @server.tool()
    def get_symbol_source(symbol: dict[str, object]) -> dict[str, object]:
        """Return source for a structured symbol ref from find_symbol."""
        return _run_tool(
            lambda: adapter.get_symbol_source(symbol),
            tool_error_type,
            adapter.repository_root,
        )

    return server


def build_parser() -> argparse.ArgumentParser:
    """创建只接受一个 repository path 的 MCP 启动参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="repoatlas-mcp",
        description="Serve RepoAtlas tools for one local repository over stdio.",
    )
    parser.add_argument(
        "repository_path",
        help="Repository path bound for the lifetime of this MCP server.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """校验仓库并启动本地 stdio MCP server。"""
    args = build_parser().parse_args(argv)

    try:
        server = create_mcp_server(args.repository_path)
    except (FileNotFoundError, NotADirectoryError, MCPDependencyError) as error:
        print(f"RepoAtlas MCP error: {error}", file=sys.stderr)
        return 2

    server.run(transport="stdio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
