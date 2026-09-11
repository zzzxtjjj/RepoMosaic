from repoatlas.core.symbols import FunctionInfo, ClassInfo, FileInfo


# 根据函数信息、函数源码和目标语言，构造函数总结提示词
def build_function_prompt(
    function_info: FunctionInfo,
    source_code: str,
    language: str,
) -> str:
    parameters = ", ".join(function_info.parameters)

    prompt = f"""
You are analyzing a function in a source code repository.

Function name:
{function_info.name}

Parameters:
{parameters}

Source code:
```python
{source_code}
```

Task:
Summarize the responsibility of this function in one concise sentence.

Output language:
{language}

Rules:
- Describe only behavior supported by the provided source code.
- Do not invent functionality.
- Do not translate function names, parameter names, file paths, or code identifiers.
- Do not include Markdown formatting.
- Return only the summary sentence.
"""

    return prompt.strip()


# 根据类信息、类源码和目标语言，构造类职责总结提示词
def build_class_prompt(
    class_info: ClassInfo,
    source_code: str,
    language: str,
) -> str:
    prompt = f"""
You are analyzing a class in a source code repository.

Class name:
{class_info.name}

Source code:
```python
{source_code}
```

Task:
Summarize the overall responsibility of this class in one concise sentence.

Output language:
{language}

Rules:
- Describe only behavior supported by the provided source code.
- Focus on the overall responsibility of the class, not every individual method.
- Do not invent functionality.
- Do not translate class names, method names, parameter names, file paths, or code identifiers.
- Do not include Markdown formatting.
- Return only the summary sentence.
"""

    return prompt.strip()


# 根据文件中的结构化符号信息和目标语言，构造文件职责总结提示词
def build_file_prompt(
    file_info: FileInfo,
    language: str,
) -> str:
    classes = "\n".join(
        f"- {class_info.name}"
        for class_info in file_info.classes
    ) or "- None"

    functions = "\n".join(
        f"- {function_info.name}({', '.join(function_info.parameters)})"
        for function_info in file_info.functions
    ) or "- None"

    methods = "\n".join(
        f"- {method_info.class_name}.{method_info.name}"
        f"({', '.join(method_info.parameters)})"
        for method_info in file_info.methods
    ) or "- None"

    prompt = f"""
You are analyzing a source code file using structured information extracted by static analysis.

File path:
{file_info.path}

Classes:
{classes}

Functions:
{functions}

Methods:
{methods}

Task:
Summarize the overall responsibility of this file in one concise sentence.

Output language:
{language}

Rules:
- Base the summary only on the provided file path and symbol information.
- Describe the overall responsibility of the file, not every individual symbol.
- Do not invent functionality that is not supported by the provided information.
- Do not translate file paths, class names, function names, method names, parameter names, or code identifiers.
- Do not include Markdown formatting.
- Return only the summary sentence.
"""

    return prompt.strip()