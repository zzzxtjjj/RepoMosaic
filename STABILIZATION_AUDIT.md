# RepoAtlas Core V0.1 stabilization audit

审计日期：2026-09-12。范围：当前工作区（含尚未提交的 module docstring 和画布修改）。

本次以审计为主，未修改 Python、HTML、CLI、语义或 LLM 实现，未执行真实模型请求、发布或 commit。唯一安全修复是在 .gitignore 增加 qwen_flash_test/；预览产物全部保留。

## 1. Overall health assessment

主干功能和分层可用，正常输入路径已获得较好测试覆盖。但当前不宜把 Core V0.1 冻结为稳定的 MCP/PyPI 接口：外部服务失败处理、路径契约、参数完整性和库级输入校验仍有缺口。建议完成下列 P1 最小修复后再冻结；无需重建架构。

## 2. Test result and evidence

- python -m pytest：55 passed in 0.29s（Windows，Python 3.12）。
- python -m repoatlas --help：成功，包含 provider/model/base-url/lang/no-llm。
- python -m repoatlas examples/sample_repo --no-llm：成功，生成 repoatlas_output 下三个文件。
- 额外离线探针：13 种网络/响应失败、unsupported provider、复杂参数、UTF-8 BOM、工作目录改变、越界 FileInfo、非法语言、Fake LLM 中英文/密钥流、wheel/sdist 构建及解包运行。
- Fake LLM CLI 对示例仓库发送 10 次请求；zh-CN 传入所有 prompt；有模块 docstring 的文件仍生成摘要；测试密钥只传入客户端配置，没有出现在三个输出文件。
- 本次未运行 Linux/macOS，未启动 VS Code，未向真实服务发送请求。Windows 创建符号链接的诊断夹具受到系统限制，相关风险来自代码检查，不冒充已完成的符号链接运行测试。

当前测试覆盖 scanner、parser、analyzer、模块 docstring、Markdown renderer、visualizer、文件 Description、AI Summary、prompts、summarizer、language helper、summary index、factory、HTTP mock 成功路径、CLI static、不完整参数、no-llm 覆盖、Fake LLM CLI、端到端分析。

最高价值的缺失回归：HTTP/超时/响应格式失败参数化测试；CLI unsupported provider（factory 已覆盖，但 CLI 无持久回归）；环境变量测试密钥不落盘；库级非法语言零调用；相对根路径跨 cwd；合法完整参数；UTF-8 BOM/编码异常；路径越界/符号链接；构建安装后的模板加载；浏览器实际交互。此次诊断探针没有冒充新增的 pytest coverage。

## 3. P0 — must fix before continuing

未确认 P0。没有发现实际密钥泄露、数据损坏或缺失模板导致包不可用的问题。此结论仅针对已检查工作区，不是凭据历史扫描或所有输入的安全保证。

## 4. P1 — should fix before MCP/PyPI

### P1-1：LLM 失败越过 CLI 异常边界

- 文件：repoatlas/llm/openai_compatible.py:42；repoatlas/cli.py:156。
- 问题：CLI 只捕获文件系统和 SyntaxError；网络异常与响应验证异常不在处理范围。离线复现 connection→ConnectError、timeout→ReadTimeout，400/401/403/404/429/500/503→HTTPStatusError，非法 JSON→JSONDecodeError，缺失 choices→KeyError，空 choices→IndexError，content=null→后续 strip 的 AttributeError。命令行入口会显示 traceback。
- 影响：预期的服务故障被当作程序崩溃；MCP 难以提供稳定错误；仓库处理中途失败丢弃本轮内存摘要。HTTP 错误信息可能带 URL，不能直接把含用户信息或 query 的 URL 原样交给用户。
- 最小建议：客户端明确 timeout，验证 choices/message/content，统一为一个简单 LLMError（或清楚约定的异常类型）；CLI 只捕获该异常，输出经过脱敏的状态分类并返回 1。配置错误仍返回 2。保留异常链供内部调试，但不向终端输出响应全文、Authorization 或带凭据 URL。不添加复杂错误框架或无限重试。
- 需要回归：上述失败矩阵、错误不泄密、非字符串/空响应；timeout 可先用明确默认值，不必重设计配置。

### P1-2：路径身份依赖进程当前目录，缺少文件边界契约

- 文件：repoatlas/core/analyzer.py:10、33；repoatlas/core/scanner.py:31；repoatlas/semantic/summarizer.py:59、74；repoatlas/rendering/visualizer.py:44。
- 问题：analyze_repository 保存传入的相对 root_path。分析 examples/sample_repo 后改变 cwd，再序列化，实际复现所有文件 source 为空；summarizer 则会读文件失败。FileInfo.path 也未经越界验证：手动传入 ../outside.py 可读取根目录外源码。scanner 未对文件符号链接的 resolved target 检查 containment。
- 影响：长生命周期 MCP 调用不能可靠复用模型；若未来适配器接受不可信模型或扫描含外部链接的仓库，会越过授权仓库边界。当前尚无 MCP，不把这一风险表述为已经发生的远程漏洞。
- 最小建议：analyze_repository 入口 expanduser().resolve() 后保存绝对 POSIX root；约定 FileInfo.path 必须是仓库相对路径；实际读取前 resolve 并验证位于根内，明确外部链接拒绝/跳过策略。MCP 还应限制允许的仓库根。不要仅做字符串前缀判断。
- 需要回归：跨 cwd、../、绝对路径、根内/根外链接（平台支持时）。

### P1-3：合法函数参数静默遗漏

- 文件：repoatlas/core/parser.py:44–50。
- 问题：仅提取 node.args.args。对 def f(a, /, b=1, *args, flag=True, **kwargs)，实际输出 parameters=['b']、签名 f(b)。
- 影响：返回结构看似完整却缺失真实输入；未来 agent 用它定位或理解函数会得到错误信息。这是当前参数提取功能的正确性缺口，不是要求完整 Python 语义分析。
- 最小建议：至少覆盖 posonlyargs、args、vararg、kwonlyargs、kwarg 并按源码顺序处理，明确 parameters 字段究竟保存参数名还是可展示签名片段；不必本轮增加复杂模型。默认值和注解的完整重建可继续延后。
- 需要回归：位置专用、关键字专用、*args/**kwargs、async、self/cls。

### P1-4：库级语义 API 不执行语言校验

- 文件：repoatlas/semantic/summarizer.py:9、23、37、67；repoatlas/semantic/languages.py:15。
- 问题：validate_language 存在，但 summarizer 未调用。CLI argparse 可限制八种语言，直接调用 summarize_repository(..., 'invalid-language', fake) 却成功发送了 10 次请求并保存非法语言。
- 影响：MCP 复用时不能依赖 CLI 校验，无效输入会消耗模型请求。
- 最小建议：在公开 summarizer 入口复用现有 validate_language，保证调用模型前失败；空仓库同样应验证。索引规则和 SemanticSummary 不必更改。
- 需要回归：不支持的语言返回清晰错误且 Fake LLM 调用数为 0。

### P1-5：发布文档与 CLI 的真实网络行为矛盾；缺少许可证声明

- 文件：README.md:9、49、110；pyproject.toml；项目根（无 LICENSE 文件）。
- 问题：README 仍声称 CLI 永不调用模型，并把 opt-in CLI orchestration 列为 roadmap，当前 CLI 已实际支持该流程。仓库未提供许可证文件或对应包元数据。
- 影响：用户无法准确判断何时源码会发送给模型提供方；开源发布前的许可选择也尚未明确。
- 最小建议：说明默认静态、完整 LLM 参数显式开启、no-llm 优先、REPOATLAS_API_KEY 用途、发送的源码/符号内容、费用与输出隐私；由项目所有者选择许可证后加入文件与元数据。审计不替所有者选择许可证。
- 需要验证：文档示例与 --help 一致；新构建包含所选许可证。

### P1-6：默认输出目录内 Markdown 源码链接指向错误位置

- 文件：repoatlas/rendering/renderer.py:39–52；repoatlas/rendering/visualizer.py:280。
- 问题：STRUCTURE.md 位于 repoatlas_output/，链接仍按仓库根生成 robot.py 或 repoatlas/core/parser.py，浏览器会相对输出目录寻找源码。示例输出内 robot.py 不存在，已核验。
- 影响：公开输出中承诺的源码导航在默认 CLI 路径下不可用；空格、括号等路径也没有 URL/Markdown 转义。
- 最小建议：保留独立 renderer 原 API，通过可选 link-base 或导出上下文把源码路径转换为相对 Markdown 文件的位置，并编码路径。对输出在另一磁盘/仓库外的场景明确 fallback。
- 需要回归：默认 output 子目录、任意输出目录、Windows 跨盘、空格/括号路径。

## 5. P2 — desirable improvement

- qwen_flash_test/ 未忽略：本轮已做唯一安全修复，加入 .gitignore。目录未 tracked，内容未删除。output/、repoatlas_output/、缓存和 egg-info 已忽略且无 tracked 产物。
- UTF-8 BOM：合法 BOM Python 文件在当前 read_text('utf-8')→ast.parse 流程抛 SyntaxError。PEP 263 非 UTF-8 源码可能抛未捕获 UnicodeDecodeError。建议后续统一采用 Python 源码编码读取方式，同时用于 semantic 源码提取；UTF-8 无 BOM 与 Unicode docstring 正常。
- 文件 prompt 缺少已存在的 module_docstring，也没有源码或顶层赋值/副作用信息；无符号文件仅给路径和 None，证据很弱。建议加入模块文档或受限源码证据，同时继续生成 LLM 摘要，不把 docstring 当作摘要替代品。
- extract_source_lines 不验证 1 <= start <= end <= 文件行数；切片对越界/负数静默处理。使用 parser 当次结果时通常有效，但文件修改或外部构造模型时需明确错误。
- 文件在分析、摘要、导出之间变化可能导致行号和源码不一致。明确快照/mtime 契约后再考虑持久化。
- scanner 在 rglob 后过滤目录，没有真正剪枝；不支持 .gitignore、生成目录/敏感源码配置，也不排序。大量依赖目录会增加扫描成本，Git 忽略的 Python 文件仍可能进入输出/模型输入。
- 无 LICENSE 之外，包缺 project URLs、维护者信息等完善元数据；属于发布质量补充。CI 仅 Ubuntu 3.11/3.12、editable install，没有 Windows/macOS 和 wheel install 测试。
- render_structure_markdown 尚未使用 module_docstring；本次要求的 HTML 数据流正常，但 Markdown 未展示该信息。
- 同名重复 class 的 UI 归属仅按 class_name，可能合并不同声明的方法；在当前简单顶层符号范围内较少见，稳定身份扩展时应处理。
- JSON/HTML/Markdown 顺序直接写入，无原子替换/整体成功标识；写入失败可留下混合版本。建议临时文件成功后替换，但不引入事务框架。
- LLMConfig 默认 dataclass repr 包含 api_key；当前代码不打印配置，但建议将密钥字段 repr=False，避免未来日志误用。
- semantic/__init__.py 仍写“预留包”；tests/test_summarizer.py 重复导入部分 dataclass。属于文案/导入整理，无运行危害。

## 6. V0.1 limitation — intentionally deferred

- 只分析 Python 顶层函数、顶层类及其直接方法；嵌套函数、嵌套类、条件语句中的定义、继承/调用图/导入图不处理。
- 支持 def/async def；不记录 async 标记、装饰器或完整默认值/类型注解。起始行是 def/class 行，装饰器不包含在源码范围内；staticmethod/classmethod 按普通方法结构处理。
- 一个语法错误即终止整仓库分析，CLI 对 SyntaxError 有可读错误；部分成功分析尚未设计。
- 没有缓存、批处理、并发、增量分析、预算、进度、取消或断点恢复。作为初版可以延后优化，但应明确当前成本与失败语义。
- 同步 API 适合一次性 CLI；未来 MCP 可在适配器层管理进度/取消，不必重写 Core。

## 7. Architecture boundary assessment

- core 只依赖标准库与结构化模型，无 rendering/CLI/LLM 反向依赖。
- llm 负责 config/factory/HTTP，LLMClient Protocol 保留为统一接口，无仓库业务逻辑。
- semantic 依赖 core 模型、LLMClient、prompt/index；不渲染。
- rendering 依赖 core 模型、build_signature 和 semantic 的纯数据/index；不创建 LLM、不读环境密钥、不构造 prompt。其源码读取依赖路径契约，见 P1-2。
- CLI 组合已有层，没有复制 summarizer 或 renderer 逻辑；配置验证与输出错误处理属于其合理职责。
- 导入 llm.base 时包 __init__ 会加载 factory/httpx，但当前 httpx 是必需依赖，也无网络副作用；不构成必须改架构的阻塞。

## 8. Public API readiness for MCP

目前 MCP 可使用公开模块级函数，无需调用 _serialize_*、_lookup_summary 等私有 helper：

- repoatlas.core.analyzer.analyze_repository
- repoatlas.core.symbols：RepositoryInfo / FileInfo / ClassInfo / FunctionInfo
- repoatlas.semantic.summarizer.summarize_repository
- repoatlas.semantic.models.SemanticSummary
- repoatlas.semantic.index：make_summary_key / build_summary_index
- repoatlas.llm：LLMClient / LLMConfig / create_llm_client
- repoatlas.rendering.visualizer：repository_to_dict / export_repository_json / render_visual_map

最小后续 API 整理：文档化并可在 core/__init__.py、semantic/__init__.py 做少量 re-export；无需 facade 或依赖注入框架。冻结前应约定绝对 root、相对 file path、行号含端点、语言与异常规则。

visualizer API 的 summaries=None/lang 参数继续兼容；但输出含完整 source 和本机 vscode_uri，MCP 不应未经选择直接把整个 visualizer JSON 当作精简工具响应。需在适配层选择需要的结构字段，后续再决定是否引入独立的纯结构导出。

## 9. LLM reliability assessment

- base_url 仅 rstrip('/') 后拼 /chat/completions；用户应给 API 根（如含 /v1），不是完整 endpoint。输入已有 endpoint、query、userinfo 或无效 scheme 时没有早期校验。
- Content-Type、可选 Bearer、model/messages 和 raise_for_status 正常。
- 本机已安装 httpx.post 的真实默认 timeout 是 Timeout(timeout=5.0)，不是“无限等待”，也不是整仓库总时限。未显式配置，模型读响应超过默认等待窗口会失败。
- 返回体完全信任 choices[0].message.content；缺少容错、字符串验证和可用错误，详见 P1-1。
- 当前 CLI 无重试，也不在失败后输出本轮已完成摘要；需优先定义失败策略，再做缓存优化。

## 10. Packaging / PyPI risks

在临时源码副本使用本机 setuptools backend 实际构建 wheel 和 sdist；两者均含 repoatlas/rendering/templates/map.html。wheel 中未发现 output/qwen/.pyc；解包后强制从该路径 import（已校验 __file__），成功生成三个输出并运行 --version=0.1.0。

这是本机后端构建与解包运行检查，不是干净网络隔离安装或 PyPI 发布演练；依赖使用本机已安装版本。构建临时副本只包含包、README、pyproject，因此不据此宣称全部 sdist 非包文件清单已审计。

requires-python >=3.11、httpx>=0.27、pytest dev extra、repoatlas.cli:main、动态 __version__、testpaths 均一致。没有发现严重打包故障。冻结前处理 P1-5；CI 加一次构建/安装 wheel 并从 checkout 外运行的 smoke test，可防止 editable install 掩盖模板遗漏。

## 11. Cross-platform risks

- P1-2：相对根路径依赖 cwd，所有平台均受影响。
- P2：本机 Windows drive URI 与空格编码已有测试；POSIX、UNC、Unicode、#/%/:、根路径为 /、Windows 字符串在 POSIX 主机解释尚无完整回归。不要把 Windows 测试通过等同于 Linux/macOS URI 可用。
- 文件路径由 scanner 输出正斜杠；普通文件系统读取用 pathlib，正常本机平台路径设计合理。
- HTML 内嵌 JSON/CSS/JS，不 fetch 本地 JSON、无 CDN/服务端依赖，适合 file://。vscode 协议能否打开由本机安装和浏览器决定。
- README Quick Start 的激活命令仅 PowerShell；CONTRIBUTING 的 venv 创建后未明确激活命令，需补平台说明。

## 12. Security / privacy result

对 repoatlas/tests/examples 及当前 output/repoatlas_output/qwen_flash_test 中 51 个文本文件进行不打印匹配值的常见凭据模式检查，未命中疑似真实凭据。测试 test-key 为 mock。未读取或输出当前真实 REPOATLAS_API_KEY，未扫描 Git 历史、虚拟环境或任意二进制；不能保证不存在非标准形态的 secret/个人信息。

另外使用临时 mock 环境变量验证 CLI：配置收到测试 key，JSON/HTML/Markdown 均没有该 sentinel。现有三类输出 JSON 结构没有 api_key/llm_config/Authorization 字段。

仍须明确：输出嵌入完整仓库 Python 源码与本机绝对路径，不能保证源码内硬编码秘密不会被复制；LLM prompt 同样会发送函数/类源码。当前没有自动脱敏或 ignore-based 隐私排除。共享地图前应审阅，未来 MCP 需明确仓库授权边界。

HTML 对嵌入 JSON 中 <、>、& 做转义，节点/摘要/代码使用 textContent，源码未被执行；未发现当前动态 HTML 注入入口。Markdown 路径/标签转义仍需修复，见 P1-6。

## 13. Truly redundant files

没有确认可删除的源码文件。旧根级 scanner/parser/analyzer/symbols/renderer/visualizer 副本不存在，未发现旧 import 或 make_lookup_key。LLMClient Protocol、包 re-export、测试 FakeLLM 都有职责；同名 helper 不能仅按名字视为重复。

JSON 写入已经统一为 _write_json。未见残留调试 print；CLI print 是用户输出。未删除测试、源码、.venv 或当前预览。

## 14. Recommended fixes BEFORE MCP

建议按四个小批次完成：

1. 客户端错误/响应验证/显式 timeout + CLI 脱敏错误 + 失败矩阵测试（P1-1）。
2. 根路径/越界规则 + 参数提取 + 库级语言校验及回归（P1-2/3/4）。
3. 默认 Markdown 链接正确性（P1-6），清楚描述代码数据、行号及异常契约，文档化公共 API。
4. README 与真实 LLM 流一致；由所有者确认许可证；加入 wheel smoke CI（P1-5 与相关 P2）。

## 15. Recommended tasks AFTER MCP

当前请求数严格为 F + C + U + M：每文件、每类、每普通函数、每方法各一次。示例仓库为 3+1+3+3=10；当前 RepoAtlas 为 38+18+107+21=184。没有执行这些真实请求。

按单次平均 1–3 秒估算，184 次串行约 3.1–9.2 分钟；5–10 秒约 15.3–30.7 分钟。这是情景估算，不是实测速度或费用。大类源码包含方法，方法又单独发送；固定 prompt 重复；每符号源码提取都再次读取整个文件。每次重跑重新付费，任何中途异常都会终止当前流程，先前完成的内存摘要没有持久化。

优化优先级：

1. 进度、请求数预估、预算/取消、错误与部分结果策略。
2. 可恢复的摘要持久化，再加以源码 hash、符号身份、语言、model/provider/prompt version 为键的缓存。
3. 每文件只读取一次，加入上下文长度限制。
4. 有界并发、限速和受控退避；认证/请求错误不要盲重试。
5. 最后考虑批量请求与增量仓库更新，验证不会破坏符号身份匹配。

本次不实现缓存、批量、MCP 或 VS Code extension。

## 16. Freeze decision

结论：可继续作为开发中的 V0.1 使用，尚不建议冻结为稳定 Core API 或直接发布。不存在需要重建架构的证据；先完成 P1 小修复及回归，再以新的全量测试、打包 smoke 和明确输入/异常契约作为冻结门槛。

本轮新增 STABILIZATION_AUDIT.md；.gitignore 仅增加 qwen_flash_test/。其余工作区修改属于此前任务/用户，已保留。未 commit。
