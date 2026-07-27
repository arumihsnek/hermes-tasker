# Hermes Tasker Toolchain

Standalone Tasker artifact generation, validation, contracts, fixtures and roundtrip tooling for Hermes and other integrations.

## Repository Purpose

This repository is a **transport-independent** producer and validator of Tasker artifacts (Tasks, Profiles, Projects). It generates catalog-backed XML, validates it against XML policy and structural graph rules, and provides fixtures and contracts for evidence-based authoring.

**It does not:**
- Interact with Android devices
- Import or execute artifacts on Tasker
- Depend on Hermes Bridge or Android transport
- Claim runtime verification without a transport adapter

**It does:**
- Generate `.tsk.xml`, `.prf.xml`, `.prj.xml` from typed specifications
- Validate against official Tasker catalogs (actions, events, states, plugin templates)
- Enforce Project graph structure (root-sibling layout, reference kinds, ID uniqueness)
- Provide reproducible CI validation of all artifacts and the static Project candidate
- Define the contract boundary with transport layers (e.g., `hermes-android`)

## Current Status

| Artifact | Status | Evidence |
|---|---|---|
| Standalone Task (`.tsk.xml`) | Supported | Official catalog + real 6.7.6-beta exports |
| Profile with Intent Received Event (`.prf.xml`) | Supported | Official catalog + Pixel 8 exports |
| Profile with State context | Supported | Real 6.7.6-beta backup fixtures |
| Profile with Day context | Supported | Official Day contract + Pixel 8 fixtures |
| Profile with Location context | Supported | Official Loc contract + Pixel 8 fixtures |
| Profile with exit task (`mid1`) | Supported | Real backup profiles |
| Project containing profiles (`.prj.xml`) | **Static gate PASS** | Real exports + structural validation |
| Java Code (code 474) | Supported | Official catalog + Pixel 8 exports |
| Termux:Tasker Run Command | Supported | Evidence template + typed replacements |
| AutoTools actions | Supported | Exact evidence templates |
| JavaScriptlet (code 129) | Supported | Static reviewed gateway/capability source |

**Static validation gate**: ✅ **PASS** (commit `b5689eb`)
- 36 focused generator tests pass
- 36 full static tests pass  
- XML policy validator: PASS
- Graph validator: PASS
- Codex review: 0 BLOCKERs, 1 IMPORTANT addressed
- Tasker assisted import and roundtrip: **PENDING**

> **Note on test counts**: The static `hermes-tasker` toolchain has **36 tests**. An earlier report of 56 tests included 20 runtime/evidence/transport tests that belong to the `hermes-android` Bridge layer. See [Test Suite Provenance Report](docs/reports/test-suite-provenance.md) for the full classification.

**Target version**: Tasker 6.7.6-beta on Pixel 8

## Supported Artifacts

| Type | Extension | Generator | Validator |
|---|---|---|---|
| Task | `.tsk.xml` | `generate_tasker_artifact.py` | `validate_tasker_xml.py` + `validate_tasker_graph.py` |
| Profile | `.prf.xml` | `generate_tasker_artifact.py` | `validate_tasker_xml.py` + `validate_tasker_graph.py` |
| Project | `.prj.xml` | `generate_tasker_artifact.py` | `validate_tasker_xml.py` + `validate_tasker_graph.py` |

## Static Validation Architecture

```
Planner / Tasker knowledge
         ↓
Tasker description or typed IR
         ↓
Deterministic artifact renderer (generate_tasker_artifact.py)
         ↓
XML policy validator (validate_tasker_xml.py --policy)
         ↓
Graph validator (validate_tasker_graph.py)
         ↓
Transport adapter (hermes-android, ADB, manual, etc.)
         ↓
Tasker import / runtime
         ↓
Evidence and roundtrip analysis
```

The renderer and validators stop at the transport boundary. They produce artifacts and validation evidence; they do not execute them.

## Relationship with `hermes-android`

| Repository | Role |
|---|---|
| `hermes-tasker` | **Transport-independent** producer and validator |
| `hermes-android` | **Preferred Android transport** and runtime integration |

- `hermes-tasker` generates artifacts and manifests
- `hermes-android` consumes artifacts/manifests via Hermes Bridge
- Bridge is the **preferred** integration, not a hard dependency
- Manual import, ADB, or other transports can consume the same artifacts
- Roundtrip transport (import + re-export + compare) is owned by `hermes-android`
- Roundtrip semantic comparison is owned by `hermes-tasker`

## Installation

### As a Hermes Skill

```bash
# The skill installs as a symlink to the canonical checkout
ln -s /home/ubuntu/code/hermes-tasker /home/ubuntu/.hermes/skills/tasker-artifact-generator
```

Requires `SKILL.md` in the skill root (present in this repo).

### Direct Local CLI Usage

```bash
cd /home/ubuntu/code/hermes-tasker

# Generate a Task
python3 scripts/generate_tasker_artifact.py --request request.json --output-dir out/

# Validate XML (catalog + policy)
python3 scripts/validate_tasker_xml.py out/artifact.tsk.xml --policy

# Validate graph structure
python3 scripts/validate_tasker_graph.py out/artifact.tsk.xml
```

## Test Commands

```bash
# Focused generator tests (36 tests)
python3 -m pytest -q tests/test_tasker_artifact_generator.py

# Full static test suite (36 tests)
python3 -m pytest -q tests

# Validate static Project candidate
python3 scripts/validate_tasker_xml.py fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml --policy
python3 scripts/validate_tasker_graph.py fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml
```

## Validator Commands

```bash
# XML catalog + policy validation
python3 scripts/validate_tasker_xml.py <artifact.xml> [--policy]

# Graph structure validation (IDs, mid0/mid1, pids, tids, nesting)
python3 scripts/validate_tasker_graph.py <artifact.xml>
```

## Candidate and Fixture Policy

- **Fixtures** (`fixtures/`): Real Tasker exports from Pixel 8 (6.7.6-beta), organized by source. Immutable evidence.
- **Candidates** (`fixtures/candidates/`): Locally generated artifacts that have passed static validation. Versioned (e.g., `project-renderer-gate-v1/`). They are **test evidence** and remain tracked.
- **Exported** (`fixtures/exported/`): Tasker re-exports of candidates after import (roundtrip). Created by `hermes-android` transport.
- **Backup/Invalid/Valid**: Internal test organization, not evidence.

The static Project candidate at `fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml` contains:
- Profile 1001 (Intent Received event, code 599)
- Task 2001 (Flash action, code 548)
- Project element with `pids="1001"` and `tids="2001"`
- Root-sibling layout: Profile, Project, Task all direct children of `<TaskerData>`

## Known Limitations

> **Tasker assisted import and roundtrip remain pending.**

Static validation (catalog, policy, graph) is complete and passing. The following are **not yet verified**:
- Actual Tasker import of generated Project artifacts
- Re-export comparison (semantic roundtrip)
- Runtime execution on device
- Profile enable/disable behavior
- Variable propagation across transport

Do not claim Pixel or runtime verification. The `STATIC_GATE_PASS` designation applies only to the static validation layer.

## Meaning of `STATIC_GATE_PASS`

A commit tagged or described as achieving `STATIC_GATE_PASS` means:

1. All focused tests pass (currently 36)
2. All full tests pass (currently 36)
3. XML policy validator returns `PASS` on the Project candidate
4. Graph validator returns `PASS` on the Project candidate
5. No Codex BLOCKER findings
6. No Task/Profile regressions introduced
7. No Tasker import, Pixel interaction, or Bridge modification occurred

It does **not** imply Tasker import success, runtime correctness, or transport verification.

## Architecture

### Core Modules

| Module | Purpose |
|---|---|
| `scripts/generate_tasker_artifact.py` | Renderer: typed spec → XML (Task, Profile, Project) |
| `scripts/validate_tasker_xml.py` | Catalog + policy validation |
| `scripts/validate_tasker_graph.py` | Structural graph validation |
| `scripts/common.py` | Shared catalog loading, JSON result formatting |
| `scripts/normalize_catalogs.py` | Official catalog → normalized JSON |

### Data Contracts

- `data/actions.json` — 382 actions (code, args, outputs, constraints)
- `data/event-contexts.json` — 90 event types
- `data/state-contexts.json` — 52 state types
- `data/plugin-templates.json` — Plugin bundle templates
- `data/dialog-types.json` — Input dialog types
- `data/built-in-variables.json` — Built-in variables

### References

- `references/project-xml-contract.md` — Canonical Project element order and rules
- `references/task-xml-contract.md` — Task structure
- `references/profile-xml-contract.md` — Profile structure
- `references/artifact-selection.md` — Artifact type decision tree
- `references/source-inventory.md` — Evidence classification
- `references/java-code.md` — Java Code (474) patterns
- `references/variables.md` — Variable naming rules
- `references/unsupported.md` — Explicitly unsupported features

## CI

GitHub Actions workflow at `.github/workflows/ci.yml` runs on every push and PR:

1. Check out the repository
2. Install Python 3.11
3. Install pytest explicitly
4. Run focused generator tests
5. Run full static test suite
6. Validate Project candidate with XML policy validator
7. Validate Project candidate with graph validator
8. Verify candidate files exist

All validations must pass for CI to succeed.

## License

MIT