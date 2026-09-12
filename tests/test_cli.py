from io import BytesIO, TextIOWrapper
from pathlib import Path
import sys
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
    assert args.lang is None


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


def test_cli_init_creates_config_in_current_directory(
    tmp_path: Path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    answers = iter(["  qwen-flash  ", "  https://example.test/v1  ", "2"])
    monkeypatch.setattr("repoatlas.cli._stdin_is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    assert main(["init"]) == 0

    captured = capsys.readouterr()
    content = (tmp_path / ".repoatlas.toml").read_text(encoding="utf-8")
    assert 'provider = "openai-compatible"' in content
    assert 'model = "qwen-flash"' in content
    assert 'base_url = "https://example.test/v1"' in content
    assert 'language = "zh-CN"' in content
    assert "api_key" not in content.casefold()
    assert "Created .repoatlas.toml" in captured.out
    assert "REPOATLAS_API_KEY" in captured.out
    assert '$env:REPOATLAS_API_KEY="YOUR_API_KEY"' in captured.out


def test_cli_init_defaults_language_and_retries_invalid_answers(
    tmp_path: Path, monkeypatch, capsys
):
    monkeypatch.chdir(tmp_path)
    answers = iter([" ", "model-a", "", "https://example.test", "9", "wrong", ""])
    monkeypatch.setattr("repoatlas.cli._stdin_is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    assert main(["init"]) == 0

    content = (tmp_path / ".repoatlas.toml").read_text(encoding="utf-8")
    captured = capsys.readouterr()
    assert 'language = "en"' in content
    assert "Model cannot be empty" in captured.out
    assert "Base URL cannot be empty" in captured.out
    assert captured.out.count("Please enter a number from 1 to 8.") == 2


def test_cli_init_noninteractive_recommends_template(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("repoatlas.cli._stdin_is_interactive", lambda: False)

    assert main(["init"]) == 2

    captured = capsys.readouterr()
    assert "interactive terminal" in captured.err
    assert "repoatlas init --template" in captured.err
    assert not (tmp_path / ".repoatlas.toml").exists()


def test_cli_init_template_and_force(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)

    assert main(["init", "--template"]) == 0
    config_path = tmp_path / ".repoatlas.toml"
    assert "# Supported values:" in config_path.read_text(encoding="utf-8")

    config_path.write_text("original\n", encoding="utf-8")
    assert main(["init", "--template"]) == 2
    assert "repoatlas init --template --force" in capsys.readouterr().err
    assert config_path.read_text(encoding="utf-8") == "original\n"

    assert main(["init", "--template", "--force"]) == 0
    assert "# Supported values:" in config_path.read_text(encoding="utf-8")
    assert "original" not in config_path.read_text(encoding="utf-8")
    assert "Created .repoatlas.toml" in capsys.readouterr().out


def test_cli_interactive_init_force_replaces_existing_config(
    tmp_path: Path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / ".repoatlas.toml"
    config_path.write_text("original\n", encoding="utf-8")
    answers = iter(["replacement-model", "https://replacement.test", "3"])
    monkeypatch.setattr("repoatlas.cli._stdin_is_interactive", lambda: True)
    monkeypatch.setattr("builtins.input", lambda prompt="": next(answers))

    assert main(["init", "--force"]) == 0

    content = config_path.read_text(encoding="utf-8")
    assert 'model = "replacement-model"' in content
    assert 'language = "ja"' in content
    assert "original" not in content


def test_cli_init_refuses_to_overwrite_existing_config(
    tmp_path: Path, monkeypatch, capsys
):
    config_path = tmp_path / ".repoatlas.toml"
    config_path.write_text("original\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    assert main(["init"]) == 2

    captured = capsys.readouterr()
    assert "already exists" in captured.err
    assert config_path.read_text(encoding="utf-8") == "original\n"


def test_cli_uses_config_and_cli_values_take_precedence(
    tmp_path: Path, monkeypatch
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / ".repoatlas.toml").write_text(
        """[llm]
provider = "config-provider"
model = "config-model"
base_url = "https://config.example/v1"
language = "中文"
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    captured_config = None
    captured_language = None

    def capture_client(config):
        nonlocal captured_config
        captured_config = config
        return FakeLLM()

    def capture_summaries(repository, language, llm):
        nonlocal captured_language
        captured_language = language
        return None

    monkeypatch.setattr("repoatlas.cli.create_llm_client", capture_client)
    monkeypatch.setattr("repoatlas.cli.summarize_repository", capture_summaries)

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(tmp_path / "output"),
            "--model",
            "cli-model",
            "--lang",
            "English",
        ]
    )

    assert exit_code == 0
    assert captured_config.provider == "config-provider"
    assert captured_config.model == "cli-model"
    assert captured_config.base_url == "https://config.example/v1"
    assert captured_language == "en"


def test_cli_normalizes_language_alias_from_config(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / ".repoatlas.toml").write_text(
        "[llm]\nlanguage = \"日本語\"\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    captured_language = None

    def capture_render(repository, output_dir, summaries, language):
        nonlocal captured_language
        captured_language = language
        return {}

    monkeypatch.setattr("repoatlas.cli.render_visual_map", capture_render)

    assert main([str(repo_dir), "--no-llm"]) == 0
    assert captured_language == "ja"


def test_cli_normalizes_canonical_language_unchanged(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    captured_language = None

    def capture_render(repository, output_dir, summaries, language):
        nonlocal captured_language
        captured_language = language
        return {}

    monkeypatch.setattr("repoatlas.cli.render_visual_map", capture_render)

    assert main([str(repo_dir), "--no-llm", "--lang", "zh-CN"]) == 0
    assert captured_language == "zh-CN"


def test_cli_rejects_unsupported_language_before_llm(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)

    def fail_if_called(config):
        raise AssertionError("unsupported language must not reach the LLM")

    monkeypatch.setattr("repoatlas.cli.create_llm_client", fail_if_called)

    exit_code = main(
        [
            str(repo_dir),
            "--model",
            "test-model",
            "--base-url",
            "https://example.test/v1",
            "--lang",
            "russian",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "Unsupported language: russian" in captured.err
    assert "Supported languages:" in captured.err
    assert "en" in captured.err
    assert "English" in captured.err
    assert "zh-CN" in captured.err
    assert "简体中文" in captured.err


def test_cli_rejects_unsupported_config_language_before_llm(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / ".repoatlas.toml").write_text(
        """[llm]
model = "test-model"
base_url = "https://example.test/v1"
language = "russian"
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def fail_if_called(config):
        raise AssertionError("unsupported config language must not reach the LLM")

    monkeypatch.setattr("repoatlas.cli.create_llm_client", fail_if_called)

    assert main([str(repo_dir)]) == 2
    assert "Unsupported language: russian" in capsys.readouterr().err


def test_unsupported_language_error_supports_limited_console_encoding(
    monkeypatch,
):
    raw_stderr = BytesIO()
    limited_stderr = TextIOWrapper(
        raw_stderr,
        encoding="gbk",
        write_through=True,
    )
    monkeypatch.setattr(sys, "stderr", limited_stderr)

    assert main([".", "--lang", "russian", "--no-llm"]) == 2

    message = raw_stderr.getvalue().decode("utf-8")
    assert "Unsupported language: russian" in message
    assert "简体中文" in message
    assert "한국어" in message


def test_no_llm_overrides_project_config(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    (tmp_path / ".repoatlas.toml").write_text(
        """[llm]
provider = "config-provider"
model = "config-model"
base_url = "https://config.example/v1"
language = "zh-CN"
""",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)

    def fail_if_called(config):
        raise AssertionError(
            "create_llm_client should not be called when --no-llm is enabled"
        )

    monkeypatch.setattr("repoatlas.cli.create_llm_client", fail_if_called)

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(tmp_path / "output"),
            "--no-llm",
        ]
    )

    assert exit_code == 0


def test_cli_default_provider_completes_explicit_llm_options(
    tmp_path: Path, monkeypatch
):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    captured_config = None

    def capture_client(config):
        nonlocal captured_config
        captured_config = config
        return FakeLLM()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("repoatlas.cli.create_llm_client", capture_client)

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(tmp_path / "output"),
            "--model",
            "cli-model",
            "--base-url",
            "https://cli.example/v1",
        ]
    )

    assert exit_code == 0
    assert captured_config.provider == "openai-compatible"


def test_cli_reads_api_key_only_from_environment(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    captured_config = None

    def capture_client(config):
        nonlocal captured_config
        captured_config = config
        return FakeLLM()

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("REPOATLAS_API_KEY", "environment-secret")
    monkeypatch.setattr("repoatlas.cli.create_llm_client", capture_client)

    exit_code = main(
        [
            str(repo_dir),
            "--output-dir",
            str(tmp_path / "output"),
            "--model",
            "cli-model",
            "--base-url",
            "https://cli.example/v1",
        ]
    )

    assert exit_code == 0
    assert captured_config.api_key == "environment-secret"


def test_empty_init_config_does_not_enable_llm(tmp_path: Path, monkeypatch):
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "main.py").write_text("value = 1\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert main(["init", "--template"]) == 0

    def fail_if_called(config):
        raise AssertionError("an unfilled template must not enable LLM features")

    monkeypatch.setattr("repoatlas.cli.create_llm_client", fail_if_called)

    assert main(
        [
            str(repo_dir),
            "--output-dir",
            str(tmp_path / "output"),
        ]
    ) == 0
