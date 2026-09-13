from repomosaic.semantic.models import SemanticSummary


# 根据代码对象的身份信息和语言，生成唯一的语义摘要索引键
def make_summary_key(
    target_type: str,
    file_path: str,
    name: str,
    start_line: int | None,
    class_name: str | None,
    language: str,
) -> tuple[str, str, str, int | None, str | None, str]:
    return (
        target_type,
        file_path,
        name,
        start_line,
        class_name,
        language,
    )


# 将语义摘要列表整理为可以快速查找的字典索引
def build_summary_index(
    summaries: list[SemanticSummary],
):
    index = {}

    for summary in summaries:
        key = make_summary_key(
            target_type=summary.target_type,
            file_path=summary.file_path,
            name=summary.name,
            start_line=summary.start_line,
            class_name=summary.class_name,
            language=summary.language,
        )

        index[key] = summary

    return index