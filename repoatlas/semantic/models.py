from dataclasses import dataclass


# 保存 RepoAtlas 为一个代码对象生成的语义摘要
@dataclass
class SemanticSummary:
    target_type: str
    file_path: str
    name: str
    summary: str
    language: str
    start_line: int | None = None
    class_name: str | None = None