from repoatlas.agent_api import (
    _serialize_symbol,
    find_symbol,
    get_repository_structure,
    get_symbol_source,
)
from repoatlas.core.analyzer import analyze_repository
from repoatlas.core.symbols import (
    ClassInfo,
    FileInfo,
    FunctionInfo,
    RepositoryInfo,
)


def test_serialize_class_symbol():
    class_info = ClassInfo(
        name="RobotController",
        start_line=1,
        end_line=20,
        docstring="Control the robot.",
    )

    result = _serialize_symbol(
        file_path="robot.py",
        kind="class",
        symbol=class_info,
    )

    assert result["kind"] == "class"
    assert result["name"] == "RobotController"
    assert result["qualified_name"] == "RobotController"
    assert result["path"] == "robot.py"
    assert result["signature"] == "RobotController"
    assert result["start_line"] == 1
    assert result["end_line"] == 20
    assert result["docstring"] == "Control the robot."

    assert result["ref"] == {
        "path": "robot.py",
        "kind": "class",
        "name": "RobotController",
        "start_line": 1,
    }


def test_serialize_function_symbol():
    function_info = FunctionInfo(
        name="parse_file",
        start_line=5,
        end_line=12,
        parameters=["file_path"],
        docstring="Parse a file.",
    )

    result = _serialize_symbol(
        file_path="parser.py",
        kind="function",
        symbol=function_info,
    )

    assert result["kind"] == "function"
    assert result["name"] == "parse_file"
    assert result["qualified_name"] == "parse_file"
    assert result["signature"] == "parse_file(file_path)"

    assert result["ref"] == {
        "path": "parser.py",
        "kind": "function",
        "name": "parse_file",
        "start_line": 5,
    }


def test_serialize_method_symbol():
    method_info = FunctionInfo(
        name="move",
        start_line=10,
        end_line=18,
        parameters=["self", "target"],
        docstring="Move to target.",
        class_name="RobotController",
    )

    result = _serialize_symbol(
        file_path="robot.py",
        kind="method",
        symbol=method_info,
    )

    assert result["kind"] == "method"
    assert result["name"] == "move"
    assert result["qualified_name"] == "RobotController.move"
    assert result["signature"] == "RobotController.move(target)"

    assert result["ref"] == {
        "path": "robot.py",
        "kind": "method",
        "name": "move",
        "start_line": 10,
    }


def test_get_repository_structure_orders_files_and_symbols():
    repository = RepositoryInfo(
        root_path="D:/projects/sample_repo",
        files=[
            FileInfo(
                path="z.py",
                functions=[],
                classes=[],
                methods=[],
                module_docstring="Z module.",
            ),
            FileInfo(
                path="robot.py",
                functions=[
                    FunctionInfo(
                        name="helper",
                        start_line=30,
                        end_line=35,
                        parameters=[],
                        docstring="Helper function.",
                    )
                ],
                classes=[
                    ClassInfo(
                        name="RobotController",
                        start_line=5,
                        end_line=25,
                        docstring="Robot controller.",
                    )
                ],
                methods=[
                    FunctionInfo(
                        name="move",
                        start_line=10,
                        end_line=15,
                        parameters=["self", "target"],
                        docstring="Move robot.",
                        class_name="RobotController",
                    )
                ],
                module_docstring="Robot module.",
            ),
        ],
    )

    result = get_repository_structure(repository)

    assert result["repository"] == "sample_repo"

    assert [
        file_info["path"]
        for file_info in result["files"]
    ] == [
        "robot.py",
        "z.py",
    ]

    robot_file = result["files"][0]

    assert robot_file["module_docstring"] == "Robot module."

    assert [
        symbol["qualified_name"]
        for symbol in robot_file["symbols"]
    ] == [
        "RobotController",
        "RobotController.move",
        "helper",
    ]


def test_get_repository_structure_does_not_include_source():
    repository = RepositoryInfo(
        root_path="D:/projects/sample_repo",
        files=[
            FileInfo(
                path="main.py",
                functions=[],
                classes=[],
                methods=[],
                module_docstring="Main module.",
            )
        ],
    )

    result = get_repository_structure(repository)

    file_result = result["files"][0]

    assert "source" not in file_result


def _make_search_repository():
    return RepositoryInfo(
        root_path="D:/projects/sample_repo",
        files=[
            FileInfo(
                path="robot.py",
                classes=[
                    ClassInfo(
                        name="RobotController",
                        start_line=1,
                        end_line=30,
                        docstring="Robot controller.",
                    )
                ],
                functions=[
                    FunctionInfo(
                        name="move_robot",
                        start_line=40,
                        end_line=45,
                        parameters=["target"],
                        docstring="Move a robot.",
                    )
                ],
                methods=[
                    FunctionInfo(
                        name="move",
                        start_line=10,
                        end_line=15,
                        parameters=["self", "target"],
                        docstring="Move to target.",
                        class_name="RobotController",
                    )
                ],
                module_docstring="Robot module.",
            ),
            FileInfo(
                path="source.py",
                classes=[],
                functions=[
                    FunctionInfo(
                        name="extract_source_lines",
                        start_line=5,
                        end_line=12,
                        parameters=[
                            "file_path",
                            "start_line",
                            "end_line",
                        ],
                        docstring="Extract source lines.",
                    ),
                    FunctionInfo(
                        name="source",
                        start_line=20,
                        end_line=22,
                        parameters=[],
                        docstring="Exact source.",
                    ),
                ],
                methods=[],
                module_docstring="Source utilities.",
            ),
        ],
    )


def test_find_symbol_exact_match_ranks_first():
    repository = _make_search_repository()

    result = find_symbol(
        repository,
        query="source",
    )

    assert result["matches"][0]["name"] == "source"
    assert result["truncated"] is False


def test_find_symbol_matches_qualified_method_name():
    repository = _make_search_repository()

    result = find_symbol(
        repository,
        query="RobotController.move",
    )

    assert len(result["matches"]) == 1
    assert result["matches"][0]["kind"] == "method"
    assert (
        result["matches"][0]["qualified_name"]
        == "RobotController.move"
    )


def test_find_symbol_filters_by_kind():
    repository = _make_search_repository()

    result = find_symbol(
        repository,
        query="move",
        kind="method",
    )

    assert len(result["matches"]) == 1
    assert result["matches"][0]["name"] == "move"


def test_find_symbol_filters_by_path():
    repository = _make_search_repository()

    result = find_symbol(
        repository,
        query="source",
        path="source.py",
    )

    assert all(
        match["path"] == "source.py"
        for match in result["matches"]
    )


def test_find_symbol_limit_sets_truncated():
    repository = _make_search_repository()

    result = find_symbol(
        repository,
        query="move",
        limit=1,
    )

    assert len(result["matches"]) == 1
    assert result["truncated"] is True


def test_find_symbol_rejects_empty_query():
    repository = _make_search_repository()

    try:
        find_symbol(
            repository,
            query="   ",
        )
    except ValueError as error:
        assert str(error) == "query must not be empty"
    else:
        raise AssertionError("Expected ValueError")


def test_find_symbol_rejects_invalid_kind():
    repository = _make_search_repository()

    try:
        find_symbol(
            repository,
            query="move",
            kind="variable",
        )
    except ValueError as error:
        assert "Unsupported symbol kind" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_get_symbol_source_returns_function_source(tmp_path):
    source = '''\
"""Sample module."""


def hello(name):
    """Say hello."""
    return f"Hello, {name}"
'''

    file_path = tmp_path / "sample.py"
    file_path.write_text(source, encoding="utf-8")

    repository = analyze_repository(tmp_path)

    search_result = find_symbol(
        repository,
        query="hello",
        kind="function",
    )

    symbol_ref = search_result["matches"][0]["ref"]

    result = get_symbol_source(
        repository_root=tmp_path,
        symbol_ref=symbol_ref,
    )

    assert result["symbol"]["name"] == "hello"
    assert result["symbol"]["kind"] == "function"
    assert result["symbol"]["qualified_name"] == "hello"
    assert result["symbol"]["signature"] == "hello(name)"

    assert result["source"] == (
        'def hello(name):\n'
        '    """Say hello."""\n'
        '    return f"Hello, {name}"'
    )


def test_get_symbol_source_returns_method_source(tmp_path):
    source = '''\
class RobotController:
    """Control a robot."""

    def move(self, target):
        """Move to target."""
        return target
'''

    file_path = tmp_path / "robot.py"
    file_path.write_text(source, encoding="utf-8")

    repository = analyze_repository(tmp_path)

    search_result = find_symbol(
        repository,
        query="RobotController.move",
        kind="method",
    )

    symbol_ref = search_result["matches"][0]["ref"]

    result = get_symbol_source(
        repository_root=tmp_path,
        symbol_ref=symbol_ref,
    )

    assert result["symbol"]["kind"] == "method"
    assert result["symbol"]["name"] == "move"
    assert (
        result["symbol"]["qualified_name"]
        == "RobotController.move"
    )
    assert (
        result["symbol"]["signature"]
        == "RobotController.move(target)"
    )

    assert result["source"] == (
        "    def move(self, target):\n"
        '        """Move to target."""\n'
        "        return target"
    )


def test_get_symbol_source_rejects_stale_ref(tmp_path):
    source = '''\
def hello():
    return "hello"
'''

    file_path = tmp_path / "sample.py"
    file_path.write_text(source, encoding="utf-8")

    repository = analyze_repository(tmp_path)

    search_result = find_symbol(
        repository,
        query="hello",
    )

    symbol_ref = search_result["matches"][0]["ref"].copy()

    # 模拟旧引用：symbol 原来的起始行已经不再正确
    symbol_ref["start_line"] = 999

    try:
        get_symbol_source(
            repository_root=tmp_path,
            symbol_ref=symbol_ref,
        )
    except ValueError as error:
        assert "stale" in str(error).lower()
        assert "find_symbol" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_get_symbol_source_rejects_repository_escape(tmp_path):
    repository_root = tmp_path / "repo"
    repository_root.mkdir()

    outside_file = tmp_path / "outside.py"
    outside_file.write_text(
        "def secret():\n    return 'secret'\n",
        encoding="utf-8",
    )

    symbol_ref = {
        "path": "../outside.py",
        "kind": "function",
        "name": "secret",
        "start_line": 1,
    }

    try:
        get_symbol_source(
            repository_root=repository_root,
            symbol_ref=symbol_ref,
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Expected ValueError")


def test_get_symbol_source_rejects_missing_ref_fields(tmp_path):
    symbol_ref = {
        "path": "sample.py",
        "kind": "function",
    }

    try:
        get_symbol_source(
            repository_root=tmp_path,
            symbol_ref=symbol_ref,
        )
    except ValueError as error:
        assert "missing required fields" in str(error)
    else:
        raise AssertionError("Expected ValueError")


def test_get_symbol_source_rejects_invalid_kind(tmp_path):
    symbol_ref = {
        "path": "sample.py",
        "kind": "variable",
        "name": "value",
        "start_line": 1,
    }

    try:
        get_symbol_source(
            repository_root=tmp_path,
            symbol_ref=symbol_ref,
        )
    except ValueError as error:
        assert "Unsupported symbol kind" in str(error)
    else:
        raise AssertionError("Expected ValueError")