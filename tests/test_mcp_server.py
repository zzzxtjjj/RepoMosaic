import inspect
from pathlib import Path

import pytest

import repomosaic.mcp_server as mcp_server


class FakeToolError(Exception):
    """模拟官方 SDK 的可恢复 tool-level error。"""


class FakeMCPServer:
    """记录 tool decorator 注册结果，不启动真实 MCP transport。"""

    def __init__(self, name, **kwargs):
        self.name = name
        self.options = kwargs
        self.tools = {}
        self.run_kwargs = None

    def tool(self):
        def register(function):
            self.tools[function.__name__] = function
            return function

        return register

    def run(self, **kwargs):
        self.run_kwargs = kwargs


@pytest.fixture
def fake_sdk(monkeypatch):
    monkeypatch.setattr(
        mcp_server,
        "_load_mcp_sdk",
        lambda: (FakeMCPServer, FakeToolError),
    )


def test_adapter_calls_agent_api_for_repository_structure(tmp_path, monkeypatch):
    repository = object()
    expected = {"repository": "sample", "files": []}
    calls = []

    monkeypatch.setattr(
        mcp_server,
        "analyze_repository",
        lambda root: calls.append(("analyze", root)) or repository,
    )
    monkeypatch.setattr(
        mcp_server.agent_api,
        "get_repository_structure",
        lambda value: calls.append(("structure", value)) or expected,
    )

    adapter = mcp_server.RepoMosaicMCPAdapter(tmp_path)

    assert adapter.get_repository_structure() == expected
    assert calls == [
        ("analyze", tmp_path.resolve()),
        ("structure", repository),
    ]


def test_find_symbol_passes_filters_and_limit_to_agent_api(tmp_path, monkeypatch):
    repository = object()
    captured = {}
    expected = {"query": "move", "matches": [], "truncated": False}

    monkeypatch.setattr(mcp_server, "analyze_repository", lambda root: repository)

    def fake_find(value, **kwargs):
        captured["repository"] = value
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(mcp_server.agent_api, "find_symbol", fake_find)
    adapter = mcp_server.RepoMosaicMCPAdapter(tmp_path)

    result = adapter.find_symbol(
        "move",
        kind="method",
        path="robot.py",
        limit=7,
    )

    assert result == expected
    assert captured == {
        "repository": repository,
        "query": "move",
        "kind": "method",
        "path": "robot.py",
        "limit": 7,
    }


def test_get_symbol_source_passes_structured_ref_to_agent_api(tmp_path, monkeypatch):
    symbol = {
        "path": "robot.py",
        "kind": "method",
        "name": "move",
        "start_line": 10,
    }
    expected = {"symbol": symbol, "source": "def move(): ..."}
    captured = {}

    def fake_get_source(**kwargs):
        captured.update(kwargs)
        return expected

    monkeypatch.setattr(mcp_server.agent_api, "get_symbol_source", fake_get_source)
    adapter = mcp_server.RepoMosaicMCPAdapter(tmp_path)

    assert adapter.get_symbol_source(symbol) == expected
    assert captured == {
        "repository_root": tmp_path.resolve(),
        "symbol_ref": symbol,
    }


def test_server_registers_exactly_three_bound_repository_tools(
    tmp_path,
    fake_sdk,
):
    server = mcp_server.create_mcp_server(tmp_path)

    assert set(server.tools) == {
        "get_repository_structure",
        "find_symbol",
        "get_symbol_source",
    }
    for tool in server.tools.values():
        assert "repository" not in inspect.signature(tool).parameters
        assert "repository_path" not in inspect.signature(tool).parameters
        assert "repository_root" not in inspect.signature(tool).parameters


def test_registered_tools_return_structured_data(tmp_path, fake_sdk, monkeypatch):
    expected = {"repository": "sample", "files": []}
    monkeypatch.setattr(
        mcp_server.RepoMosaicMCPAdapter,
        "get_repository_structure",
        lambda self: expected,
    )
    server = mcp_server.create_mcp_server(tmp_path)

    assert server.tools["get_repository_structure"]() == expected


def test_expected_input_error_becomes_clean_tool_error(
    tmp_path,
    fake_sdk,
    monkeypatch,
):
    monkeypatch.setattr(
        mcp_server.RepoMosaicMCPAdapter,
        "find_symbol",
        lambda self, query, kind, path, limit: (_ for _ in ()).throw(
            ValueError(f"Invalid query under {self.repository_root}")
        ),
    )
    server = mcp_server.create_mcp_server(tmp_path)

    with pytest.raises(FakeToolError) as caught:
        server.tools["find_symbol"]("bad")

    assert "Invalid query" in str(caught.value)
    assert str(tmp_path.resolve()) not in str(caught.value)
    assert "<repository>" in str(caught.value)


def test_unexpected_programming_error_is_not_hidden(
    tmp_path,
    fake_sdk,
    monkeypatch,
):
    monkeypatch.setattr(
        mcp_server.RepoMosaicMCPAdapter,
        "get_repository_structure",
        lambda self: (_ for _ in ()).throw(RuntimeError("programming bug")),
    )
    server = mcp_server.create_mcp_server(tmp_path)

    with pytest.raises(RuntimeError, match="programming bug"):
        server.tools["get_repository_structure"]()


def test_invalid_repository_is_rejected_before_loading_mcp(tmp_path, monkeypatch):
    loaded = False

    def fake_load():
        nonlocal loaded
        loaded = True
        return FakeMCPServer, FakeToolError

    monkeypatch.setattr(mcp_server, "_load_mcp_sdk", fake_load)

    with pytest.raises(FileNotFoundError):
        mcp_server.create_mcp_server(tmp_path / "missing")

    assert loaded is False


def test_missing_optional_sdk_has_actionable_error(monkeypatch):
    def reject_mcp_import(name, *args, **kwargs):
        if name.startswith("mcp"):
            raise ImportError("mcp is unavailable")
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", reject_mcp_import)

    with pytest.raises(
        mcp_server.MCPDependencyError,
        match=r'pip install "repomosaic\[mcp\]"',
    ):
        mcp_server._load_mcp_sdk()


def test_module_import_does_not_require_mcp_sdk():
    source = Path(mcp_server.__file__).read_text(encoding="utf-8")

    assert "from mcp.server import MCPServer" in source
    assert source.index("def _load_mcp_sdk") < source.index(
        "from mcp.server import MCPServer"
    )


def test_main_runs_stdio_for_bound_repository(tmp_path, monkeypatch):
    server = FakeMCPServer("RepoMosaic")
    captured = {}

    def fake_create(path):
        captured["path"] = path
        return server

    monkeypatch.setattr(mcp_server, "create_mcp_server", fake_create)

    assert mcp_server.main([str(tmp_path)]) == 0
    assert captured["path"] == str(tmp_path)
    assert server.run_kwargs == {"transport": "stdio"}
