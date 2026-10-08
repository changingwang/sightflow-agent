# External module reuse and adoption audit — 2026-10-08

Status: CODE REVIEW COMPLETE / IMPORT NOT AUTHORIZED / NO RUNTIME TEST
Scope: hwh0825/wechat-auto-reply, colorsbear/wxbot-auto-reply, deepdadou/sightflow-agent, lineCode/wecom-bot.

## Reuse classification

| Source + symbol/module | Reuse level | Reason / dependencies | Required action |
|---|---|---|---|
| deepdadou/sightflow-agent: src/sightflow_agent/drivers/base.py BaseDriver | ALREADY IN FORK | Existing portable abstract driver base, pyautogui dependencies limited to concrete commands | Retain, add typed receipt-bearing execution contract via adapter rather than destructive rewrite |
| deepdadou: scanner.py ScreenScanner | ADAPT | Screenshot API works as initial abstraction; unread red-dot fallback imports scipy.ndimage but scipy absent in base pyproject dependencies; chat list contains placeholder | Add missing dependency or replace detector; build fixtures, remove placeholder |
| deepdadou: ocr.py OCR | ADAPT | Pluggable OCR engines and optional dependencies | Validate engine initialization/version compatibility; calibrate confidence |
| deepdadou: agent.py VisionAgent | REFERENCE ONLY for production | _ai_reply returns None; sync auto_reply calls asyncio.sleep without await; lack durable send receipt | Preserve legacy API but route new experiments to journal_flow |
| hwh0825: wechat_bot/adaptation.py LayoutProfile, EnvironmentProbe | PORT SELECTIVELY | Windows/DPI/virtual screen calibration designed for WeChat 4.x; imports PIL and local project config/version | Isolate pure geometry and calibration model, avoid cross-importing entire application |
| hwh0825: watcher.py CaptureBackend / bubble-side detection | PORT SELECTIVELY | Strong Windows-specific screen/PrintWindow implementation, dependencies pywin32/Pillow/OCR; no portable interface | Implement WindowsVisualInputAdapter behind pure InputEvent/PerceptionResult contract |
| hwh0825: monitor.py bubble diff helpers | ADAPT | OCR alignment and stale frame handling are reusable logic | Copy only with source/license review; build known-frame fixtures |
| hwh0825: keys.py send confirmation flow | PORT SELECTIVELY | Valuable focus/contact verification/receipt logic; Windows pywin32 & config-specific | Wrap as DesktopExecutor; do not send until source identity and full target verification implemented |
| colorsbear: wxmini2.py list_sessions/read_chat | ADAPT | Concrete Windows UIA reader, wxauto4.uia and ctypes, version-sensitive control IDs | Optional WindowsUIAInputAdapter, exact WeChat 4.x version gate |
| colorsbear: wxbot_weflow.py WeFlowClient | DIRECT-USE CANDIDATE (optional) | Small HTTP read-only client; depends on separate locally installed WeFlow server/token | Adapter normalizes message IDs into InputEvent; verify legal access, auth and provenance; no repo-level dependency until tested |
| colorsbear: wxbot_context.py | DIRECT-USE CANDIDATE (pure helper) | Context budget, trimming and input caching utilities, lightweight Python | Import selected pure functions with tests and copyright/license confirmation |
| colorsbear: wxbot_memory.py | ADAPT | Conversation-specific workspace, extraction and prompt injection coupled to project directories/config | Extract memory provider interface; control data retention and prompt injection |
| colorsbear: wxbot_send.py | REFERENCE ONLY initially | UIA + clipboard + process/window focus behavior tuned to specific WeChat 4.1.x, side effects possible | Port safety strategy, not whole file |
| lineCode: src/runtime/source-registry.ts | PORT DESIGN (cross-language) | Account/source/session/peer binding, TypeScript | Implement Python analogue for personal IM; WeCom plugin uses native one |
| lineCode: src/channel.ts, index.ts | DIRECT USE ONLY AS STANDALONE OPENCLAW PLUGIN | OpenClaw-specific ChannelPlugin/SDK | Keep as separate managed provider, no source copy into Python core |
| lineCode: src/capability/doc/tool.ts, calendar/tool.ts | DIRECT USE ONLY IN WECOM OPENCLAW ENVIRONMENT | Enterprise WeCom API credentials and source gate; TypeScript + OpenClaw | Integrate at tool/capability interface via gateway, not embedded Python |
| lineCode: transport/ | STANDALONE PROVIDER | WS/Webhook/HTTP encrypted media transport, account/credential requirements | Treat as authoritative WeCom provider behind channel adapter |

## Source evidence

- https://github.com/deepdadou/sightflow-agent/blob/main/src/sightflow_agent/drivers/base.py
- https://github.com/deepdadou/sightflow-agent/blob/main/src/sightflow_agent/agent.py
- https://github.com/deepdadou/sightflow-agent/blob/main/src/sightflow_agent/scanner.py
- https://github.com/hwh0825/wechat-auto-reply/blob/main/wechat_bot/adaptation.py
- https://github.com/hwh0825/wechat-auto-reply/blob/main/wechat_bot/watcher.py
- https://github.com/hwh0825/wechat-auto-reply/blob/main/wechat_bot/monitor.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxmini2.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxbot_weflow.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxbot_context.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxbot_memory.py
- https://github.com/lineCode/wecom-bot/blob/main/index.ts
- https://github.com/lineCode/wecom-bot/blob/main/src/channel.ts
- https://github.com/lineCode/wecom-bot/blob/main/src/runtime/source-registry.ts

## Licenses / provenance

- deepdadou/sightflow-agent has MIT LICENSE and pyproject license declaration; existing fork inherits source obligations.
- lineCode/wecom-bot has ISC LICENSE and ISC package.json.
- hwh0825 and colorsbear license text was not independently fetched from LICENSE or LICENSE.md in this review. README/manifest alone is not proof of grant. Treat direct source copying as HOLD_PENDING_LICENSE_VERIFICATION. Architectural learning and separate reimplementation are possible.
- Third-party transitive SDK/client package licenses must be checked independently.

## Journal design now implemented

- SQLiteActionJournal reserve() atomically inserts unique action key in a durable transaction before side effect.
- mark_in_flight() durably transitions PENDING → IN_FLIGHT before executor.
- complete() stores receipt and sets CONFIRMED, FAILED, or UNKNOWN.
- recover() moves abandoned PENDING or IN_FLIGHT to UNKNOWN.
- Duplicate key, including UNKNOWN, is never auto-retried.
- journal_flow.process_once_journal applies perception, source identity, authorization, unique key, executor, receipt.

### Operational controls not yet met

- Must call recover() on startup BEFORE processing any event. Integration into existing legacy VisionAgent has intentionally not happened.
- Single journal writer/process ownership (instance lock) remains a gate. A concurrent startup recover() could prematurely convert an active IN_FLIGHT record to UNKNOWN, so do not run multiple producers over the same journal.
- No automatic UNKNOWN reconciliation. User must inspect actual app state and explicitly authorize any compensating action under a new action ID.
- Even application-confirmed receipts cannot prove receiver delivery.
- ReceiptStore from the first research prototype is in-memory, intentionally distinct from journal-backed production candidate.
- Test fixtures are written but not executed. Do not claim PASS.
- Live WeChat or WeCom action remains DISABLED and not authorized.

## Next bounded gate

1. Run tests locally: python -m unittest discover -s tests -v (with project import installed via pip install -e .).
2. Add single-instance runtime ownership and startup recovery integration.
3. Finish license provenance check before copying hwh/colorsbear source.
4. Build fixture-backed read-only adapters first: VisualInput then UIAInput/WeFlowInput.
5. Add no-send dry-run executor and identity/focus target validation; only then propose supervised live tests.

Decision: adopt interfaces first, proven pure utilities second, controlled drivers third, enterprise channel via provider boundary.
