from repoatlas.core.symbols import FunctionInfo, ClassInfo, FileInfo
from repoatlas.semantic.summarizer import summarize_function, summarize_class, summarize_file
import pytest

# 模拟一个假的 LLM，避免测试时真的调用外部 API
class FakeLLM:
    def generate(self, prompt: str) -> str:
        return "  计算两个输入值之间的绝对差值。  "


# 验证 summarize_function 能调用 LLM 并返回清理后的摘要
def test_summarize_function_returns_clean_summary():
    function_info = FunctionInfo(
        name="calculate_distance",
        start_line=1,
        end_line=2,
        parameters=["x", "y"],
        docstring="Calculate distance.",
    )

    source_code = """def calculate_distance(x, y):
    return abs(x - y)"""

    result = summarize_function(
        function_info=function_info,
        source_code=source_code,
        language="zh-CN",
        llm=FakeLLM(),
    )

    assert result == "计算两个输入值之间的绝对差值。"


# 模拟 LLM，并保存收到的 prompt，方便测试 Summarizer 是否传入正确内容
class RecordingFakeLLM:
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "解析 Python 文件并返回结构化信息。"


# 验证函数名、源码和目标语言都被正确放入传给 LLM 的 prompt
def test_summarize_function_sends_correct_prompt():
    function_info = FunctionInfo(
        name="parse_python_file",
        start_line=10,
        end_line=20,
        parameters=["file_path"],
        docstring="Parse a Python file.",
    )

    source_code = """def parse_python_file(file_path):
    return file_path"""

    fake_llm = RecordingFakeLLM()

    summarize_function(
        function_info=function_info,
        source_code=source_code,
        language="zh-CN",
        llm=fake_llm,
    )

    assert fake_llm.received_prompt is not None
    assert "parse_python_file" in fake_llm.received_prompt
    assert "file_path" in fake_llm.received_prompt
    assert "return file_path" in fake_llm.received_prompt
    assert "zh-CN" in fake_llm.received_prompt
    assert "approximately 2-3 sentences" in fake_llm.received_prompt
    assert "inputs are used" in fake_llm.received_prompt
    assert "returned, modified, or produced" in fake_llm.received_prompt
    assert "Do not invent functionality" in fake_llm.received_prompt
    assert "without Markdown headings or bullet lists" in fake_llm.received_prompt


# 模拟 Class Summary 使用的大模型
class ClassFakeLLM:
    def generate(self, prompt: str) -> str:
        return "  负责机器人的运动控制与停止操作。  "


# 验证 summarize_class 能返回清理后的类职责摘要
def test_summarize_class_returns_clean_summary():
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

    result = summarize_class(
        class_info=class_info,
        source_code=source_code,
        language="zh-CN",
        llm=ClassFakeLLM(),
    )

    assert result == "负责机器人的运动控制与停止操作。"


# 模拟 LLM，并记录 Class Summarizer 实际传入的 prompt
class RecordingClassFakeLLM:
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "负责机器人控制。"


# 验证 summarize_class 将正确的类信息传给 LLM
def test_summarize_class_sends_correct_prompt():
    class_info = ClassInfo(
        name="RobotController",
        start_line=1,
        end_line=8,
        docstring="Control robot movement.",
    )

    source_code = """class RobotController:
    def move(self, position):
        pass"""

    fake_llm = RecordingClassFakeLLM()

    summarize_class(
        class_info=class_info,
        source_code=source_code,
        language="ja",
        llm=fake_llm,
    )

    assert fake_llm.received_prompt is not None
    assert "RobotController" in fake_llm.received_prompt
    assert "def move" in fake_llm.received_prompt
    assert "ja" in fake_llm.received_prompt
    assert "approximately 2-4 sentences" in fake_llm.received_prompt
    assert "important state" in fake_llm.received_prompt
    assert "key methods collectively do" in fake_llm.received_prompt


# 模拟 File Summary 使用的大模型
class FileFakeLLM:
    def generate(self, prompt: str) -> str:
        return "  负责解析 Python 文件并提取结构化代码符号信息。  "


# 验证 summarize_file 能返回清理后的文件职责摘要
def test_summarize_file_returns_clean_summary():
    file_info = FileInfo(
        path="repoatlas/core/parser.py",
        module_docstring="Parse Python modules into structured metadata.",
        classes=[],
        functions=[
            FunctionInfo(
                name="parse_python_file",
                start_line=1,
                end_line=10,
                parameters=["file_path"],
                docstring="Parse a Python file.",
            )
        ],
        methods=[],
    )

    result = summarize_file(
        file_info=file_info,
        language="zh-CN",
        llm=FileFakeLLM(),
    )

    assert result == "负责解析 Python 文件并提取结构化代码符号信息。"


# 模拟 LLM，并记录 File Summarizer 实际收到的 prompt
class RecordingFileFakeLLM:
    def __init__(self):
        self.received_prompt = None

    def generate(self, prompt: str) -> str:
        self.received_prompt = prompt
        return "负责 Python 代码解析。"


# 验证 summarize_file 将正确的文件结构信息传给 LLM
def test_summarize_file_sends_correct_prompt():
    file_info = FileInfo(
        path="repoatlas/core/parser.py",
        module_docstring="Parse Python modules into structured metadata.",
        classes=[],
        functions=[
            FunctionInfo(
                name="parse_python_file",
                start_line=1,
                end_line=10,
                parameters=["file_path"],
                docstring="Parse a Python file.",
            )
        ],
        methods=[],
    )

    fake_llm = RecordingFileFakeLLM()

    summarize_file(
        file_info=file_info,
        language="ja",
        llm=fake_llm,
    )

    assert fake_llm.received_prompt is not None
    assert "repoatlas/core/parser.py" in fake_llm.received_prompt
    assert "parse_python_file(file_path)" in fake_llm.received_prompt
    assert "ja" in fake_llm.received_prompt
    assert "Parse Python modules into structured metadata." in fake_llm.received_prompt
    assert "approximately 3-5 sentences" in fake_llm.received_prompt
    assert "how those components work together" in fake_llm.received_prompt
    assert "dependencies, or side effects" in fake_llm.received_prompt


from repoatlas.core.symbols import (
    ClassInfo,
    FileInfo,
    FunctionInfo,
    RepositoryInfo,
)
from repoatlas.semantic.summarizer import summarize_repository


# 模拟整仓语义分析使用的大模型，并记录收到的所有 Prompt
class RepositoryFakeLLM:
    def __init__(self):
        self.prompts = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "Generated summary."


# 验证 summarize_repository 能为文件、类、函数和方法分别生成语义摘要
def test_summarize_repository(tmp_path):
    source_code = """class Robot:
    \"\"\"Control the robot.\"\"\"

    def move(self, x):
        \"\"\"Move the robot.\"\"\"
        return x

def helper(value):
    \"\"\"Return the input value.\"\"\"
    return value
"""

    source_file = tmp_path / "sample.py"
    source_file.write_text(source_code, encoding="utf-8")

    class_info = ClassInfo(
        name="Robot",
        start_line=1,
        end_line=6,
        docstring="Control the robot.",
    )

    method_info = FunctionInfo(
        name="move",
        start_line=4,
        end_line=6,
        parameters=["self", "x"],
        docstring="Move the robot.",
        class_name="Robot",
    )

    function_info = FunctionInfo(
        name="helper",
        start_line=8,
        end_line=10,
        parameters=["value"],
        docstring="Return the input value.",
    )

    file_info = FileInfo(
        path="sample.py",
        classes=[class_info],
        functions=[function_info],
        methods=[method_info],
    )

    repository = RepositoryInfo(
        root_path=tmp_path.as_posix(),
        files=[file_info],
    )

    fake_llm = RepositoryFakeLLM()

    summaries = summarize_repository(
        repository=repository,
        language="zh-CN",
        llm=fake_llm,
    )

    assert len(summaries) == 4

    assert [summary.target_type for summary in summaries] == [
        "file",
        "class",
        "function",
        "method",
    ]

    file_summary = summaries[0]
    assert file_summary.file_path == "sample.py"
    assert file_summary.name == "sample.py"
    assert file_summary.language == "zh-CN"

    class_summary = summaries[1]
    assert class_summary.name == "Robot"
    assert class_summary.start_line == 1
    assert class_summary.target_type == "class"

    function_summary = summaries[2]
    assert function_summary.name == "helper"
    assert function_summary.start_line == 8
    assert function_summary.target_type == "function"

    method_summary = summaries[3]
    assert method_summary.name == "move"
    assert method_summary.start_line == 4
    assert method_summary.class_name == "Robot"
    assert method_summary.target_type == "method"

    assert len(fake_llm.prompts) == 4


# 验证不支持的语言会在任何 LLM 调用之前被拒绝
def test_summarize_repository_rejects_unsupported_language(
    tmp_path,
):
    source_file = tmp_path / "main.py"

    source_file.write_text(
        """
def hello():
    return "hello"
""".strip(),
        encoding="utf-8",
    )

    repository = RepositoryInfo(
        root_path=tmp_path.as_posix(),
        files=[
            FileInfo(
                path="main.py",
                functions=[
                    FunctionInfo(
                        name="hello",
                        start_line=1,
                        end_line=2,
                        parameters=[],
                        docstring="",
                    )
                ],
                classes=[],
                methods=[],
            )
        ],
    )

    class FailIfCalledLLM:
        def generate(self, prompt: str) -> str:
            raise AssertionError(
                "LLM should not be called for unsupported language"
            )

    with pytest.raises(
        ValueError,
        match="Unsupported language",
    ):
        summarize_repository(
            repository=repository,
            language="ru",
            llm=FailIfCalledLLM(),
        )
