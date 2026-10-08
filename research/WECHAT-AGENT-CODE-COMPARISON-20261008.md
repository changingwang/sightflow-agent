# 微信 / 企业微信 AI Agent 代码级比较
## WECHAT-AGENT-CODE-COMPARISON-20261008

研究基线日期：2026-10-08
对象：
- hwh0825/wechat-auto-reply
- colorsbear/wxbot-auto-reply
- deepdadou/sightflow-agent
- lineCode/wecom-bot

本报告以各仓库当前默认分支可读取代码为主要证据，README 只作为定位辅助。结论区分 code evidence 与 inference。

## 1. 总结结论

四个项目代表四种不同的系统形态：

| 项目 | 核心路线 | 最强层 | 当前主要价值 |
|---|---|---|---|
| hwh0825/wechat-auto-reply | OCR + Windows 截图 + 受控发送 | 执行可靠性 / 安全停机 | 微信 4.x 桌面执行器 |
| colorsbear/wxbot-auto-reply | UIA 读写 + WeFlow 读消息 + LLM | 输入解耦 + context/memory + 能力分发 | 微信 Agent 应用骨架 |
| deepdadou/sightflow-agent | 通用视觉 Driver + Scanner/OCR | 抽象层 | 通用 IM Agent 的概念骨架，当前实现成熟度不足 |
| lineCode/wecom-bot | Bot WS + Agent API + 多账号 + Capability | 组织入口 / 路由 / capability governance | 企业微信组织级 Agent 通道 |

最重要的研究发现：

1. 输入层已经可以明显解耦。colorsbear 直接出现“读消息平面”和“发消息平面”分离：WeFlow 负责只读消息，UIA 负责发送。
2. hwh 把“执行请求”和“执行成功”明确区分，并在发送后要求新增气泡核对；这是四项目中最接近 receipt-first execution 的个人微信实现。
3. WeCom 项目把 account、source、session、peer 和 capability 放入运行时边界，已经具备组织级主体归属和多入口再耦合的形态。
4. SightFlow 当前最值得保留的是 BaseDriver / VisionAgent / Scanner 这一级抽象；实际代码仍有多个占位实现，现阶段不应把它当作可靠执行基线。
5. 因此 SightFlow 下一步应以“统一接口 + 真实 Adapter + receipt + replay test”建设，吸收 hwh 的可靠性和 colorsbear 的输入解耦，同时吸收 WeCom 的 source/account/capability attribution。

## 2. 统一六层映射

### L0 环境与身份

hwh：
- wechat_bot/adaptation.py 定义 ProbeReport、LayoutProfile、环境指纹、DPI、虚拟桌面、微信版本和支持矩阵。
- 兼容档案与实际运行环境绑定。

colorsbear：
- UIA 通过微信主窗口 class、AutomationId、focused control 识别运行环境。
- wxmini2.py 使用 Qt51514QWindowIcon、session_list、chat_message_list 等稳定 UI 标识。

SightFlow：
- BaseDriver 只保存 window_handle、chat_region、input_region。
- WeChatDriver 通过窗口标题“微信”查找窗口，身份建模较弱。

WeCom：
- channel.ts 和 runtime/source-registry.ts 以 accountId、source、sessionKey、sessionId、peerKind、peerId 等建立来源归属。

判断：
L0 是四项目差异最大的地方。WeCom 已达到组织级 source/account attribution；hwh 达到较强的设备/环境 identity；colorsbear 偏应用窗口 identity；SightFlow 仍是简单 window abstraction。

### L1 输入

hwh：
- watcher.py 使用完整虚拟桌面/PrintWindow 截图。
- OCR 解析会话列表和聊天气泡。
- 支持负坐标、多屏、DPI。

colorsbear：
- wxmini2.py 直接使用 UIA 树读取 session_list/chat_message_list。
- wxbot_weflow.py 接入本地 WeFlow HTTP API，可读 sessions/messages/SSE。
- wxbot_send.py 将发送保持在 UIA 通道。
- 形成明确的双平面输入/执行设计。

SightFlow：
- scanner.py 提供 screenshot + OCR + template/颜色检测。
- 目前 detect_chat_list() 返回固定的 Chat 1。
- detect_input_field() 主要返回固定的底部区域。
- WeChatDriver 默认区域硬编码。

WeCom：
- monitor.ts 接收 webhook。
- source-registry.ts 记录消息来源和会话/peer 关联。
- channel.ts 将 gateway、transport、account 管理接入 OpenClaw。

判断：
colorsbear 最接近“输入与执行解耦”；WeCom 最接近“输入事件标准化”；hwh 最接近“视觉输入工程化”；SightFlow 当前只具备抽象接口。

## 3. L2 感知与消息语义化

### hwh

watcher.py：
- read_watch_rows() 对联系人、预览、时间和红点分别解析。
- read_chat_bubbles() 解析 sender side、OCR text、bubble region。
- _bubble_side() 结合气泡颜色与 x 位置，颜色不能可靠判断时存在未知态。
- monitor.py 使用气泡历史做增量 diff，并对 OCR 噪声提供 SequenceMatcher 容错。

这是较成熟的“感知 → 语义事件”层。

### colorsbear

wxmini2.py：
- ListItemControl 是消息/会话的结构载体。
- message kind 通过 Name 内容推断。
- side 通过截图颜色和空间位置判断。

优势：
- UIA 直接给出消息对象和 BoundingRectangle。
- 消息读取比纯 OCR 更结构化。

局限：
- side 仍依赖截图像素分析。
- 多媒体与非文本消息依然需要额外解释。

### SightFlow

agent.py：
- Message 只有 sender、text、timestamp、is_unread、raw_data。
- unread notification 只有 app/contact/count/position。

scanner.py：
- detect_unread_dots 有模板/红色颜色 fallback。
- chat list/input field 的真实检测仍属占位。

判断：
数据类型设计可以继承，感知实现需要重做。

### WeCom

source-registry.ts：
- messageId、sessionKey、sessionId、peerKind、peerId、upstreamCorpId 都可以进入 source snapshot。
- 显式记录 account scope。

这已经具备比视觉项目更强的 event identity。

## 4. L3 主体、上下文与决策

### hwh

state.py：
- memory、seen_bubbles、last_sent、last_preview、handled、reply_times 全部持久化。
- memory 与去重游标分开。

llm.py：
- system guardrails + persona + recent memory 形成 LLM 输入。
- LLM 失败返回空值，monitor.py 把空回复视为失败。

monitor.py：
- quiet hours、sensitive、rate limit、risk placeholder 在 LLM 之前执行。
- 风险消息可直接人工处理。

优势：
决策前置 guard 比较清晰。

缺口：
主体模型仍接近“个人微信账号 + contact”；项目/任务/workorder 等更高层对象尚未抽象。

### colorsbear

wxbot_memory.py：
- 每个 conversation workspace 包含 MEMORY.md、daily memory、files、notes。
- memory_inject() 将长期记忆和近两天笔记注入 system。
- should_extract() 按回复轮次触发记忆提取。

wxbot_context.py：
- 支持 token/percentage budget。
- 旧消息截断 → 丢弃最旧消息。
- system cache 对 persona/memory/model 等变化失效。

wxbot.py：
- reply policy、personas、behavior probabilities、memory、context compression、search、file、sticker 等统一进入机器人主循环。

优势：
这是四项目中最完整的“对话主体上下文”。

缺口：
长期记忆主要服务于聊天 persona，并未形成独立 subject/project/task semantic layer。

### SightFlow

agent.py：
- _generate_reply 支持 keyword/ai/smart 三种模式。
- _ai_reply 当前为 TODO，直接返回 None。
- 因此 LLM 决策实际没有接通。

这是当前最大的成熟度瓶颈。

### WeCom

source-registry + dynamic routing/capability：
- source plane 可区分 bot-ws 与 agent-callback。
- 工具注册时用 source registry 判断当前工具是否应该暴露。
- capability 可以依据当前 channel/source context 动态出现。

这是明显更接近“决策上下文决定可用 capability”的实现。

## 5. L4 执行

### hwh

keys + watcher + monitor：
- 环境探测
- 焦点检查
- UI 操作节流
- 发送
- 回执确认
- 环境不确定时 safe stop

monitor.py 的执行链明确写成：
护栏 → LLM → 发送 → 气泡核对。

### colorsbear

wxmini2.py：
- 自定义 UIA walking。
- 搜索联系人。
- 输入、粘贴、Enter。
- 发送前后 clipboard verification。

wxbot_send.py：
- 微信 4.1.x 的输入防御环境下，将导航与输入拆开。
- 导航使用 pyautogui。
- 输入使用 UIA 原生 SendKeys。
- 每一步调用 _is_wechat_alive()。

这是非常有价值的“不同 action 使用不同 execution channel”设计。

### SightFlow

WeChatDriver：
- type_message 使用 pyautogui.write。
- send 使用 Enter。
- open_chat 搜索后直接选择第一个结果。
- get_chat_list / click_unread / unread count 均为 TODO。

因此当前执行层只能视为 prototype。

### WeCom

channel.ts/outbound/transport：
- Bot WS 与 Agent callback 是正式 transport。
- tool capability 直接调用企业微信 API。
- doc/calendar 有独立 capability client/tool/schema。

它的 execution boundary 最清晰。

## 6. L5 结果确认 / receipt

| 项目 | 本地动作确认 | UI/app receipt | 业务 receipt |
|---|---:|---:|---:|
| hwh | 3 | 3/4 | 0 |
| colorsbear | 3/4 | 3 | 0/1 |
| SightFlow | 1 | 0 | 0 |
| WeCom | 4 | 4 | 视具体 capability |

hwh：
monitor.py 明确要求发送后读取新增气泡；若动作执行但无法核对，返回 verification_error 并安全停机。

colorsbear：
wxmini2.py 的 paste_verified() 对 clipboard write 和输入框 readback 做实际核对；send chain 仍主要围绕客户端操作成功。

WeCom：
API/tool result 有结构化 ok/action/raw result，但“API success”与业务对象真正生效仍需按具体 API 单独实验。

## 7. 失败治理

### hwh：最强

- EnvironmentProbe
- calibration_required
- sensitive keyword
- risk placeholders
- UI rate limiting
- circuit breaker
- safe stop
- duplicate suppression
- OCR alignment fallback
- lock-screen detection

尤其值得移植：
“无法确认 → 停止”这一行为约束。

### colorsbear：强

- LLM fallback
- global backoff
- no-message-loss
- UIA self-healing
- clipboard verification
- per-conversation memory
- context budget
- multi-capability fallback

值得移植：
“输入平面与执行平面可独立退化”。

### SightFlow：弱

try/except 存在，但没有形成完整状态机。
此外 agent.py 中 auto_reply() 是同步函数，却调用 asyncio.sleep(interval) 而没有 await，当前实现不会产生预期的异步等待。

### WeCom：系统级

- account conflict
- source attribution
- operational events
- transport state
- health/connection/authentication status
- 多账号隔离
- capability source gating

其治理对象已经超过单机器人。

## 8. provisional 评分

评分含义：
0 无；1 概念；2 基础实现；3 可运行且有边界保护；4 有系统级验证/治理证据。

| 维度 | hwh | colorsbear | SightFlow | WeCom |
|---|---:|---:|---:|---:|
| 输入可靠性 | 3 | 4 | 1 | 4 |
| 消息语义化 | 3 | 3 | 1 | 4 |
| subject/session attribution | 2 | 3 | 1 | 4 |
| context/memory | 3 | 4 | 0 | 3 |
| decision/policy separation | 3 | 3 | 1 | 4 |
| execution abstraction | 3 | 4 | 3 | 4 |
| target validation | 3 | 3 | 1 | 4 |
| action receipt | 4 | 3 | 1 | 4 |
| business receipt | 0 | 0 | 0 | 2 |
| duplicate/idempotency | 4 | 4 | 0 | 3 |
| retry/backoff | 3 | 4 | 1 | 4 |
| safe stop | 4 | 3 | 1 | 4 |
| human takeover | 3 | 2 | 0 | 3 |
| multimodal capability | 2 | 4 | 1 | 4 |
| capability composition | 2 | 3 | 2 | 4 |
| multi-account isolation | 1 | 1 | 0 | 4 |
| observability/audit | 3 | 3 | 2 | 4 |
| replay/testability | 3 | 2 | 1 | 3 |
| version portability | 3 | 2 | 2 | 4 |
| architecture reusability | 3 | 4 | 3 | 4 |

这些评分是代码证据驱动的 provisional rating，不代表实际运行质量。下一阶段实验必须重新 adjudicate。

## 9. 最值得抽取的共同结构

建议 SightFlow 将最小执行协议定义为：

InputEvent
- source
- account
- session
- peer
- message
- timestamp
- raw/evidence

PerceptionResult
- recognized object
- confidence
- evidence
- unresolved fields

Decision
- action
- target
- reason/policy
- authorization
- expiry/idempotency key

Action
- executor
- parameters
- preconditions
- started_at
- finished_at

Receipt
- action_status
- application_status
- business_status
- evidence
- error_category

State
- cursor
- memory
- pending action
- last receipt

这套结构可以同时容纳：
- OCR
- UIA
- WeFlow
- WeCom API
- future VLM
- other desktop apps

## 10. 对 SightFlow 的直接改造建议

优先级 P0：

1. 保留 BaseDriver，但将 open_chat / read_messages / send_message / verify_action 从简单函数升级成 typed interface。
2. 引入 Source / Account / Session / Peer 四级 identity。
3. 把 ScreenScanner 从“返回位置”升级成“带 evidence + confidence 的 perception result”。
4. 将 LLM decision 与 driver execution 分离。
5. 引入 Receipt 对象，并强制所有 send/tool action 返回 receipt。
6. 加入 deterministic replay fixture。

P1：

1. 把 hwh 的环境探测/校准模式引入 desktop driver。
2. 把 colorsbear 的 WeFlow read-plane 作为可选 adapter。
3. 加入 context/memory provider。
4. 引入 capability registry。
5. 支持多个 executor：
   - VisualExecutor
   - UIAExecutor
   - APIExecutor

P2：

1. 把 Workflow 从 YAML placeholder 变为 typed task/flow definition。
2. 引入 capability × target × policy 的组合规则。
3. 增加 business receipt。
4. 建立微信/企业微信实验集。

## 11. 当前 Adopt 判断

hwh0825/wechat-auto-reply：
ADOPT_BOUNDED
- 适合作为个人微信 4.x execution/reliability reference。

colorsbear/wxbot-auto-reply：
ADOPT_BOUNDED / HIGH-VALUE REFERENCE
- 适合作为 input-plane decoupling、memory、multimodal capability reference。

deepdadou/sightflow-agent：
REFERENCE + BUILD TARGET
- 当前代码适合作为抽象骨架。
- 需要重新实现核心 perception/execution/receipt。

lineCode/wecom-bot：
ADOPT_BOUNDED / ARCHITECTURE REFERENCE
- 适合作为组织级 source/account/capability/routing reference。
- 它属于企业微信 API 体系，不能直接作为个人微信 4.x UI executor。

## 12. 下一阶段实验顺序

G0：四仓库代码快照与符号索引完成
G1：统一 capability map
G2：SightFlow typed interface
G3：WeChat Visual Adapter
G4：WeChat UIA Adapter
G5：WeFlow Read Adapter
G6：WeCom API Adapter
G7：Receipt + replay
G8：End-to-end flow

最终实验目标：

同一个业务需求：

“收到微信消息 → 识别主体 → 判断是否回应 → 生成回复 → 发送 → 证明发送成功 → 更新状态”

能够使用不同输入/执行实现运行：

VisualInput + VisualExecutor
UIAInput + UIAExecutor
WeFlowInput + UIAExecutor
WeComInput + WeComExecutor

上层 Decision / Flow / Receipt contract 保持一致。

这将直接验证“解耦输入与执行，再通过统一 flow/IPOF 再耦合”的工程可行性。
