from repomosaic.core.symbols import FunctionInfo, ClassInfo, FileInfo
from repomosaic.semantic.prompts import build_function_prompt, build_class_prompt, build_file_prompt


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
    assert "approximately 2-3 sentences" in prompt
    assert "concrete operation" in prompt
    assert "how important inputs are used" in prompt
    assert "returned, modified, or produced" in prompt
    assert "validation, errors, or side effects" in prompt
    assert "only behavior supported by the provided source code" in prompt
    assert "without Markdown headings or bullet lists" in prompt


def test_build_method_prompt_includes_owning_class():
    method_info = FunctionInfo(
        name="move",
        start_line=2,
        end_line=3,
        parameters=["self", "position"],
        docstring="Move the robot.",
        class_name="RobotController",
    )

    prompt = build_function_prompt(
        function_info=method_info,
        source_code="def move(self, position):\n    self.position = position",
        language="en",
    )

    assert "analyzing a method" in prompt
    assert "Owning class:\nRobotController" in prompt


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
    assert "approximately 2-4 sentences" in prompt
    assert "important state" in prompt
    assert "key methods collectively do" in prompt
    assert "directly supported by the source" in prompt
    assert "without Markdown headings or bullet lists" in prompt


# 验证文件路径、类、函数、方法和目标语言都能正确进入 File Prompt
def test_build_file_prompt():
    file_info = FileInfo(
        path="repomosaic/core/parser.py",
        module_docstring="Parse Python modules into structured symbol metadata.",
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

    assert "repomosaic/core/parser.py" in prompt
    assert "PythonParser" in prompt
    assert "parse_python_file(file_path)" in prompt
    assert "extract_function_info(node)" in prompt
    assert "PythonParser.parse(self, source)" in prompt
    assert "zh-CN" in prompt
    assert "Parse Python modules into structured symbol metadata." in prompt
    assert "Parse a Python file." in prompt
    assert "approximately 3-5 sentences" in prompt
    assert "primary responsibility" in prompt
    assert "how those components work together" in prompt
    assert "inputs, outputs, dependencies, or side effects" in prompt
    assert "only when directly supported" in prompt
    assert "do not merely restate its filename or list symbols" in prompt
    assert "without Markdown headings or bullet lists" in prompt
