# 微信 / 企业微信 AI Agent 周边研究方案
## WECHAT-AGENT-RESEARCH-PLAN-v0.1
日期：2026-10-08
研究仓库：changingwang/sightflow-agent
研究对象：hwh0825/wechat-auto-reply、colorsbear/wxbot-auto-reply、deepdadou/sightflow-agent、lineCode/wecom-bot

## 1. 研究目标

本研究围绕一条统一的端到端链路展开：

输入层 → 感知/消息抽取 → 主体上下文 → 认知 → 决策 → 执行 → 结果确认 → 状态/记忆 → 输出

核心问题是：微信及微信周边开源项目，如何把外部消息、视觉/协议输入、主体状态、AI 认知、动作决策、工具执行和结果回执组合成可运行系统；哪些机制可以抽取为通用的 deAgent / IPOF 再耦合基础设施。

研究重点同时覆盖两条技术路线：
- 视觉/桌面自动化：面向个人微信 4.x
- API/协议/企业协作：面向企业微信及组织级 Agent

研究最终要形成：
1. 微信 AI Agent 的统一能力地图；
2. 四个代表项目的代码级结构图；
3. 可迁移的输入/认知/决策/执行/输出接口；
4. 可复用的可靠性与治理模式；
5. SightFlow 后续实验与 prototype 的实施清单。

## 2. 统一分析模型

### 2.1 六层端到端模型

L0 环境与身份
- OS / 微信版本 / 企业 / account / session / contact / group
- 窗口、DPI、屏幕、权限、认证

L1 输入
- 屏幕截图
- OCR / VLM
- UIA / accessibility tree
- WebSocket / Webhook / API
- 本地 DB / 事件流
- 用户直接输入

L2 感知与语义化
- 未读检测
- 会话定位
- 消息解析
- 消息类型识别
- 发送方识别
- 时间/联系人/群等上下文恢复

L3 主体认知与决策
- 历史上下文
- 长短期记忆
- 人设/角色
- 权限与护栏
- LLM / VLM 推理
- reply / skip / escalate / tool-call
- 多 Agent / account / session 路由

L4 执行
- UI 点击
- 输入/粘贴
- 键盘
- API 调用
- Bot WS
- Agent callback
- 文件/图片/媒体发送
- 企业协作能力调用

L5 结果与输出
- 新气泡出现
- 状态更新
- 回执
- 日志
- 运行状态
- 记忆沉淀
- 对外输出
- 失败/人工接管

### 2.2 IPOF 视角

将上述链路归一到：
- I：外部消息、屏幕状态、会话状态、工具返回结果
- P：认知、判断、选择、策略组合
- O：状态变化、动作请求、执行结果
- F：确认、失败、重试、回执、记忆与下一次输入

重点区分：
- 感知结果与决策结果
- 决策结果与执行结果
- 执行请求与执行成功
- 执行成功与业务结果成立

## 3. 研究问题

### R1 输入层
不同项目从哪里获得“新消息”：
- UI screenshot
- OCR
- VLM
- UIA tree
- DB/API
- webhook / WS

需要记录：
- latency
- fidelity
- version dependency
- privacy exposure
- failure mode
- replayability

### R2 感知层
如何把原始输入变成：
- contact
- peer
- message
- sender
- timestamp
- message kind
- unread
- conversation state

重点检查：
- 是否允许模糊匹配
- 是否存在“猜联系人”
- 是否有 stable identifiers
- OCR 噪声如何处理
- 多媒体如何表示

### R3 主体与状态
研究每个项目怎样保存：
- conversation memory
- state cursor
- owner / user identity
- account identity
- session identity
- persona
- permission
- cooldown / rate limits

分析是否存在明确的 subject attribution。

### R4 决策
识别：
- LLM 是否直接控制执行
- 是否存在 policy / guard 层
- 是否支持 skip / human handoff
- 是否具备风险动作分级
- 是否存在多入口路由

### R5 执行
比较：
- UIA / pyautogui / SendInput
- API / SDK / webhook
- clipboard injection
- media upload
- document/calendar tools

重点考察：
- action precondition
- focus validation
- target validation
- timeout
- retry
- idempotency
- receipt

### R6 结果确认
定义三种确认：
1. local action confirmation：动作执行成功；
2. UI/application receipt：客户端出现预期状态；
3. business receipt：业务结果真正成立。

记录项目实际做到哪一级。

### R7 失败治理
研究：
- stop-safe
- circuit breaker
- retry/backoff
- duplicate suppression
- stale frame prevention
- environment calibration
- human takeover
- degradation

## 4. 四项目代码级审查范围

### A. hwh0825/wechat-auto-reply

重点文件：
- wechat_bot/adaptation.py
- wechat_bot/watcher.py
- wechat_bot/monitor.py
- wechat_bot/guard.py
- wechat_bot/state.py
- wechat_bot/llm.py
- main.py

重点验证：
- 微信 4.x 兼容/校准
- 屏幕外窗口截图
- OCR 消息差分
- sender side classification
- 状态游标
- 风险拦截
- 发送后气泡核对
- 多人模式联系人验证边界

### B. colorsbear/wxbot-auto-reply

重点文件：
- wxmini2.py
- wxbot.py
- wxbot_memory.py
- wxbot_context.py
- wxbot_files.py
- wxbot_search.py
- wxbot_weflow.py
- wxbot_send.py

重点验证：
- UIA 消息读写
- WeFlow 读消息与 UIA 发消息的双平面架构
- 会话/消息/能力分发
- memory workspace
- context compression
- multimodal/file capabilities
- send verification
- fallback/recovery

### C. deepdadou/sightflow-agent

重点文件：
- src/sightflow_agent/agent.py
- src/sightflow_agent/scanner.py
- src/sightflow_agent/ocr.py
- src/sightflow_agent/drivers/base.py
- src/sightflow_agent/drivers/wechat.py
- src/sightflow_agent/cli.py
- src/sightflow_agent/workflows/

重点验证：
- 是否已经实现通用 IM driver abstraction
- vision scanner 是否真实可运行
- workflow 与 tool boundary
- Agent 与执行驱动之间的耦合方式
- 测试/回执/错误处理成熟度

### D. lineCode/wecom-bot

重点文件：
- index.ts
- src/channel.ts
- src/monitor.ts
- src/runtime.ts
- src/runtime/source-registry.ts
- src/capability/mcp/index.ts
- src/capability/doc/tool.ts
- src/capability/calendar/tool.ts
- transport / gateway / config 目录

重点验证：
- Bot WS / Agent callback 双入口
- account/session/source attribution
- dynamic routing
- capability registration
- docs/calendar/MCP 工具
- runtime health / audit events
- organization-level subject and capability boundaries

## 5. 统一比较矩阵

每个项目按 0-4 级评分：
0 = 无
1 = 概念/占位
2 = 基础实现
3 = 可运行且有边界保护
4 = 有系统级验证/治理证据

维度：
1. 输入可靠性
2. 消息语义化
3. subject/session attribution
4. context/memory
5. decision/policy separation
6. execution abstraction
7. target validation
8. action receipt
9. business receipt
10. duplicate/idempotency
11. retry/backoff
12. safe stop
13. human takeover
14. multimodal capability
15. tool/capability composition
16. multi-account/multi-session isolation
17. observability/audit
18. testability/replayability
19. version portability
20. architecture reusability

评分必须对应：
- repository
- exact file
- symbol/function/class
- code evidence
- inference
- confidence

## 6. 重点实验

### E1 消息输入实验
同一条消息分别从：
- screenshot/OCR
- UIA
- WeFlow/API
获取，比较内容完整性和延迟。

### E2 新消息去重实验
连续测试：
- 相同文本
- OCR 微小变化
- 多帧重复
- 历史消息回滚
测试错误触发率。

### E3 联系人安全实验
制造：
- 同名联系人
- 搜索第一结果错误
- 标题 OCR 失败
- UI 焦点丢失
验证是否会误发。

### E4 发送回执实验
区分：
- API call returned
- input box contained text
- Enter executed
- sent bubble appeared
- target peer visible

### E5 LLM 故障实验
模拟：
- empty response
- timeout
- HTTP error
- malformed response
测试：
- retry
- duplicate suppression
- safe stop
- backlog recovery

### E6 状态恢复实验
重启应用/微信后测试：
- message cursor
- memory
- conversation identity
- pending action
是否可恢复。

### E7 能力再耦合实验
定义统一能力：
read_message
identify_peer
decide_reply
send_text
send_media
create_document
create_schedule

分别从视觉、UIA、WeCom API 映射到统一 interface。

## 7. 研究产出

本研究至少产出：

1. WECHAT-AGENT-RESEARCH-PLAN-v0.1.md
2. WECHAT-AGENT-CODE-COMPARISON-20261008.md
3. WECHAT-AGENT-CAPABILITY-MAP-20261008.md
4. WECHAT-AGENT-RECOUPLING-GRAMMAR-EXPERIMENT-v0.1.md
5. 实验记录与 receipts
6. SightFlow 改进 issue / implementation backlog

## 8. 判定原则

研究中严格区分：
- README claim
- code evidence
- runtime evidence
- benchmark evidence
- inference

安全性只能在有测试或运行证据时给出高等级结论。

“纯视觉”“无协议”“官方 API”等属于输入/执行机制描述，不直接等价于安全、稳定、合规或可生产。

## 9. 与 deAgent 的连接

研究最终将回答：

1. 微信消息能否成为 deAgent 的外部 I/O；
2. 消息读取、认知、决策、执行能否拆成独立 IPOf 单元；
3. 能力、目标、成果能否通过统一 flow 跨系统流动；
4. 视觉执行器、UIA 执行器、WeCom API 执行器能否成为同一 T2 interface 的不同 implementation；
5. 哪些状态应归主体、项目、任务、WorkOrder、Session；
6. 哪些能力应沉淀到 KAS / capability registry；
7. 如何建立“执行成功”与“业务结果成立”的两级以上回执体系。

## 10. 阶段门

G0 FACT VERIFIED
- 代码路径和符号定位完成
- README claim 与 code evidence 分离

G1 STRUCTURE MAPPED
- 四个项目映射到六层模型

G2 FAILURE SURFACE MAPPED
- 每个项目至少识别 5 个关键失败模式

G3 COMMON INTERFACE CANDIDATE
- 形成最小统一输入/决策/执行/receipt interface

G4 EXPERIMENT READY
- SightFlow 可以按统一实验协议运行

G5 RECOUPLING CANDIDATE
- 将能力、目标、成果及消息/工具执行映射到 flow + IPOF

G6 ADOPTION DECISION
- 形成 Adopt / Adopt Bounded / Reference Only / Reject 四级结论
