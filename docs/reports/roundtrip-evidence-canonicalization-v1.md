# Roundtrip Evidence Canonicalization v1

## Decision

`ROUNDTRIP_EVIDENCE_CANONICALIZATION_V1=PASS`  
`ROUNDTRIP_GATE_VERDICT=EXACT_PASS`

The canonical pair is already versioned and is independently confirmed by the external bundle:

- candidate: `fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml`
- reexport: `fixtures/exported/project-renderer-gate-v1/artifact.reexported.prj.xml`
- SHA-256 for both: `0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1`
- byte comparison: `cmp -s` exit 0
- comparator: lexical, structural, and semantic differences all zero; verdict `EXACT_PASS`.

The portable command is:

```bash
python3 scripts/verify_roundtrip_evidence.py
```

It consumes only versioned paths and fixed hashes. The absolute external path remains provenance only, never a CI dependency.

## Historical naming discrepancy

The committed `artifact_valid.prj.xml` is not the canonical candidate. Its SHA-256 is `f65fdd7ce7566a3cda443a23122035b458b3d27fedf6579f1f3b55a29a60ea82` and it fails comparison against the recovered reexport. No XML bytes, timestamps, IDs, whitespace, or names were changed to obtain this result.
