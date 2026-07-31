# Hermes Task Runtime v2.4 — Installed Runner Reference

**Purpose:** pin the exact Tasker Project XML that we treat as the canonical
v2.4 runner for `hermes-tasker` work, so contracts and gates line up with
what is actually exported and importable in Tasker 6.7.6-beta on Pixel 8.

## Source of truth

| Field | Value |
|---|---|
| Artifact | `docs/runtime/hermes-tasker-runtime-v2.4.prj.xml` |
| Project name | `Hermes · Remote Task Runner v2.4` (id `551`) |
| Tasker version | `6.7.6-beta` |
| Export source | Tasker backup/import XML, Tasker 6.7.6-beta, Pixel 8 |
| Captured at | 2026-07-30T15:05:53Z |
| SHA-256 | `fb772103af1c70ee11d37c57aef86a652999a2aac04570ab51a513146f311a58` |
| Size | 78 711 bytes |
| Origin | `/home/ubuntu/.hermes/cache/documents/doc_904d3961fe7b_Hermes_Task_Runtime_v2.4.prj.xml` |

## Components (from the Project XML)

| Type | ID | Name |
|---|---|---|
| Profile | 560 | Hermes · Remote Task Import v2.4 |
| Profile | 561 | Hermes · Result Probe v2.4 |
| Task | 551 | Hermes · Run Task v2.4 |
| Task | 552 | Hermes · Capability · Smoke v1 |
| Task | 553 | Hermes · Result Probe v2.4 |
| Task | 554 | Hermes · Import Task v2.4 |
| Task | 555 | Hermes · Confirm Import v2.4 |
| Task | 563 | Hermes · Capability · Runtime Status v1 |

## Contract surface

- **Import intent:** `com.hermes.tasker.v2.4.IMPORT_TASK` (Profile 560 → Task 554)
- **Result probe:** `com.hermes.tasker.v2.4.PROBE_RESULT` (Profile 561 → Task 553)
- **Result channel:** ContentProvider on `com.hermesandroid.bridge.taskerresult`
  with `submit_result` / `submit_progress` methods.
- **Envelope:** `hermes-tasker-result/v1` with `operation: import | run | probe`.

The full contract lives in `PROJECT_PLAN_tasker-safe-update-v1.md` (Phase A
baseline) and in the typed-IR / roundtrip docs brought by the
`codex/typed-ir-runtime-v1` and `codex/roundtrip-evidence-canonicalization-v1`
branches on `recovery/hermes-tasker-consolidation`.

## How to verify against the live device

The artifact above is **the export we have**. It is not a guarantee that
the same Project is currently installed on Shiba. To confirm the live
state, run the Capability Runtime Status Task (id `563`) on the device
through Hermes Bridge and compare the reported IDs and event strings
against this file.

The intended path is `hermes-android` Bridge → `RUN_TASK` on
`Hermes · Capability · Runtime Status v1` → JSON result listing
`last_import`, `last_run`, `last_probe`, and `provider_reply` keys.

## How to regenerate this artifact

If the runner changes (new IDs, new envelopes, new tasks):

1. Export from Tasker on the target device (Tasker → ⋮ → "Export
   Description as XML").
2. Save the `.prj.xml` over `docs/runtime/hermes-tasker-runtime-v2.4.prj.xml`.
3. Recompute SHA-256 (`sha256sum docs/runtime/hermes-tasker-runtime-v2.4.prj.xml`)
   and update the table above.
4. Bump the version suffix if the contract changes incompatibly
   (e.g. `v2.5`), and add a migration recipe to
   `references/migrations/`.

## What this file is *not*

- Not an executable. Don't try to import it through Hermes CLI; it
  must travel through `hermes-android` Bridge so the bridge can stage
  it on `content://com.hermesandroid.bridge.taskerresult`.
- Not a substitute for the live device check. Treat it as a
  reference contract, and verify before claiming v2.4 is the
  installed runner.
