from repomosaic.semantic.index import (
    build_summary_index,
    make_summary_key,
)
from repomosaic.semantic.models import SemanticSummary


# 验证语义摘要可以根据代码身份和语言建立唯一索引
def test_build_summary_index():
    chinese_summary = SemanticSummary(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        summary="解析 Python 文件并提取代码结构。",
        language="zh-CN",
        start_line=42,
    )

    english_summary = SemanticSummary(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        summary="Parses a Python file and extracts code structure.",
        language="en",
        start_line=42,
    )

    index = build_summary_index(
        [chinese_summary, english_summary]
    )

    chinese_key = make_summary_key(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        start_line=42,
        class_name=None,
        language="zh-CN",
    )

    english_key = make_summary_key(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        start_line=42,
        class_name=None,
        language="en",
    )

    assert chinese_key in index
    assert english_key in index

    assert index[chinese_key].summary == (
        "解析 Python 文件并提取代码结构。"
    )

    assert index[english_key].summary == (
        "Parses a Python file and extracts code structure."
    )


# 验证可以使用代码对象的身份信息直接查询对应摘要
def test_lookup_summary_by_symbol_identity():
    summary = SemanticSummary(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        summary="解析 Python 文件并提取代码结构。",
        language="zh-CN",
        start_line=42,
    )

    index = build_summary_index([summary])

    key = make_summary_key(
        target_type="function",
        file_path="repomosaic/core/parser.py",
        name="parse_python_file",
        start_line=42,
        class_name=None,
        language="zh-CN",
    )

    result = index.get(key)

    assert result is not None
    assert result.summary == "解析 Python 文件并提取代码结构。"


# 验证不存在对应摘要时，可以安全返回 None
def test_lookup_missing_summary_returns_none():
    index = build_summary_index([])

    key = make_summary_key(
        target_type="function",
        file_path="missing.py",
        name="missing_function",
        start_line=1,
        class_name=None,
        language="en",
    )

    assert index.get(key) is None