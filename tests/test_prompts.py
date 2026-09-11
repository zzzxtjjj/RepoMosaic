from repoatlas.core.symbols import FunctionInfo, ClassInfo, FileInfo
from repoatlas.semantic.prompts import build_function_prompt, build_class_prompt, build_file_prompt


# 验证函数信息、源码和语言能够正确进入 Prompt
def test_build_function_prompt():
    function_info = FunctionInfo(
        name="calculate_distance",
        start_line=1,
        end_line=2,
        parameters=["x", "y"],
        docstring="Calculate distance.",
    )

    source_code = """def calculate_distance(x, y):
    return abs(x - y)"""

    prompt = build_function_prompt(
        function_info=function_info,
        source_code=source_code,
        language="zh-CN",
    )

    assert "calculate_distance" in prompt
    assert "x, y" in prompt
    assert "return abs(x - y)" in prompt
    assert "zh-CN" in prompt


# 验证类名、源码和目标语言能够正确进入 Class Prompt
def test_build_class_prompt():
    class_info = ClassInfo(
        name="RobotController",
        start_line=1,
        end_line=8,
        docstring="Control robot movement.",
    )

    source_code = """class RobotController:
    def move(self, position):
        pass

    def stop(self):
        pass"""

    prompt = build_class_prompt(
        class_info=class_info,
        source_code=source_code,
        language="zh-CN",
    )

    assert "RobotController" in prompt
    assert "def move" in prompt
    assert "def stop" in prompt
    assert "zh-CN" in prompt
    assert "overall responsibility" in prompt


# 验证文件路径、类、函数、方法和目标语言都能正确进入 File Prompt
def test_build_file_prompt():
    file_info = FileInfo(
        path="repoatlas/core/parser.py",
        classes=[
            ClassInfo(
                name="PythonParser",
                start_line=1,
                end_line=20,
                docstring="Parse Python source code.",
            )
        ],
        functions=[
            FunctionInfo(
                name="parse_python_file",
                start_line=22,
                end_line=40,
                parameters=["file_path"],
                docstring="Parse a Python file.",
            ),
            FunctionInfo(
                name="extract_function_info",
                start_line=42,
                end_line=55,
                parameters=["node"],
                docstring="Extract function metadata.",
            ),
        ],
        methods=[
            FunctionInfo(
                name="parse",
                start_line=5,
                end_line=15,
                parameters=["self", "source"],
                docstring="Parse source code.",
                class_name="PythonParser",
            )
        ],
    )

    prompt = build_file_prompt(
        file_info=file_info,
        language="zh-CN",
    )

    assert "repoatlas/core/parser.py" in prompt
    assert "PythonParser" in prompt
    assert "parse_python_file(file_path)" in prompt
    assert "extract_function_info(node)" in prompt
    assert "PythonParser.parse(self, source)" in prompt
    assert "zh-CN" in prompt
