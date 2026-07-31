# XML authoring hardening V1 working set

- Initial HEAD: `ef6f99ecb30f89c42b3ac6b32f8c05145683d9a4`
- Branch: `codex/xml-authoring-hardening-v1`
- Worktree: `/home/ubuntu/code/hermes-tasker-xml-hardening-v1`
- Parallel missions detected: `gate/assisted-project-roundtrip-v1`, `gate/typed-ir-runtime-v1`.
- Exclusive paths: `data/xml-support-matrix.json`, `data/schemas/`, `data/xml-shape-contracts/`, `scripts/xml_support.py`, `scripts/xml_shape_contracts.py`, `scripts/validate_xml_support_matrix.py`, `tests/test_xml_*.py`, `fixtures/golden/xml-authoring-v1/`, XML hardening reports/references.
- Shared hotspots: renderer, XML validator, `scripts/common.py`, existing generator tests, README, SKILL, CI.
- Prohibited: `hermes-android`, Typed IR/runtime modules, historical fixtures, broad refactors and dependency changes.
- Consumed interfaces: catalog JSON and plugin-template JSON through stable dictionaries; existing renderer/validator only at the later integration checkpoint.
- Integration points: narrow support lookup in renderer and symmetric policy lookup in validator, deferred until the parallel branches are reviewed.
- Merge risks: parallel branches may add roundtrip evidence and candidate fixtures; no conflict is present at initial inspection.
- Commit order: working set, audit, levels, matrix, contracts, golden corpus, mutations, integration boundary, renderer, validator, integrity/CI/docs.
