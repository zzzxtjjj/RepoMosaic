"""RepoAtlas 命令行入口。"""
import argparse
import getpass
from pathlib import Path
import sys
from typing import Sequence

from repoatlas import __version__
from repoatlas.core.analyzer import analyze_repository
from repoatlas.credentials import (
    CredentialStoreError,
    clear_stored_api_key,
    resolve_api_key,
    set_stored_api_key,
)
from repoatlas.rendering.visualizer import render_visual_map
from repoatlas.semantic.languages import SUPPORTED_LANGUAGES, normalize_language
from repoatlas.llm.config import LLMConfig
from repoatlas.llm.factory import create_llm_client
from repoatlas.semantic.summarizer import summarize_repository
from repoatlas.llm.base import LLMError
from repoatlas.project_config import (
    DEFAULT_LANGUAGE,
    DEFAULT_PROVIDER,
    ProjectConfigError,
    load_project_config,
    write_project_config,
    write_project_config_values,
)


def _print_language_error(error: ValueError) -> None:
    """在受限 Windows code page 下也用 UTF-8 输出完整语言列表。"""
    message = f"RepoAtlas error: {error}"
    encoding = getattr(sys.stderr, "encoding", None) or "utf-8"

    try:
        message.encode(encoding)
    except (LookupError, UnicodeEncodeError):
        buffer = getattr(sys.stderr, "buffer", None)
        if buffer is not None:
            buffer.write((message + "\n").encode("utf-8"))
            buffer.flush()
            return

    print(message, file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    """创建 RepoAtlas V0.1 命令行参数解析器。"""
    parser = argparse.ArgumentParser(
        prog="repoatlas",
        description="Generate a repository knowledge map using static analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "commands:\n"
            "  repoatlas init         Configure the current project\n"
            "  repoatlas auth set     Save the user-level API key\n"
            "  repoatlas auth status  Check API-key availability\n"
            "  repoatlas auth clear   Remove the stored API key"
        ),
    )

    parser.add_argument(
        "repo_path",
        nargs="?",
        default=".",
        help="Repository path to analyze (default: current directory).",
    )

    parser.add_argument(
        "--output-dir",
        default="repoatlas_output",
        help="Directory for generated files (default: repoatlas_output).",
    )

    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Disable LLM features (currently the default behavior).",
    )

    parser.add_argument(
    "--provider",
    default=None,
    help="LLM provider, for example: openai-compatible",
    )

    parser.add_argument(
        "--model",
        default=None,
        help="Model name used for semantic summaries",
    )

    parser.add_argument(
        "--base-url",
        default=None,
        help="Base URL of the LLM API",
    )

    parser.add_argument(
        "--lang",
        default=None,
        help="Summary language code or common name/alias (default: en)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def build_init_parser() -> argparse.ArgumentParser:
    """Create the parser for ``repoatlas init``."""
    parser = argparse.ArgumentParser(
        prog="repoatlas init",
        description="Set up .repoatlas.toml in the current directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing .repoatlas.toml file.",
    )
    parser.add_argument(
        "--template",
        action="store_true",
        help="Create a commented configuration template for manual editing.",
    )
    return parser


def build_auth_parser() -> argparse.ArgumentParser:
    """Create the parser for user-level credential commands."""
    parser = argparse.ArgumentParser(
        prog="repoatlas auth",
        description="Manage RepoAtlas's user-level API credential.",
    )
    commands = parser.add_subparsers(dest="auth_command", required=True)
    commands.add_parser("set", help="Save the default API key securely.")
    commands.add_parser("status", help="Show whether an API key is configured.")
    commands.add_parser("clear", help="Remove the stored RepoAtlas API key.")
    return parser


def _stdin_is_interactive() -> bool:
    """判断当前标准输入是否适合交互式配置。"""
    try:
        return bool(sys.stdin.isatty())
    except (AttributeError, OSError):
        return False


def _prompt_required(label: str) -> str:
    """读取必填文本，并在空输入时给出简短重试提示。"""
    while True:
        value = input(f"{label}:\n> ").strip()
        if value:
            return value
        print(f"{label} cannot be empty. Please try again.\n")


def _prompt_language() -> str:
    """用编号选择输出语言，并返回 canonical language code。"""
    languages = list(SUPPORTED_LANGUAGES.items())
    print("Output language:")
    for index, (_, name) in enumerate(languages, start=1):
        print(f"  {index}. {name}")

    while True:
        selection = input(f"\nChoose [1-{len(languages)}] [default: 1]:\n> ").strip()
        if not selection:
            return languages[0][0]
        try:
            index = int(selection)
        except ValueError:
            index = 0
        if 1 <= index <= len(languages):
            return languages[index - 1][0]
        print(f"Please enter a number from 1 to {len(languages)}.")


def _print_init_next_steps() -> None:
    """提示用户通过用户级凭据存储提供 API key。"""
    print("\nNext:")
    print("If needed, save your API key once, then run:\n")
    print("    repoatlas auth set")
    print("    repoatlas .")


def _run_auth_command(arguments: Sequence[str]) -> int:
    """执行用户级 API key 的保存、检查或删除操作。"""
    args = build_auth_parser().parse_args(arguments)

    try:
        if args.auth_command == "set":
            if not _stdin_is_interactive():
                print(
                    "RepoAtlas auth set needs an interactive terminal.",
                    file=sys.stderr,
                )
                return 2
            print("RepoAtlas authentication\n")
            while True:
                api_key = getpass.getpass("API key:\n> ").strip()
                if api_key:
                    break
                print("API key cannot be empty. Please try again.\n")
            set_stored_api_key(api_key)
            print("\nRepoAtlas API key saved securely.")
            print("\nNext:\n  cd path/to/project\n  repoatlas init\n  repoatlas .")
            return 0

        if args.auth_command == "status":
            credential = resolve_api_key()
            print(f"API key configured: {'yes' if credential else 'no'}")
            if credential:
                print(f"Source: {credential.source}")
            return 0

        if clear_stored_api_key():
            print("RepoAtlas API key removed.")
        else:
            print("No stored RepoAtlas API key found.")
        return 0
    except (CredentialStoreError, ValueError) as error:
        print(f"RepoAtlas error: {error}", file=sys.stderr)
        return 2


def main(argv: Sequence[str] | None = None) -> int:
    """分析仓库并生成 Markdown、JSON 和交互式 HTML 地图。"""
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if arguments and arguments[0] == "init":
        init_args = build_init_parser().parse_args(arguments[1:])
        config_path = Path.cwd() / ".repoatlas.toml"
        if config_path.exists() and not init_args.force:
            force_command = (
                "repoatlas init --template --force"
                if init_args.template
                else "repoatlas init --force"
            )
            print(
                "RepoAtlas configuration already exists:\n"
                ".repoatlas.toml\n\n"
                f"Use:\n{force_command}",
                file=sys.stderr,
            )
            return 2

        if not init_args.template and not _stdin_is_interactive():
            print(
                "RepoAtlas init needs an interactive terminal.\n"
                "Use 'repoatlas init --template' to create a manual template.",
                file=sys.stderr,
            )
            return 2

        try:
            if init_args.template:
                config_path = write_project_config(
                    Path.cwd(), force=init_args.force
                )
            else:
                print("RepoAtlas setup\n")
                model = _prompt_required("Model")
                print()
                base_url = _prompt_required("Base URL")
                print()
                language = _prompt_language()
                config_path = write_project_config_values(
                    Path.cwd(),
                    model=model,
                    base_url=base_url,
                    language=language,
                    force=init_args.force,
                )
        except (FileExistsError, OSError) as error:
            print(f"RepoAtlas error: {error}", file=sys.stderr)
            return 2

        print(f"\nCreated {config_path.name}")
        _print_init_next_steps()
        return 0

    if arguments and arguments[0] == "auth":
        return _run_auth_command(arguments[1:])

    args = build_parser().parse_args(arguments)

    try:
        project_config = load_project_config(Path.cwd())
    except ProjectConfigError as error:
        print(f"RepoAtlas error: {error}", file=sys.stderr)
        return 2

    provider = (
        args.provider
        if args.provider is not None
        else project_config.provider or DEFAULT_PROVIDER
    )
    model = args.model if args.model is not None else project_config.model
    base_url = (
        args.base_url if args.base_url is not None else project_config.base_url
    )
    language = (
        args.lang
        if args.lang is not None
        else project_config.language or DEFAULT_LANGUAGE
    )

    try:
        language = normalize_language(language)
    except ValueError as error:
        _print_language_error(error)
        return 2

    llm_requested = any(
        [
            args.provider,
            model,
            base_url,
        ]
    )

    if args.no_llm:
        llm_requested = False

    llm_config: LLMConfig | None = None

    if llm_requested:
        missing = []

        if not provider:
            missing.append("provider")

        if not model:
            missing.append("model")
   
        if not base_url:
            missing.append("base-url")

        if missing:
            print(
                f"RepoAtlas error: missing LLM options: {', '.join(missing)}",
                file=sys.stderr,
            )
            return 2

        try:
            credential = resolve_api_key()
        except CredentialStoreError as error:
            print(f"RepoAtlas error: {error}", file=sys.stderr)
            return 2

        if credential is None:
            print(
                "RepoAtlas error: No API key configured.\n\n"
                "Run:\n  repoatlas auth set\n\n"
                "For temporary use you may set:\n  REPOATLAS_API_KEY",
                file=sys.stderr,
            )
            return 2

        llm_config = LLMConfig(
            provider=provider,
            model=model,
            api_key=credential.value,
            base_url=base_url,
        )

    llm_client = None

    if llm_config is not None:
        # 根据已经验证过的 LLM 配置创建对应的大模型客户端
        try:
            llm_client = create_llm_client(llm_config)

        except ValueError as error:
            print(f"RepoAtlas error: {error}", file=sys.stderr)
            return 2
    
    repo_path = Path(args.repo_path).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    try:
        repository = analyze_repository(repo_path)

        summaries = None

        if llm_client is not None:
            # 使用已经创建好的 LLM Client，为整个仓库生成语义摘要
            summaries = summarize_repository(
                repository=repository,
                language=language,
                llm=llm_client,
            )

        generated = render_visual_map(
            repository,
            output_dir,
            summaries=summaries,
            language=language,
        )

    except LLMError as error:
        print(
            f"RepoAtlas error: {error}",
            file=sys.stderr,
        )
        return 1

    except (
        FileNotFoundError,
        NotADirectoryError,
        OSError,
        SyntaxError,
    ) as error:
        print(
            f"RepoAtlas error: {error}",
            file=sys.stderr,
        )
        return 1

    print(f"Repository analyzed: {repository.root_path}")

    for output_path in generated.values():
        print(f"Generated: {output_path}")

    return 0
