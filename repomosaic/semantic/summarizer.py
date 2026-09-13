from pathlib import Path
from repomosaic.core.symbols import FunctionInfo, ClassInfo, FileInfo, RepositoryInfo
from repomosaic.llm.base import LLMClient
from repomosaic.semantic.prompts import build_function_prompt, build_class_prompt, build_file_prompt
from pathlib import Path
from repomosaic.semantic.models import SemanticSummary
from repomosaic.core.paths import resolve_repository_file
from repomosaic.semantic.languages import validate_language


# 根据函数信息和源码构造 Prompt，调用 LLM，并返回清理后的函数摘要
def summarize_function(
    function_info: FunctionInfo,
    source_code: str,
    language: str,
    llm: LLMClient,
) -> str:
    prompt = build_function_prompt(function_info, source_code, language)

    summary = llm.generate(prompt)

    return summary.strip()


# 根据函数信息和源码构造 Prompt，调用 LLM，并返回清理后的类摘要
def summarize_class(
    class_info: ClassInfo,
    source_code: str,
    language: str,
    llm: LLMClient,
) -> str:
    prompt = build_class_prompt(class_info, source_code, language)

    summary = llm.generate(prompt)

    return summary.strip()


# 根据文件的结构化信息调用 LLM，生成文件整体职责摘要
def summarize_file(
    file_info: FileInfo,
    language: str,
    llm: LLMClient,
) -> str:
    prompt = build_file_prompt(
        file_info,
        language,
    )

    summary = llm.generate(prompt)

    return summary.strip()


# 根据起止行号，从源文件中提取指定代码片段
def extract_source_lines(
    file_path: str | Path,
    start_line: int,
    end_line: int,
) -> str:
    path = Path(file_path)
    lines = path.read_text(encoding="utf-8").splitlines()

    return "\n".join(
        lines[start_line - 1:end_line]
    )


# 遍历整个仓库，为文件、类、函数和方法生成语义摘要
def summarize_repository(
    repository: RepositoryInfo,
    language: str,
    llm: LLMClient,
) -> list[SemanticSummary]:
    language = validate_language(language)
    
    summaries: list[SemanticSummary] = []

    repo_root = Path(repository.root_path)

    for file_info in repository.files:
        full_path = resolve_repository_file(
            repository.root_path,
            file_info.path,
        )

        # 为当前文件生成整体职责摘要
        file_summary_text = summarize_file(
            file_info=file_info,
            language=language,
            llm=llm,
        )

        file_summary = SemanticSummary(
            target_type="file",
            file_path=file_info.path,
            name=file_info.path,
            summary=file_summary_text,
            language=language,
        )

        summaries.append(file_summary)

        # 为当前文件中的每个类提取源码，并生成类职责摘要
        for class_info in file_info.classes:
            class_source = extract_source_lines(
                file_path=full_path,
                start_line=class_info.start_line,
                end_line=class_info.end_line,
            )

            class_summary_text = summarize_class(
                class_info=class_info,
                source_code=class_source,
                language=language,
                llm=llm,
            )

            class_summary = SemanticSummary(
                target_type="class",
                file_path=file_info.path,
                name=class_info.name,
                summary=class_summary_text,
                language=language,
                start_line=class_info.start_line,
            )

            summaries.append(class_summary)

        # 为当前文件中的每个顶层函数提取源码，并生成函数职责摘要
        for function_info in file_info.functions:
            function_source = extract_source_lines(
                file_path=full_path,
                start_line=function_info.start_line,
                end_line=function_info.end_line,
            )

            function_summary_text = summarize_function(
                function_info=function_info,
                source_code=function_source,
                language=language,
                llm=llm,
            )

            function_summary = SemanticSummary(
                target_type="function",
                file_path=file_info.path,
                name=function_info.name,
                summary=function_summary_text,
                language=language,
                start_line=function_info.start_line,
            )

            summaries.append(function_summary)

        # 为当前文件中的每个方法提取源码，并生成方法职责摘要
        for method_info in file_info.methods:
            method_source = extract_source_lines(
                file_path=full_path,
                start_line=method_info.start_line,
                end_line=method_info.end_line,
            )

            method_summary_text = summarize_function(
                function_info=method_info,
                source_code=method_source,
                language=language,
                llm=llm,
            )

            method_summary = SemanticSummary(
                target_type="method",
                file_path=file_info.path,
                name=method_info.name,
                summary=method_summary_text,
                language=language,
                start_line=method_info.start_line,
                class_name=method_info.class_name,
            )

            summaries.append(method_summary)

    return summaries
