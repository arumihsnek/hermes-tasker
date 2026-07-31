# Runtime Echo Android integration contract v1

## Tasker handoff

The immutable handoff consists of the Runtime Echo spec, normalized IR, candidate XML, manifest, and their SHA-256 values.  The request is structured JSON with `run_id`, `capability`, `command_id`, `result_token`, `payload`, candidate hash, and manifest hash.  The expected terminal result repeats capability, command ID, token, and payload exactly with `status: success`.

`hermes-tasker` creates and verifies this package only.  It neither contacts a device nor interprets a visual notification as a result.

## Hermes Bridge responsibility

Hermes Bridge must transport a run-ID-named immutable package to device-accessible storage, verify candidate and manifest hashes before and after transfer, guide the required Tasker import/selection, invoke the Task, collect structured accepted/progress/terminal events, and return safe portable evidence.  It must reject duplicate, stale-run, wrong-token, wrong-command, wrong-payload, timeout, and failure outcomes.

The response must include candidate received/imported/available state, execution state, correlation IDs, payload, status, timestamps, structured errors, candidate/manifest hashes, device and Tasker versions, and minimal redacted logs.  Re-export is collected when the import path permits it; its comparison verdict remains separate from runtime success.

## Human boundary

If Tasker requires an import or security confirmation, Bridge prepares the immutable evidence bundle and pauses at that exact UI action.  A human performs only the required confirmation.  The same run ID and hashes are then retained for execution and result capture.  No security UI is bypassed.

## Versioned Android gap

At Android base `7b503d850d47d4827fc942114d147edb83258010`, Hermes Bridge provides transport primitives but no versioned Tasker candidate import/run/result correlation contract.  `ANDROID_CHANGES_REQUIRED=yes`.  Local uncommitted Tasker-result-channel observations are excluded from this conclusion.

Any implementation must live in the dedicated isolated Android worktree created from that committed base, use Hermes Bridge rather than a second transport architecture, and keep Typed Spec/IR and XML rendering in `hermes-tasker`.
