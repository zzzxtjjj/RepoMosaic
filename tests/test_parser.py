from repoatlas.core.parser import parse_python_file, build_signature
from repoatlas.core.symbols import FunctionInfo


# 测试 Python 文件解析：验证类、普通函数、异步函数、方法、参数、行号和 docstring
def test_parse_python_file(tmp_path):
    sample = tmp_path / "sample.py"

    source = """
class Robot:
    \"\"\"Control the robot.\"\"\"

    def move(self):
        \"\"\"Move the robot.\"\"\"
        pass

def calculate_distance():
    \"\"\"Calculate the distance.\"\"\"
    pass

async def fetch_data(url):
    \"\"\"Fetch data from a URL.\"\"\"
    pass
"""

    sample.write_text(source, encoding="utf-8")

    result = parse_python_file(sample)

    class_info = result.classes[0]
    method_info = result.methods[0]
    function_info = result.functions[0]
    async_function_info = result.functions[1]

    # 检查类信息
    assert class_info.name == "Robot"
    assert class_info.docstring == "Control the robot."
    assert class_info.start_line == 2
    assert class_info.end_line == 7

    # 检查类方法
    assert method_info.name == "move"
    assert method_info.class_name == "Robot"
    assert method_info.parameters == ["self"]
    assert method_info.docstring == "Move the robot."

    # 检查普通函数
    assert function_info.name == "calculate_distance"
    assert function_info.parameters == []
    assert function_info.docstring == "Calculate the distance."

    # 检查异步函数
    assert async_function_info.name == "fetch_data"
    assert async_function_info.parameters == ["url"]
    assert async_function_info.docstring == "Fetch data from a URL."


# 测试函数签名生成：普通函数保留参数，实例方法隐藏 self，类方法隐藏 cls
def test_build_signature():
    normal_function = FunctionInfo(
        name="add",
        start_line=1,
        end_line=2,
        parameters=["a", "b"],
        docstring="",
    )

    instance_method = FunctionInfo(
        name="move",
        start_line=1,
        end_line=2,
        parameters=["self", "position", "speed"],
        docstring="",
        class_name="Robot",
    )

    class_method = FunctionInfo(
        name="create",
        start_line=1,
        end_line=2,
        parameters=["cls", "config"],
        docstring="",
        class_name="Robot",
    )

    static_method = FunctionInfo(
        name="calculate",
        start_line=1,
        end_line=2,
        parameters=["x", "y"],
        docstring="",
        class_name="Math",
    )

    assert build_signature(normal_function) == "add(a, b)"
    assert build_signature(
        instance_method,
        is_method=True,
    ) == "move(position, speed)"

    assert build_signature(
        class_method,
        is_method=True,
    ) == "create(config)"

    assert build_signature(
        static_method,
        is_method=True,
    ) == "calculate(x, y)"


# 验证 parser 能提取 Python 文件顶部的模块级 docstring
def test_parse_python_file_extracts_module_docstring(tmp_path):
    file_path = tmp_path / "utils.py"

    file_path.write_text(
        '''
"""Utility functions used by the sample repository."""

def calculate_distance(start, end):
    return abs(end - start)
'''.strip(),
        encoding="utf-8",
    )

    file_info = parse_python_file(file_path)

    assert (
        file_info.module_docstring
        == "Utility functions used by the sample repository."
    )


# 验证没有模块级 docstring 时，FileInfo 使用空字符串
def test_parse_python_file_without_module_docstring(tmp_path):
    file_path = tmp_path / "utils.py"

    file_path.write_text(
        """
def calculate_distance(start, end):
    return abs(end - start)
""".strip(),
        encoding="utf-8",
    )

    file_info = parse_python_file(file_path)

    assert file_info.module_docstring == ""