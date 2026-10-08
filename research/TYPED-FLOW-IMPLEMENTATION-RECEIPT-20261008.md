# Typed Flow Re-coupling — Implementation Receipt (2026-10-08)

## Scope and status

- Branch: research/typed-flow-recoupling-20261008
- Baseline: main at 33e616648e64e2f1ad82d70fb4620096f3468d5e
- Status: CODE SUBMITTED / FIXTURE TESTS NOT YET EXECUTED / REAL WECHAT NOT CONNECTED
- Scope: typed domain contract + bounded single-event flow + six fixture test cases

## Implemented

- src/sightflow_agent/contracts.py
  - SourceIdentity, InputEvent, PerceptionResult, Decision, Action, Receipt.
  - Status distinguishes local confirmation, application confirmation, business confirmation.
- src/sightflow_agent/flow.py
  - injectable perception, policy, executor, receipt store.
  - identity matching, confidence gate, owner authorization callback and idempotency check.
  - uncertain/failed application receipt blocks success claim.
- tests/test_flow_contract.py
  - happy path + duplicate, denied authorization, unresolved perception, cross-source mismatch, skip and unknown application receipt.

## Current boundaries and known limitations

1. The in-memory Store in tests only verifies basic re-entry; production requires a transactional durable claim-before-send journal. An abrupt crash between physical send and receipt persistence is presently unsafe. Do not deploy the prototype against real accounts.
2. Authorization callback defaults to deny. No authority or policy engine is embedded.
3. Confidence is adapter-provided; it is not calibrated by an independent benchmark.
4. The action executor is entirely injected. Current code has no actual WeChat/WeCom I/O integration.
5. Business receipt remains UNKNOWN without an independent downstream confirmation.
6. Tests are authored but not yet executed through an attached CI runner.
7. Existing VisionAgent and WeChatDriver are deliberately unchanged, preserving the upstream project and separating research candidate from production behavior.

## Immediate next work

- G1: run tests and CI, inspect all six fixtures and augment unsafe-abort/exception tests.
- G2: introduce claim-before-send journal with PENDING/IN_FLIGHT/UNKNOWN/CONFIRMED and manual reconciliation on ambiguous outcomes.
- G3: add read-only visual and UIA adapters, measure entity identity and message detection errors.
- G4: add dry-run execution adapter with observable receipt, no real messaging.
- G5: experimental WeFlow read and WeCom authenticated adapters under separate permissions and source attribution.
- G6: supervised sandbox manual-send experiment after explicit owner approval.

## External research evidence

- https://github.com/hwh0825/wechat-auto-reply/blob/main/wechat_bot/monitor.py
- https://github.com/hwh0825/wechat-auto-reply/blob/main/wechat_bot/watcher.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxbot_weflow.py
- https://github.com/colorsbear/wxbot-auto-reply/blob/master/wxmini2.py
- https://github.com/lineCode/wecom-bot/blob/main/src/runtime/source-registry.ts
- https://github.com/deepdadou/sightflow-agent/blob/main/src/sightflow_agent/agent.py

## Adoption boundary

This is a research implementation candidate. The architecture is deliberately nested/compositional: a source event carries its context, decision/action belong to the corresponding accountable source identity, and receipts may feed subsequent IPOF iterations. The module does not impose a single linear global workflow across business/project/task hierarchies.
