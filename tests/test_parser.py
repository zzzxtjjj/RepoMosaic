from repoatlas.parser import parse_python_file, build_signature


# 测试 Python 文件解析功能：验证类、普通函数、异步函数、方法、参数、行号和 docstring 是否能被正确提取
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

    class_info = result["classes"][0]
    method_info = result["methods"][0]
    function_info = result["functions"][0]
    async_function_info = result["functions"][1]

    assert class_info["name"] == "Robot"
    assert class_info["docstring"] == "Control the robot."
    assert class_info["start_line"] == 2
    assert class_info["end_line"] == 7

    assert method_info["name"] == "move"
    assert method_info["class_name"] == "Robot"
    assert method_info["parameters"] == ["self"]
    assert method_info["docstring"] == "Move the robot."

    assert function_info["name"] == "calculate_distance"
    assert function_info["parameters"] == []
    assert function_info["docstring"] == "Calculate the distance."

    assert async_function_info["name"] == "fetch_data"
    assert async_function_info["parameters"] == ["url"]
    assert async_function_info["docstring"] == "Fetch data from a URL."


# 测试函数签名生成：普通函数保留所有参数，实例方法隐藏 self，类方法隐藏 cls，静态方法保留真实参数
def test_build_signature():

    normal_function = {
        "name": "add",
        "parameters": ["a", "b"],
    }

    instance_method = {
        "name": "move",
        "parameters": ["self", "position", "speed"],
    }

    class_method = {
        "name": "create",
        "parameters": ["cls", "config"],
    }

    static_method = {
        "name": "calculate",
        "parameters": ["x", "y"],
    }

    assert build_signature(normal_function) == "add(a, b)"

    assert build_signature(instance_method, is_method=True) == "move(position, speed)"

    assert build_signature(class_method, is_method=True) == "create(config)"

    assert build_signature(static_method, is_method=True) == "calculate(x, y)"