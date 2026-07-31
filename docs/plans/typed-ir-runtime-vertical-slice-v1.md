# Typed IR Runtime Echo vertical slice v1

## Boundary

This design adds one Task-only capability: `runtime.echo`.  It is a strict vertical slice, not a general capability framework or an XML-support expansion.

```
RuntimeEchoSpec -> RuntimeEchoInvocation -> legacy renderer request -> existing renderer
```

The first two representations are immutable dataclasses and serialize with sorted keys and compact JSON.  The adapter is the sole place that knows the legacy renderer mapping.  The IR contains no XML, paths, device details, transport handles, or secrets.

## Typed Spec

`RuntimeEchoSpec` is the public external input.  Its exact fields are `capability`, `payload`, `command_id`, and `result_token`; unknown fields fail closed.  `capability` must be `runtime.echo`; the other three values must be non-empty strings.  Payload has an explicit conservative maximum of 1024 Unicode code points; command and token each have a 256-character maximum.  Error codes/messages are stable constants.

## Typed IR

`RuntimeEchoInvocation` is an internal semantic value with `capability_id`, `invocation_id`, `result_token`, and `payload`.  `from_spec()` is pure, deterministic, and validates the same invariants at the boundary.  Equality is value equality.  JSON/XML-looking values are plain payload strings only; the IR schema exposes no XML or transport field.

## Renderer adapter and output

`to_legacy_tasker_request()` accepts only a valid `RuntimeEchoInvocation`.  It emits the existing Task request shape for a deterministic Task whose catalog-backed Return action returns a canonical JSON success envelope containing the capability, payload, command ID, and result token.  It uses a fixed task ID and name for the v1 evidence candidate.  No raw action dictionary may enter the new public path.

The existing renderer remains responsible for catalog lookup, XML serialization, policy validation, graph validation where applicable, and export.  The legacy CLI remains supported unchanged.  Unknown capabilities, incomplete IR, unexpected variants, and unsupported adapter arguments raise stable typed errors before rendering.

## Runtime request and result

The Android handoff is transport-independent JSON:

* request: `capability`, `command_id`, `result_token`, `payload`, candidate/manifest SHA-256, and immutable run ID;
* accepted/progress: structured events carrying the run ID and both correlation IDs;
* terminal result: `status` (`success` or `failure`), capability, command ID, result token, payload on success, timestamps, hashes, and structured error on failure.

Only exact equality of command ID, token, payload, and `success` closes Runtime Echo.  Text logs and notifications are evidence attachments, never status sources.  Duplicate, stale-run, wrong-token, wrong-command, wrong-payload, and timeout results fail closed.

## Evidence

The static candidate contains normalized spec and IR JSON, XML, manifest, SHA-256 values, generator commit, regeneration command, validator commands, and the expected runtime result.  Runtime evidence is created later by the Android transport and may contain only safe request/result fields, timestamps, versions, hashes, and minimal logs.  No device paths, credentials, or reusable secrets are versioned.

## Ownership and exclusions

`hermes-tasker` owns the models, renderer adapter, deterministic candidate, manifest, static gate, and integration contract.  `hermes-android` owns transfer, hashes at each boundary, assisted import, execution, structured capture, correlation, device evidence, and any required human confirmation.

Excluded: general IR versioning, all-action migration, public YAML DSL, universal Profiles/Projects, renderer refactor, Android transport redesign, dynamic JavaScript generation, XML support matrix integration, and a second capability.

## Future XML-hardening integration

Typed IR expresses semantic intent.  A future support matrix authorizes/rejects rendering; a shape contract defines XML serialization; the renderer materializes it; and the validator checks the same rules symmetrically.  This branch does not implement or import those XML-hardening assets.
