"""RepoAtlas 命令行入口。"""

import argparse
from pathlib import Path
import sys
from typing import Sequence

from repoatlas import __version__
from repoatlas.core.analyzer import analyze_repository
from repoatlas.rendering.visualizer import render_visual_map


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
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """分析仓库并生成 Markdown、JSON 和交互式 HTML 地图。"""
    args = build_parser().parse_args(argv)
    repo_path = Path(args.repo_path).expanduser()
    output_dir = Path(args.output_dir).expanduser()

    try:
        repository = analyze_repository(repo_path)
        generated = render_visual_map(repository, output_dir)
    except (FileNotFoundError, NotADirectoryError, OSError, SyntaxError) as error:
        print(f"RepoAtlas error: {error}", file=sys.stderr)
        return 1

    print(f"Repository analyzed: {repository.root_path}")
    for output_path in generated.values():
        print(f"Generated: {output_path}")
    return 0
