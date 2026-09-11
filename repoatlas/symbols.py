from dataclasses import dataclass


@dataclass
class FunctionInfo:
    """
    保存 RepoAtlas 从函数或方法中提取出的结构化信息。
    """

    name: str
    start_line: int
    end_line: int
    parameters: list[str]
    docstring: str
    class_name: str | None = None


# 保存 RepoAtlas 从类中提取出的结构化信息
@dataclass
class ClassInfo:
    name: str
    start_line: int
    end_line: int
    docstring: str