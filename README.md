**English** | [简体中文](README.zh-CN.md)

# RepoAtlas

Turn an unfamiliar Python repository into a human-first, agent-readable knowledge map.

RepoAtlas runs static analysis locally and produces a Markdown overview, structured JSON, and an interactive Repository Knowledge Canvas. Optional, opt-in LLM summaries add concise semantic explanations in eight supported languages.

## Key features

- Local Python AST analysis for files, classes, methods, functions, signatures, line ranges, and docstrings
- Interactive Knowledge Canvas with search, filters, source viewing, and VS Code handoff
- Optional grounded AI semantic summaries through an OpenAI-compatible provider
- User-level API-key storage through the operating system credential store
- Stable structured data for Coding Agents and an optional MCP server
- Markdown, Mermaid, JSON, and self-contained HTML outputs

## Quick Start

### 1. Install RepoAtlas

Recommended:

```bash
uv tool install repoatlas
```

This installs RepoAtlas in an isolated environment and makes the `repoatlas` command available globally. Install it once, then use it from different repositories without activating a dedicated RepoAtlas virtual environment each time.

Alternatively:

```bash
pip install repoatlas
```

If you install RepoAtlas inside a Python virtual environment, activate that environment whenever you want to use the `repoatlas` command.

### 2. Save your API key once

```bash
repoatlas auth set
```

The key is entered through a hidden prompt and stored in the system credential store.

### 3. Configure a project

```bash
cd path/to/project
repoatlas init
```

Answer the model, base URL, and output-language prompts. RepoAtlas writes `.repoatlas.toml` for you.

### 4. Build the knowledge map

```bash
repoatlas .
```

### 5. Explore

Open `repoatlas_output/map.html` in a browser, or read `repoatlas_output/STRUCTURE.md` on GitHub or in VS Code.

## Static-only mode

No API key or model service is needed for local static analysis:

```bash
repoatlas . --no-llm
```

`--no-llm` prevents model API calls even when a project contains LLM settings.

## Authentication

```bash
repoatlas auth set
repoatlas auth status
repoatlas auth clear
```

- `set` saves one default RepoAtlas credential using Windows Credential Manager, macOS Keychain, or a supported Linux keyring backend.
- `status` reports only whether a key is available and its source; it never prints the key.
- `clear` removes only the stored RepoAtlas credential.

For temporary use, the `REPOATLAS_API_KEY` environment variable overrides the stored credential. It is not necessary to save a separate key for every repository.

## Generated outputs

By default, RepoAtlas creates `repoatlas_output/`:

- `map.html` — self-contained interactive Repository Knowledge Canvas
- `STRUCTURE.md` — detailed Markdown map with a Mermaid overview
- `structure.json` — machine-readable repository and symbol data

Use `--output-dir PATH` to choose another directory.

## How RepoAtlas works

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
pip install "repoatlas[mcp]"
repoatlas-mcp path/to/project
```

The MCP server uses stdio and exposes `get_repository_structure`, `find_symbol`, and `get_symbol_source` tools. Configure the command in your MCP client according to that client's documentation.

## Configuration reference

Interactive setup:

```bash
repoatlas init
```

Advanced users can create a commented template with `repoatlas init --template`. Existing configuration is protected unless `--force` is supplied.

Project configuration contains non-secret LLM settings:

```toml
[llm]
provider = "openai-compatible"
model = "your-model"
base_url = "https://your-provider.example/v1"
language = "en"
```

CLI options `--provider`, `--model`, `--base-url`, and `--lang` override `.repoatlas.toml`. Supported canonical language codes are `en`, `zh-CN`, `ja`, `ko`, `de`, `it`, `pt`, and `es`.

## Privacy and security

- Static analysis and `--no-llm` run locally without model API calls.
- LLM summaries are optional and opt-in.
- LLM mode sends relevant source code and repository context to the user-configured provider.
- Credentials are resolved from `REPOATLAS_API_KEY` first, then the system credential store.
- API keys are never written to `.repoatlas.toml`, `structure.json`, `map.html`, `STRUCTURE.md`, or other generated outputs.
- Never commit API keys. Review your provider's privacy, retention, and data-use policies before analyzing a private repository with LLM features.

## Development

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## License

RepoAtlas is licensed under the [Apache License 2.0](LICENSE).
