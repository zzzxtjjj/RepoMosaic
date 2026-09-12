"""RepoAtlas 命令行入口。"""
import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from repoatlas import __version__
from repoatlas.core.analyzer import analyze_repository
from repoatlas.rendering.visualizer import render_visual_map
from repoatlas.semantic.languages import normalize_language
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
        description="Create a .repoatlas.toml template in the current directory.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing .repoatlas.toml file.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """分析仓库并生成 Markdown、JSON 和交互式 HTML 地图。"""
    arguments = list(argv) if argv is not None else sys.argv[1:]

    if arguments and arguments[0] == "init":
        init_args = build_init_parser().parse_args(arguments[1:])
        try:
            config_path = write_project_config(Path.cwd(), force=init_args.force)
        except (FileExistsError, OSError) as error:
            print(f"RepoAtlas error: {error}", file=sys.stderr)
            return 2

        print(f"Created: {config_path}")
        print("Set REPOATLAS_API_KEY in your environment before using LLM features.")
        return 0

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

        api_key = os.getenv("REPOATLAS_API_KEY")

        llm_config = LLMConfig(
            provider=provider,
            model=model,
            api_key=api_key,
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
