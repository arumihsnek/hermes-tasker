# Typed IR / Runtime Echo audit v1

## Scope and provenance

This audit is based on Tasker commit `820676e3d52b68bb35cdf9ea1305118f3ca03734` and the Android committed base `7b503d850d47d4827fc942114d147edb83258010`.  The Android checkout was inspected read-only.  Its local modifications are not an API source and are not used by this design.

The historical recovery report is decisive: `gate/typed-ir-runtime-v1` is an alias of the Project-roundtrip branch at `26065ed`; no prior Typed IR or Runtime Echo implementation was recovered.

## Renderer and static pipeline

1. **Public renderer entrypoint.** `scripts/generate_tasker_artifact.py` is the public CLI: `--request <json>` and `--output-dir <dir>`.  Its in-process entry is `main()`, which dispatches to `render_task`, `render_profile`, or `render_project`.
2. **Untyped input.** It reads a JSON object and uses the untyped mapping at `request["artifact_spec"]`.  The legacy format contains `artifact_type`, Tasker version, IDs/names, action dictionaries, and catalog action arguments.  There is no public Typed IR model.
3. **Before render.** The CLI accepts only Tasker `6.7.6-beta` and `task`, `profile`, or `project`; renderer functions and action lookup then reject absent/invalid values through `KeyError`, `TypeError`, `ValueError`, catalog checks, and plugin-template checks.  A capability-prefixed Task additionally requires a catalog-backed `Return` action.
4. **After render.** The generated `ElementTree` is checked by `validate(..., policy=True)` from `validate_tasker_xml.py`; Projects additionally receive in-process graph validation.  Export is deterministic for a given request and writes the XML plus generation result/manifest information.  Standalone commands are `validate_tasker_xml.py --policy` and `validate_tasker_graph.py`.

The existing renderer is therefore the adapter target.  The Runtime Echo slice must create its legacy request only after Typed Spec and Typed IR validation, and must not alter existing callers or the canonical Project candidate.

## Existing contracts and artifacts

5. **Runtime contracts in Tasker.** Tasker has transport-boundary documentation, a capability prefix/Return-action policy, candidate conventions, static manifests, XML policy, graph validation, and the exact/semantic roundtrip comparator.  It does not contain a Runtime Echo request/result contract, `command_id`, `result_token`, `submit_progress`, or `submit_result` implementation.
6. **Repository ownership.** `hermes-tasker` owns typed intent, IR, deterministic rendering, candidate/manifest/hash generation, static validators, and portable static evidence.  `hermes-android` owns Hermes Bridge transport, accessible storage, assisted Tasker import, actual execution, human confirmation, result capture, re-export, and device evidence.
7. **Echo candidate.** No Runtime Echo candidate, spec, IR, or manifest exists at the audited Tasker base.  The only canonical runtime-adjacent evidence is the historical Project renderer candidate and its byte-identical re-export; it must remain unchanged.

## Android audit (read-only)

### ANDROID_VERSIONED_CAPABILITIES

The committed Android base supplies Hermes Bridge routing, authenticated transport, Android shell/terminal execution, accessibility/notification observation, device information, and an `ActionExecutor` with an observed Tasker `ACTION_TASK` handling path.  The repository documentation calls Hermes Bridge the preferred device integration.  These are reusable transport primitives, but the committed base contains no versioned Tasker candidate-import endpoint, no Runtime Echo manifest parser, and no structured Tasker result receiver/correlation API using `command_id` and `result_token`.

### ANDROID_UNCOMMITTED_OBSERVATIONS

The read-only checkout has uncommitted Tasker-result-channel files and modifications (including result HTTP/TCP/provider-related paths).  They are explicitly **UNCOMMITTED_OBSERVATION** only: they are neither copied nor treated as available APIs, evidence, or a reason to pass the gate.

### ANDROID_REQUIRED_GAPS

At the committed base, a minimal versioned Bridge contract is still required for immutable candidate transfer/hash checks, assisted import/selection, invocation, structured result capture, and exact correlation.  Consequently Android changes are expected after the static gate and the Tasker-to-Android integration contract; no Android worktree is created by this phase.

8. **Available transport.** Hermes Bridge is the preferred existing transport.  Manual import, ADB, and shell are fallback operational mechanisms, not a new architecture for this slice.
9. **Current correlation.** No committed Tasker runtime result correlation contract was found.  The new contract must carry explicit command and result identifiers; free text cannot be status.
10. **Human confirmation.** Tasker import/permission UI remains a human confirmation boundary.  The bridge may prepare and observe the run, but must not bypass a required Tasker security confirmation.
11. **Portable evidence.** Tasker can version the normalized spec/IR, candidate XML, manifest, SHA-256 values, static validator outputs, request/expected result, generator commit, and reproduction command.  Android can later add safe timestamps, device/Tasker versions, transfer hashes, structured result, selected/imported task evidence, and a minimal redacted log.

## XML hardening boundary

12. **Shared hotspots.** The renderer, `validate_tasker_xml.py`, `scripts/common.py`, existing generator tests, README, SKILL, and CI overlap with XML hardening.  The XML branch reserves its support matrix and shape contracts and defers renderer/validator integration.  This branch will add only a narrow Typed-IR-to-existing-renderer adapter and will not copy or merge XML hardening changes.

The future integration contract is deliberately small: Typed IR states semantic intent; a support matrix authorizes/rejects rendering; a shape contract defines XML serialization; the renderer materializes it; and the validator enforces the same rules symmetrically.  No support matrix is implemented here.

## Audit conclusion

The canonical base and Project roundtrip verifier are intact.  A single Task-only Runtime Echo vertical slice can be implemented without widening XML support: Typed Spec -> Typed IR -> legacy request adapter -> existing deterministic renderer -> static candidate/manifest gate.  The Android execution gate cannot be passed from Tasker-only tests and will remain blocked until a versioned Android transport contract and a real correlated Pixel run exist.
