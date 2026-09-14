**English** | [简体中文](README.zh-CN.md)

# RepoMosaic

Turn an unfamiliar Python repository into a human-first, agent-readable knowledge map.

RepoMosaic runs static analysis locally and produces a Markdown overview, structured JSON, and an interactive Repository Knowledge Canvas. Optional, opt-in LLM summaries add concise semantic explanations in eight supported languages.

## Status

**Active Development — usable V0.1 CLI and library.** RepoMosaic currently analyzes Python source repositories. Its static outputs do not require an API key; semantic summaries are optional.

## Demo

▶ **[Watch the 40-second RepoMosaic demo](docs/assets/repomosaic-demo.mp4)**

RepoMosaic turns an unfamiliar Python repository into a navigable knowledge canvas. In the demo, a real repository has already been analyzed into files, classes, functions, and methods. The developer searches for a symbol, selects it to inspect its path, type, signature, developer-written docstring, and optional AI summary, then moves from repository-level context to the corresponding source code. Zooming and panning make it practical to switch between the whole structure and a local implementation.

```text
Repository
└── File
    ├── Class
    │   └── Method
    └── Function
```

- **Understand a module:** a File node shows its module description, optional semantic summary, and contained classes and functions.
- **Understand an object or subsystem:** a Class node shows its responsibility, source location, docstring, optional semantic explanation, and methods.
- **Locate an operation:** a Function or Method node connects its signature and source location to its description, optional summary, and source code. Methods retain class context through qualified names such as `ClassName.method_name`.
- **Find a known name:** search locates the symbol and keeps it visible within the surrounding repository structure.

Static analysis builds the map from source facts such as symbols, signatures, line ranges, and ownership relationships. Optional semantic analysis explains what those facts mean. RepoMosaic does not execute functions or dynamically observe runtime behavior.

## Key features

- Local Python AST analysis for files, classes, methods, functions, signatures, line ranges, and docstrings
- Interactive Knowledge Canvas with search, filters, source viewing, and VS Code handoff
- Optional grounded AI semantic summaries through an OpenAI-compatible provider
- User-level API-key storage through the operating system credential store
- Stable structured data for Coding Agents and an optional MCP server
- Markdown, Mermaid, JSON, and self-contained HTML outputs

## Quick Start

### 1. Install RepoMosaic

Recommended:

```bash
uv tool install repomosaic
```

This installs RepoMosaic in an isolated environment and makes the `repomosaic` command available globally. Install it once, then use it from different repositories without activating a dedicated RepoMosaic virtual environment each time.

Alternatively:

```bash
pip install repomosaic
```

If you install RepoMosaic inside a Python virtual environment, activate that environment whenever you want to use the `repomosaic` command.

### 2. Save your API key once

```bash
repomosaic auth set
```

The key is entered through a hidden prompt and stored in the system credential store.

### 3. Configure a project

```bash
cd path/to/project
repomosaic init
```

Answer the model, base URL, and output-language prompts. RepoMosaic writes `.repomosaic.toml` for you.

### 4. Build the knowledge map

```bash
repomosaic .
```

### 5. Explore

Open `repomosaic_output/map.html` in a browser, or read `repomosaic_output/STRUCTURE.md` on GitHub or in VS Code.

## Static-only mode

No API key or model service is needed for local static analysis:

```bash
repomosaic . --no-llm
```

`--no-llm` prevents model API calls even when a project contains LLM settings.

## Authentication

```bash
repomosaic auth set
repomosaic auth status
repomosaic auth clear
```

- `set` saves one default RepoMosaic credential using Windows Credential Manager, macOS Keychain, or a supported Linux keyring backend.
- `status` reports only whether a key is available and its source; it never prints the key.
- `clear` removes only the stored RepoMosaic credential.

For temporary use, the `REPOMOSAIC_API_KEY` environment variable overrides the stored credential. It is not necessary to save a separate key for every repository.

## Generated outputs

By default, RepoMosaic creates `repomosaic_output/`:

- `map.html` — self-contained interactive Repository Knowledge Canvas
- `STRUCTURE.md` — detailed Markdown map with a Mermaid overview
- `structure.json` — machine-readable repository and symbol data

Use `--output-dir PATH` to choose another directory.

The default `repomosaic_output` directory represents the latest generated atlas for the current repository, so a later run may replace those files. To preserve static and semantic versions separately, choose distinct output directories:

```bash
# Keep a static atlas
repomosaic . --no-llm --output-dir repomosaic_output_static

# Keep a semantic atlas
repomosaic . --output-dir repomosaic_output_semantic
```

## How RepoMosaic works

```text
Local repository
  → scanner
  → Python AST parser
  → RepositoryInfo
      ├── Markdown renderer
      ├── JSON / Knowledge Canvas renderer
      └── optional grounded semantic summaries
```

Static analysis remains the source of structural facts. When LLM mode is enabled, only relevant source or compressed symbol context is sent to the configured provider for summaries; generated text does not replace original docstrings.

## Coding Agent and MCP usage

The Python Agent API exposes repository structure, symbol search, and source lookup without requiring a UI. For MCP clients, install the optional dependency and start a server bound to one repository:

```bash
pip install "repomosaic[mcp]"
repomosaic-mcp path/to/project
```

The MCP server uses stdio and exposes `get_repository_structure`, `find_symbol`, and `get_symbol_source` tools. Configure the command in your MCP client according to that client's documentation.

## Configuration reference

Interactive setup:

```bash
repomosaic init
```

Advanced users can create a commented template with `repomosaic init --template`. Existing configuration is protected unless `--force` is supplied.

Project configuration contains non-secret LLM settings:

```toml
[llm]
provider = "openai-compatible"
model = "your-model"
base_url = "https://your-provider.example/v1"
language = "en"
```

CLI options `--provider`, `--model`, `--base-url`, and `--lang` override `.repomosaic.toml`. Supported canonical language codes are `en`, `zh-CN`, `ja`, `ko`, `de`, `it`, `pt`, and `es`.

## Privacy and security

- Static analysis and `--no-llm` run locally without model API calls.
- LLM summaries are optional and opt-in.
- LLM mode sends relevant source code and repository context to the user-configured provider.
- Credentials are resolved from `REPOMOSAIC_API_KEY` first, then the system credential store.
- API keys are never written to `.repomosaic.toml`, `structure.json`, `map.html`, `STRUCTURE.md`, or other generated outputs.
- Never commit API keys. Review your provider's privacy, retention, and data-use policies before analyzing a private repository with LLM features.

## Current limitations

- Source analysis is currently Python-specific and AST-based; RepoMosaic does not execute or dynamically trace the target repository.
- Call graphs, runtime data flow, dependency resolution across installed packages, and semantic equivalence are outside the current static model.
- Optional summaries depend on the configured OpenAI-compatible provider and should be reviewed rather than treated as source facts.
- The generated Knowledge Canvas is a self-contained local HTML artifact, not a hosted collaborative service.
- MCP mode exposes the implemented repository structure, symbol search, and source lookup tools; it is not a general coding-agent runtime.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## License

RepoMosaic is licensed under the [Apache License 2.0](LICENSE).
