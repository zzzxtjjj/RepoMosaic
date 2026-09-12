from pathlib import Path
from repoatlas.llm.base import LLMError
from repoatlas.cli import build_parser, main


# 模拟真实大模型客户端，避免测试过程中访问网络或消耗 API
class FakeLLM:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return "FAKE SEMANTIC SUMMARY"


# 验证 CLI 在没有额外参数时会使用预期的默认配置
def test_build_parser_defaults():
    parser = build_parser()
    args = parser.parse_args([])

    assert args.repo_path == "."
    assert args.output_dir == "repoatlas_output"
    assert args.no_llm is False
    assert args.provider is None
    assert args.model is None
    assert args.base_url is None
    assert args.lang == "en"


# 验证 CLI 在不启用 LLM 时仍能完成静态仓库分析并生成三个输出文件
def test_cli_generates_outputs_without_llm(tmp_path: Path):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text(
        """
def hello(name):
    return f"Hello {name}"
""".strip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--no-llm",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "structure.json").exists()
    assert (output_dir / "map.html").exists()
    assert (output_dir / "STRUCTURE.md").exists()


# 验证只提供部分 LLM 参数时，CLI 会拒绝继续执行并返回参数错误
def test_cli_rejects_incomplete_llm_options(capsys):
    exit_code = main(
        [
            ".",
            "--model",
            "fake-model",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 2
    assert "missing LLM options" in captured.err
    assert "provider" in captured.err
    assert "base-url" in captured.err


# 验证 --no-llm 的优先级高于其他 LLM 参数，不会尝试创建大模型客户端
def test_no_llm_overrides_llm_options(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text(
        "value = 1\n",
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    def fail_if_called(config):
        raise AssertionError(
            "create_llm_client should not be called when --no-llm is enabled"
        )

    monkeypatch.setattr(
        "repoatlas.cli.create_llm_client",
        fail_if_called,
    )

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--no-llm",
            "--model",
            "fake-model",
        ]
    )

    assert exit_code == 0
    assert (output_dir / "structure.json").exists()


# 验证 CLI 启用 LLM 后，会生成语义摘要并写入可视化输出
def test_cli_generates_semantic_summaries_with_llm(
    tmp_path: Path,
    monkeypatch,
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text(
        """
def hello(name):
    return f"Hello {name}"
""".strip(),
        encoding="utf-8",
    )

    output_dir = tmp_path / "output"

    fake_llm = FakeLLM()

    monkeypatch.setattr(
        "repoatlas.cli.create_llm_client",
        lambda config: fake_llm,
    )

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(output_dir),
            "--provider",
            "openai-compatible",
            "--model",
            "fake-model",
            "--base-url",
            "https://fake.example.com",
            "--lang",
            "en",
        ]
    )

    assert exit_code == 0

    # 至少证明 summarize_repository 确实调用过 LLM
    assert len(fake_llm.prompts) > 0

    structure_path = output_dir / "structure.json"

    assert structure_path.exists()

    structure_content = structure_path.read_text(
        encoding="utf-8"
    )

    # 验证 Fake LLM 返回的摘要最终真的进入 Visual Map 数据
    assert "FAKE SEMANTIC SUMMARY" in structure_content


# 验证 LLM 调用失败时 CLI 返回干净错误，而不是抛出 traceback
def test_cli_handles_llm_error(
    tmp_path,
    monkeypatch,
    capsys,
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()

    (repo_dir / "main.py").write_text(
        """
def hello():
    return "hello"
""".strip(),
        encoding="utf-8",
    )

    class FailingLLM:
        def generate(self, prompt: str) -> str:
            raise LLMError("LLM request timed out.")

    monkeypatch.setattr(
        "repoatlas.cli.create_llm_client",
        lambda config: FailingLLM(),
    )

    exit_code = main(
        [
            str(repo_dir),
            "--provider",
            "openai-compatible",
            "--model",
            "fake-model",
            "--base-url",
            "https://fake.example.com",
        ]
    )

    captured = capsys.readouterr()

    assert exit_code == 1
    assert "RepoAtlas error: LLM request timed out." in captured.err