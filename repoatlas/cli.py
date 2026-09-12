"""RepoAtlas 命令行入口。"""
import argparse
import os
from pathlib import Path
import sys
from typing import Sequence

from repoatlas import __version__
from repoatlas.core.analyzer import analyze_repository
from repoatlas.rendering.visualizer import render_visual_map
from repoatlas.semantic.languages import SUPPORTED_LANGUAGES
from repoatlas.llm.config import LLMConfig
from repoatlas.llm.factory import create_llm_client
from repoatlas.semantic.summarizer import summarize_repository
from repoatlas.llm.base import LLMError


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
        default="en",
        choices=SUPPORTED_LANGUAGES.keys(),
        help="Language used for semantic summaries",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """分析仓库并生成 Markdown、JSON 和交互式 HTML 地图。"""
    args = build_parser().parse_args(argv)

    llm_requested = any(
        [
            args.provider,
            args.model,
            args.base_url,
        ]
    )

    if args.no_llm:
        llm_requested = False

    llm_config: LLMConfig | None = None

    if llm_requested:
        missing = []

        if not args.provider:
            missing.append("provider")

        if not args.model:
            missing.append("model")
   
        if not args.base_url:
            missing.append("base-url")

        if missing:
            print(
                f"RepoAtlas error: missing LLM options: {', '.join(missing)}",
                file=sys.stderr,
            )
            return 2

        api_key = os.getenv("REPOATLAS_API_KEY")

        llm_config = LLMConfig(
            provider=args.provider,
            model=args.model,
            api_key=api_key,
            base_url=args.base_url,
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
                language=args.lang,
                llm=llm_client,
            )

        generated = render_visual_map(
            repository,
            output_dir,
            summaries=summaries,
            language=args.lang,
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