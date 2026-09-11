# RepoAtlas

Human-first and agent-readable repository knowledge maps.

## What is RepoAtlas?

RepoAtlas uses static analysis to turn a code repository into a browsable knowledge map. It extracts Python files, classes, functions, methods, signatures, line ranges, and docstrings, then presents that information as Markdown, Mermaid, JSON, and an interactive HTML map.

Its optional semantic layer can generate multilingual responsibility summaries through an injected LLM client. The visual map accepts those summaries as input, while the current CLI remains static-analysis-only and never contacts a model provider.

## Current Features

- Repository scanning with common development directories ignored
- Python AST analysis
- Class, function, and method extraction
- Function and method signatures
- Source line ranges and docstrings
- Repository-level structured data
- Markdown knowledge map with Mermaid overview
- Interactive, expandable HTML visualization with a detail panel
- Function, class, method, and file semantic summaries
- Eight supported summary languages
- OpenAI-compatible LLM client abstraction

## Why RepoAtlas?

A normal file tree tells you where code lives. RepoAtlas is being built to help both people and coding agents understand the structure and responsibilities inside a repository: which files contain important symbols, how classes and methods are organized, what parameters functions accept, and where each symbol is defined.

Structural facts, docstrings, and optional semantic summaries provide that context without coupling rendering to an LLM provider.

## Quick Start

From a local clone or source checkout:

```powershell
cd repoatlas
uv venv --python 3.12
.\.venv\Scripts\Activate.ps1
uv pip install -e ".[dev]"
repoatlas .
```

You can also run the package without the installed console command:

```powershell
python -m repoatlas . --output-dir repoatlas_output
```

No API key is required for the CLI workflow. RepoAtlas V0.1 runs static analysis only unless application code explicitly invokes the semantic layer with an LLM client.

## Example

Given a small repository:

```text
Repository
├── robot.py
│   └── class RobotController
│       ├── move(position)
│       └── stop()
└── utils.py
    ├── calculate_distance(start, end)
    └── load_config()
```

RepoAtlas preserves signatures, line ranges, and available docstrings in the generated maps. A runnable analysis target is available in `examples/sample_repo/`.

## Output

By default, `repoatlas .` creates `repoatlas_output/` containing:

- `STRUCTURE.md` — human-readable details and a Mermaid mindmap
- `structure.json` — machine-readable repository structure
- `map.html` — interactive knowledge tree and symbol detail panel

Use `--output-dir PATH` to choose another output directory.

## Architecture

```text
Scanner
  ↓
Parser
  ↓
Analyzer
  ↓
RepositoryInfo
  ├── Renderer   → STRUCTURE.md
  └── Visualizer → structure.json + map.html
```

The optional semantic flow looks like this:

```text
LLMConfig
  ↓
LLM Factory
  ↓
OpenAICompatibleClient
  ↓
Semantic Summarizer
  ↓
SemanticSummary index
  ↓
Visualizer
```

## Roadmap

- Opt-in CLI orchestration for semantic summaries
- Import and dependency graphs
- Task-aware file ranking
- MCP integration
- More programming languages
- Incremental analysis and caching

Roadmap items are not implemented features.

## Development

Install development dependencies and run all tests:

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

See `CONTRIBUTING.md` for the short contribution guide.

## Security

Never commit API keys to the repository. Applications using the optional LLM layer should obtain credentials from environment variables or local configuration. Tests use fake HTTP responses and must not contact real model APIs.
