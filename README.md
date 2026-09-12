# RepoAtlas

Human-first and agent-readable repository knowledge maps.

## What is RepoAtlas?

RepoAtlas uses static analysis to turn a code repository into a browsable knowledge map. It extracts Python files, classes, functions, methods, signatures, line ranges, and docstrings, then presents that information as Markdown, Mermaid, JSON, and an interactive HTML map.

Static repository analysis runs locally. RepoAtlas can optionally generate multilingual semantic summaries through a user-configured LLM provider.

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
repoatlas . --no-llm
```

Both commands perform local static analysis. `--no-llm` explicitly disables model API calls, even if LLM options are also present.

To opt into semantic summaries, configure your provider and run:

```powershell
$env:REPOATLAS_API_KEY = "<your-provider-api-key>"
repoatlas . `
  --provider openai-compatible `
  --model your-model `
  --base-url https://your-provider.example/v1 `
  --lang en
```

`python -m repoatlas` accepts the same options as the installed `repoatlas` command. Supported summary languages are `zh-CN`, `en`, `ja`, `ko`, `de`, `it`, `pt`, and `es`.

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

## Network and privacy

Local static analysis does not call a model API. LLM summaries are opt-in and are enabled only when the provider, model, and base URL options are supplied without `--no-llm`.

When LLM mode is enabled, RepoAtlas sends relevant source code and repository context to the configured provider. API credentials are read from `REPOATLAS_API_KEY`; never commit this variable or its value to the repository. RepoAtlas does not include API keys in `structure.json`, `map.html`, `STRUCTURE.md`, or other generated outputs.

Before enabling LLM features for a private repository, review the selected provider's privacy, retention, and data-use policies.

## Roadmap

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

## License

RepoAtlas is licensed under the Apache License 2.0. See `LICENSE`.
