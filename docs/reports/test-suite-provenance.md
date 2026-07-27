# Test Suite Provenance Report

## Executive Summary

This document establishes the authoritative provenance of test counts for the `hermes-tasker` repository, resolving the previously reported discrepancy between 56 tests (pre-migration) and 36 tests (current).

**Conclusion**: The missing 20 tests belong to the **runtime/evidence/transport layer** (`hermes-android` / Bridge), not the transport-independent `hermes-tasker` toolchain. The current count of **36 tests** is correct for `hermes-tasker`.

---

## Original Reported Counts

| Metric | Previously Reported | Current Verified |
|--------|--------------------|------------------|
| Focused generator tests | 36 | **36** ✅ |
| Full test suite | 56 | **36** (current), **56** (pre-migration backup) |

---

## Test Classification: The 56 Tests from Pre-Migration Backup

The pre-migration backup at `/home/ubuntu/.hermes/skills/tasker-artifact-generator.pre-migration-20260727-205641` contains **56 collected tests** across 10 test files:

| File | Test Count | Classification | Owner |
|------|------------|----------------|-------|
| `test_tasker_artifact_generator.py` | 36 | **A. Static generator/validator** | `hermes-tasker` ✅ |
| `test_tasker_evidence_collector.py` | 1 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_e2e_echo_v21_contract.py` | 1 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_e2e_fixture.py` | 2 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_contract.py` | 3 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_evidence_callback.py` | 1 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_evidence_task.py` | 1 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_negative_contract.py` | 3 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_v21_callback_contract.py` | 2 | **C. Runtime/evidence** | `hermes-android` / runtime |
| `test_runtime_v21_contract.py` | 7 | **C. Runtime/evidence** | `hermes-android` / runtime |
| **Total** | **56** | | |

### Classification Breakdown

| Class | Description | Count | Repository |
|-------|-------------|-------|------------|
| **A** | Static generator/validator tests (catalog, graph, policy, regression) | **36** | `hermes-tasker` ✅ |
| **B** | Catalog/contract tests | 0 | — |
| **C** | Runtime/import/evidence tests (Bridge, callback, gateway, v21 contracts) | **20** | `hermes-android` / runtime ❌ |
| **D** | Bridge/transport tests | 0 | `hermes-android` |
| **E** | Obsolete/experimental | 0 | — |
| **F** | Unresolved | 0 | — |

**Total accounted**: 36 (A) + 20 (C) = **56** ✅

---

## Ownership Boundary

```
┌─────────────────────────────────────────────────────────────────┐
│                    hermes-tasker (this repo)                    │
│  Transport-independent artifact generation & validation         │
│  ✅ 36 static tests — catalog-backed XML generation             │
│  ✅ XML policy validator                                        │
│  ✅ Graph structure validator                                   │
│  ✅ Static Project candidate                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
              Transport boundary (artifacts + manifests)
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    hermes-android (separate repo)               │
│  Android transport, Bridge, runtime integration                 │
│  🔶 20 runtime/evidence tests — Bridge, callback, gateway       │
│  🔶 Tasker import/roundtrip execution                           │
│  🔶 Device interaction (Pixel, ADB, Shizuku)                    │
└─────────────────────────────────────────────────────────────────┘
```

The 20 Class C tests were **co-located** in the pre-migration skill directory because the skill was developed inside `hermes-android` before extraction. They were never part of the transport-independent toolchain's test suite.

---

## Verification Commands

```bash
# Current hermes-tasker (canonical checkout)
cd /home/ubuntu/code/hermes-tasker
python3 -m pytest --collect-only -q tests
# → 36 tests collected

python3 -m pytest -q tests
# → 36 passed

# Pre-migration backup (preserved, unchanged)
cd /home/ubuntu/.hermes/skills/tasker-artifact-generator.pre-migration-20260727-205641
python3 -m pytest --collect-only -q tests
# → 56 tests collected (36 static + 20 runtime)

python3 -m pytest -q tests
# → 56 passed
```

Both collections verified on **2026-07-27**.

---

## Static Validation Results (Current HEAD: `36651e2`)

| Gate | Command | Result |
|------|---------|--------|
| Focused generator tests | `pytest -q tests/test_tasker_artifact_generator.py` | **36 passed** |
| Full test suite | `pytest -q tests` | **36 passed** |
| XML Policy Validator | `python3 scripts/validate_tasker_xml.py fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml --policy` | **PASS** |
| Graph Validator | `python3 scripts/validate_tasker_graph.py fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml` | **PASS** |
| Candidate files exist | `test -f fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml` | **PASS** |

---

## Commit History Evidence

| Commit | Description | Test Count at Commit |
|--------|-------------|---------------------|
| `b5689eb` | Close static Project renderer conformance gate | 36 static tests (this repo) |
| `6a3bc8f` | Add catalog data and shared modules | — |
| `d1491f0` | Add normalize_catalogs.py | — |
| `75a4374` | Add standalone repo docs and CI | — |
| `36651e2` | Add SKILL.md for Hermes skill | — |

The static gate commit `b5689eb` is an ancestor of current `HEAD` (`36651e2`).

---

## Conclusions

1. **No tests were lost** during the repository extraction. The 20 "missing" tests were never part of the transport-independent toolchain.

2. **The authoritative test count for `hermes-tasker` is 36** — all static generator and validator tests.

3. **The 20 runtime tests belong to `hermes-android`** (Bridge, gateway, callback, evidence, v21 runtime contracts) and should reside in that repository's test suite.

4. **README test counts updated**: Focused = 36, Full = 36 (both now match the verified static suite).

5. **No test restoration is needed** — the current 36-test suite is complete for the `hermes-tasker` scope.

---

## References

- Canonical checkout: `/home/ubuntu/code/hermes-tasker` (commit `36651e23e11a61b46803cb7637cb1d09d906e0d6`)
- Pre-migration backup: `/home/ubuntu/.hermes/skills/tasker-artifact-generator.pre-migration-20260727-205641` (preserved, unmodified)
- Hermes skill symlink: `/home/ubuntu/.hermes/skills/tasker-artifact-generator` → canonical checkout
- Static gate commit: `b5689eb` (ancestor of HEAD)
- Related repo: `/home/ubuntu/code/hermes-android` (unchanged by this mission)

---

*Document created: 2026-07-27*  
*Mission: Close Hermes Tasker Repository Publication Hygiene*  
*Status: PROVENANCE_RESOLVED*