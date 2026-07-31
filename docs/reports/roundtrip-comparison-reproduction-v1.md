# Roundtrip Comparison Reproduction v1

Official comparator: `python3 scripts/compare_tasker_roundtrip.py LEFT RIGHT --output RESULT.json`.

| Pair | Left SHA-256 | Right SHA-256 | Lexical | Structural | Semantic | Byte comparison |
|---|---|---|---|---|---|---|
| versioned canonical candidate vs versioned reexport | `0ec730…3e1` | `0ec730…3e1` | PASS, 0 differences | PASS, 0 differences | PASS, 0 differences | `cmp -s` exit 0 |
| external original candidate vs external reexport | `0ec730…3e1` | `0ec730…3e1` | PASS, 0 differences | PASS, 0 differences | PASS, 0 differences | equal hashes; external `comparison/verdict.json` reports byte equality |
| external `artifact.prj.xml` identity vs reexport | `0ec730…3e1` | `0ec730…3e1` | PASS, 0 differences | PASS, 0 differences | PASS, 0 differences | equal bytes through the versioned copy |
| `artifact_valid.prj.xml` vs versioned reexport | `f65fdd…ea82` | `0ec730…3e1` | 3 differences | 3 differences | 2 differences | different |

The last row is diagnostic only. It proves that `artifact_valid.prj.xml` must not replace the candidate identified by the external lock, transfer summary, and historical roundtrip result.

Reproduction command:

```bash
python3 scripts/verify_roundtrip_evidence.py
```

It verifies the two portable bytes, their fixed SHA-256, and the comparator's `EXACT_PASS`; it does not read `/home/ubuntu/evidence`.
