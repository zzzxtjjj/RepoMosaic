[English](README.md) | **简体中文**

# RepoMosaic

把陌生的 Python 仓库转换成人类易读、Coding Agent 可用的代码知识地图。

RepoMosaic 在本地执行静态分析，并生成 Markdown 总览、结构化 JSON 和可交互的仓库知识画布。用户还可以主动启用 LLM，用八种受支持语言生成简洁的 AI 语义摘要。

## 演示

▶ **[观看约 40 秒的 RepoMosaic 演示](docs/assets/repomosaic-demo.mp4)**

RepoMosaic 会把陌生的 Python 仓库转换成可导航的代码知识图谱。演示打开的是一个已经完成分析的真实仓库，其中的代码被拆解成 File、Class、Function 和 Method。开发者可以搜索目标 symbol，选中节点后查看路径、类型、签名、开发者编写的 docstring 和可选的 AI 语义摘要，再从仓库级上下文进入对应源码。缩放和平移则帮助开发者在整体结构与局部实现之间切换。

```text
Repository
└── File
    ├── Class
    │   └── Method
    └── Function
```

- **理解一个模块：**File 节点展示模块说明、可选语义摘要，以及其中包含的 Class 和 Function。
- **理解一个对象或子系统：**Class 节点展示职责、源码位置、docstring、可选语义解释和所属 Method。
- **定位一项操作：**Function 或 Method 节点把签名和源码位置与说明、可选摘要及实际源码连接起来。Method 会保留所属 Class 上下文，并使用 `ClassName.method_name` 形式的限定名称。
- **只知道名称、不知道位置：**搜索可以定位 symbol，同时保留它在仓库结构中的上下文。

静态分析根据 symbol、签名、行号范围和归属关系等源码事实构建地图；可选的语义分析进一步解释这些事实代表什么。RepoMosaic 不会执行函数，也不会动态观察程序运行行为。

## 核心功能

- 基于 Python AST 在本地提取文件、类、方法、函数、签名、行号范围和 docstring
- 可交互的仓库知识画布，支持搜索、过滤、源码查看和跳转到 VS Code
- 通过 OpenAI-compatible provider 生成可选且有源码依据的 AI 语义摘要
- 通过操作系统凭据存储保存一次用户级 API key
- 为 Coding Agent 提供稳定结构化数据，并提供可选 MCP server
- 输出 Markdown、Mermaid、JSON 和单文件 HTML

## 快速开始

### 1. 安装 RepoMosaic

推荐方式：

```bash
uv tool install repomosaic
```

该命令会把 RepoMosaic 安装到独立环境中，并让 `repomosaic` 命令在全局可用。只需安装一次，之后进入不同代码仓库即可使用，不需要每次手动激活 RepoMosaic 专用虚拟环境。

备选方式：

```bash
pip install repomosaic
```

如果把 RepoMosaic 安装在 Python 虚拟环境中，使用 `repomosaic` 命令前必须先激活该环境。

### 2. 保存一次 API key

```bash
repomosaic auth set
```

API key 通过隐藏输入读取，并保存在系统凭据存储中。

### 3. 配置项目

```bash
cd path/to/project
repomosaic init
```

按提示选择模型、Base URL 和输出语言，RepoMosaic 会自动写入 `.repomosaic.toml`。

### 4. 生成知识地图

```bash
repomosaic .
```

### 5. 浏览结果

在浏览器中打开 `repomosaic_output/map.html`，也可以在 GitHub 或 VS Code 中阅读 `repomosaic_output/STRUCTURE.md`。

## 仅静态分析模式

本地静态分析不需要 API key 或模型服务：

```bash
repomosaic . --no-llm
```

即使项目中存在 LLM 配置，`--no-llm` 也会阻止模型 API 调用。

## 身份认证

```bash
repomosaic auth set
repomosaic auth status
repomosaic auth clear
```

- `set` 使用 Windows Credential Manager、macOS Keychain 或受支持的 Linux keyring 后端保存一个默认 RepoMosaic 凭据。
- `status` 只显示 API key 是否可用及其来源，绝不会输出 key。
- `clear` 只删除 RepoMosaic 保存的凭据。

临时使用时，可以通过 `REPOMOSAIC_API_KEY` 环境变量覆盖已保存的凭据。不同仓库不需要重复保存 API key。

## 生成结果

RepoMosaic 默认创建 `repomosaic_output/`：

- `map.html` — 单文件、可交互的仓库知识画布
- `STRUCTURE.md` — 包含 Mermaid 总览的详细 Markdown 地图
- `structure.json` — 面向工具的仓库与 symbol 结构化数据

可使用 `--output-dir PATH` 指定其他目录。

默认的 `repomosaic_output` 表示当前仓库最近一次生成的知识地图，因此后续运行可能替换其中的文件。如果希望分别保留静态分析版和语义增强版，可以指定不同的输出目录：

```bash
# 保留静态分析版
repomosaic . --no-llm --output-dir repomosaic_output_static

# 保留语义增强版
repomosaic . --output-dir repomosaic_output_semantic
```

## RepoMosaic 如何工作

```text
本地代码仓库
  → scanner
  → Python AST parser
  → RepositoryInfo
      ├── Markdown renderer
      ├── JSON / 仓库知识画布 renderer
      └── 可选的、有证据依据的 AI 语义摘要
```

静态分析始终是结构事实的来源。启用 LLM 后，RepoMosaic 只向配置的 provider 发送相关源码或压缩后的 symbol 上下文，用于生成摘要；生成内容不会替换原始 docstring。

## Coding Agent 与 MCP

Python Agent API 可以在不依赖 UI 的情况下读取仓库结构、搜索 symbol 和查询源码。MCP 客户端可安装可选依赖，并启动绑定到单个仓库的 server：

```bash
pip install "repomosaic[mcp]"
repomosaic-mcp path/to/project
```

MCP server 使用 stdio，并提供 `get_repository_structure`、`find_symbol` 和 `get_symbol_source` 工具。请按照所使用 MCP 客户端的文档配置这条命令。

## 配置参考

交互式初始化：

```bash
repomosaic init
```

高级用户可以通过 `repomosaic init --template` 创建带注释模板。已有配置不会被覆盖，除非明确传入 `--force`。

项目配置只包含非敏感的 LLM 设置：

```toml
[llm]
provider = "openai-compatible"
model = "your-model"
base_url = "https://your-provider.example/v1"
language = "zh-CN"
```

CLI 参数 `--provider`、`--model`、`--base-url` 和 `--lang` 的优先级高于 `.repomosaic.toml`。受支持的 canonical language code 为 `en`、`zh-CN`、`ja`、`ko`、`de`、`it`、`pt` 和 `es`。

## 隐私与安全

- 静态分析和 `--no-llm` 在本地执行，不调用模型 API。
- LLM 摘要是可选、主动启用的功能。
- LLM 模式会把相关源码和仓库上下文发送给用户配置的 provider。
- 凭据解析顺序为 `REPOMOSAIC_API_KEY` 环境变量优先，其次是系统凭据存储。
- API key 绝不会写入 `.repomosaic.toml`、`structure.json`、`map.html`、`STRUCTURE.md` 或其他生成结果。
- 不要提交 API key。对私有仓库启用 LLM 功能前，请检查 provider 的隐私、数据保留和数据使用政策。

## 开发

```bash
python -m pip install -e ".[dev]"
python -m pytest
```

贡献说明请参阅 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 许可证

RepoMosaic 使用 [Apache License 2.0](LICENSE)。
