# Roundtrip Chain of Custody v1

Run `run-20260728T004816Z-43023f` identifies the canonical Project bytes by SHA-256, not by the later `artifact_valid.prj.xml` name.

| Stage | Path | SHA-256 | Source that demonstrates it |
|---|---|---|---|
| Generated | `provenance/candidate.original.prj.xml` (external) | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | `provenance/candidate.lock.json`, `preflight/preflight.json` |
| Validated | `fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml` | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | byte match with external original; versioned manifest; portable verifier |
| Pushed | Pixel path represented by `content://com.android.externalstorage.documents/document/primary%3ATasker%2Fhermes%2FHermes_project_0ec73026b83dedad.prj.xml` | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | `preflight/preflight_summary.json` reports candidate, Pixel, and recovered hashes equal |
| Imported | Tasker import activity invoked with that content URI | same candidate hash | `transport/am_start_output.json`, `transport/import_error_state.json` |
| Reexported | `reexport/artifact.reexported.prj.xml` (external) | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | `comparison/verdict.json`; external file bytes |
| Compared left | `fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml` | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | `fixtures/exported/project-renderer-gate-v1/roundtrip-result.json` |
| Compared right | `fixtures/exported/project-renderer-gate-v1/artifact.reexported.prj.xml` | `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1` | `fixtures/exported/project-renderer-gate-v1/roundtrip-result.json` |

The preflight records Tasker `6.7.6-beta` on a Google Pixel 8 (`shiba`, Android release `17`), and the import-activity transcript records a successful launch. The external comparison verdict contains no differences and reports `EXACT_PASS`.

`artifact_valid.prj.xml` is a separate 1,596-byte file with SHA-256 `f65fdd7ce7566a3cda443a23122035b458b3d27fedf6579f1f3b55a29a60ea82`. It is not an alias for the original candidate and is intentionally excluded from the custody chain.

`ROUNDTRIP_CHAIN_OF_CUSTODY_COMPLETE`
