import ast
from pathlib import Path
from repomosaic.core.symbols import FunctionInfo, ClassInfo, FileInfo


# 解析单个 Python 文件，遍历 AST，并统一返回其中的顶层函数、类和类方法的结构化信息
def parse_python_file(file_path: str | Path) -> FileInfo:

    path = Path(file_path)

    source = path.read_text(encoding="utf-8")

    tree = ast.parse(source)

    functions: list[FunctionInfo] = []
    classes: list[ClassInfo] = []
    methods: list[FunctionInfo] = []
    module_docstring = ast.get_docstring(tree) or ""

    for node in tree.body:

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(extract_function_info(node))

        if isinstance(node, ast.ClassDef):
            classes.append(extract_class_info(node))

            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    method_info = extract_function_info(child)
                    method_info.class_name = node.name
                    methods.append(method_info)

    return FileInfo(
        path=path.as_posix(),
        functions=functions,
        classes=classes,
        methods=methods,
        module_docstring=module_docstring
    )


# 提取信息
def extract_function_info(node: ast.FunctionDef | ast.AsyncFunctionDef) -> FunctionInfo:

    return FunctionInfo(
        name=node.name,
        start_line=node.lineno,
        end_line=node.end_lineno,
        parameters=extract_parameters(node.args),
        docstring=extract_docstring(node),
    )


# 根据函数结构化信息生成适合思维导图展示的函数签名，并隐藏 self / cls
def build_signature(function_info: FunctionInfo, is_method: bool = False) -> str:
    parameters = function_info.parameters

    if is_method and parameters:
        first_parameter = parameters[0]

        if first_parameter in ("self", "cls"):
            parameters = parameters[1:]

    parameter_text = ", ".join(parameters)

    return f'{function_info.name}({parameter_text})'


# 提取函数、方法或类中的 docstring；如果没有 docstring，则返回空字符串
def extract_docstring(node: ast.AST) -> str:
    docstring = ast.get_docstring(node)
    if docstring is None:
        return ""

    return docstring


# 从类的 AST 节点中提取类名、起止行号和 docstring 等结构化信息
def extract_class_info(node: ast.ClassDef) -> ClassInfo:
    return ClassInfo(
        name=node.name,
        start_line=node.lineno,
        end_line=node.end_lineno,
        docstring=extract_docstring(node),
    )


# 从 Python AST 的函数参数节点中提取完整的参数列表，包括位置参数、*args 和 **kwargs
def extract_parameters(arguments: ast.arguments) -> list[str]:
    parameters: list[str] = []

    for argument in arguments.posonlyargs:
        parameters.append(argument.arg)

    if arguments.posonlyargs:
        parameters.append("/")

    for argument in arguments.args:
        parameters.append(argument.arg)

    if arguments.vararg is not None:
        parameters.append(f"*{arguments.vararg.arg}")

    if arguments.kwonlyargs and arguments.vararg is None:
        parameters.append("*")

    for argument in arguments.kwonlyargs:
        parameters.append(argument.arg)

    if arguments.kwarg is not None:
        parameters.append(f"**{arguments.kwarg.arg}")

    return parameters
