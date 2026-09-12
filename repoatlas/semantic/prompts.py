from repoatlas.core.symbols import FunctionInfo, ClassInfo, FileInfo


def _compact_description(description: str) -> str:
    """把 docstring 压缩成适合文件级 Prompt 的单行证据。"""
    return " ".join(description.split()) or "No docstring"


# 根据函数信息、函数源码和目标语言，构造函数总结提示词
def build_function_prompt(
    function_info: FunctionInfo,
    source_code: str,
    language: str,
) -> str:
    parameters = ", ".join(function_info.parameters)
    symbol_type = "method" if function_info.class_name else "function"
    owner = function_info.class_name or "Not applicable"

    prompt = f"""
You are analyzing a {symbol_type} in a source code repository.

Name:
{function_info.name}

Owning class:
{owner}

Parameters:
{parameters}

Source code:
```python
{source_code}
```

Task:
Write a concise, information-dense summary of approximately 2-3 sentences when the source supports it. Explain the concrete operation performed, how important inputs are used, and what is returned, modified, or produced. Mention validation, errors, or side effects only when they are clearly visible in the source.

Output language:
{language}

Rules:
- Describe only behavior supported by the provided source code.
- Do not invent functionality.
- Do not translate function names, parameter names, file paths, or code identifiers.
- Use plain natural-language text, without Markdown headings or bullet lists.
- Return only the summary.
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
Write a concise, information-dense summary of approximately 2-4 sentences when the source supports it. Explain the class's main responsibility, important state it represents or manages, and what its key methods collectively do. Mention interactions with other components only when they are directly supported by the source.

Output language:
{language}

Rules:
- Describe only behavior supported by the provided source code.
- Synthesize the class's overall responsibility instead of mechanically listing every method.
- Do not invent functionality.
- Do not translate class names, method names, parameter names, file paths, or code identifiers.
- Use plain natural-language text, without Markdown headings or bullet lists.
- Return only the summary.
"""

    return prompt.strip()


# 根据文件中的结构化符号信息和目标语言，构造文件职责总结提示词
def build_file_prompt(
    file_info: FileInfo,
    language: str,
) -> str:
    classes = "\n".join(
        f"- {class_info.name}: {_compact_description(class_info.docstring)}"
        for class_info in file_info.classes
    ) or "- None"

    functions = "\n".join(
        f"- {function_info.name}({', '.join(function_info.parameters)}): "
        f"{_compact_description(function_info.docstring)}"
        for function_info in file_info.functions
    ) or "- None"

    methods = "\n".join(
        f"- {method_info.class_name}.{method_info.name}"
        f"({', '.join(method_info.parameters)}): "
        f"{_compact_description(method_info.docstring)}"
        for method_info in file_info.methods
    ) or "- None"

    prompt = f"""
You are analyzing a source code file using structured information extracted by static analysis.

File path:
{file_info.path}

Module docstring:
{_compact_description(file_info.module_docstring)}

Classes:
{classes}

Functions:
{functions}

Methods:
{methods}

Task:
Write a concise, information-dense summary of approximately 3-5 sentences when the available evidence supports it. Explain the file's primary responsibility, its important components, and how those components work together. Include important inputs, outputs, dependencies, or side effects only when visible in the supplied evidence, and describe the file's repository role only when directly supported.

Output language:
{language}

Rules:
- Base the summary only on the provided path, module docstring, and symbol metadata.
- Synthesize the file's responsibility; do not merely restate its filename or list symbols.
- Do not invent functionality that is not supported by the provided information.
- Do not translate file paths, class names, function names, method names, parameter names, or code identifiers.
- Use plain natural-language text, without Markdown headings or bullet lists.
- Return only the summary.
"""

    return prompt.strip()
