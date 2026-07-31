# Typed IR/Runtime Branch Recovery v1

## Alias confirmation

`gate/assisted-project-roundtrip-v1` and `gate/typed-ir-runtime-v1` both resolve to `26065edc870710b747bf9f4ac243f35180dfdd0c`; their direct diff is empty.

`TYPED_IR_RUNTIME_BRANCH_IS_ALIAS=yes`

## Investigation record

| Surface | Result |
|---|---|
| Local and remote reachable commits | No commit subject or changed path matched Typed IR, Runtime Echo, capability runtime, `result_token`, `command_id`, or `submit_result`. |
| Reflogs | The typed branch was created directly from `26065ed` at `2026-07-28 14:07:38 +0000`; no later candidate commit, reset target, or detached work is recorded. |
| Worktrees | Five worktrees inspected: main, canonicalization, XML hardening, roundtrip, and runtime alias. All were clean. The runtime worktree is at `26065ed`. |
| Stashes | None. |
| Unreachable Git objects | `git fsck --full --no-reflogs --unreachable --lost-found` emitted no objects. |
| Scoped filesystem search | No matching checkout, evidence, or source was found below `/home/ubuntu/code`, `/home/ubuntu/.codex`, `/home/ubuntu/.hermes`, `/home/ubuntu/evidence`, or `/tmp`, excluding Git internals and caches. |

No candidate meets the required recovery categories (Typed IR/schema, renderer integration, IR tests, Runtime Echo candidate, runtime execution evidence, and closure documentation). No recovery branch was created and the alias branch was not moved.

`TYPED_IR_RUNTIME_BRANCH_RECOVERY_V1=NOT_FOUND`  
`TYPED_IR_RUNTIME_WORK=NOT_RECOVERED`
