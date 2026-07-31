# Recreate Typed IR/Runtime Gate v1

Start from the canonical roundtrip base, not `gate/typed-ir-runtime-v1` (which is an alias): `codex/roundtrip-evidence-canonicalization-v1` after its portable verifier passes.

1. Create a new isolated branch and worktree from that canonical base. Define typed schemas/models whose minimum component identity is `kind`, `identifier`, `variant`, and `values`; add parsing and validation tests before adapters.
2. Add the smallest adapter from the final Typed IR to the existing renderer. Preserve the existing Project candidate and run `python3 scripts/verify_roundtrip_evidence.py` as a regression before and after the adapter.
3. Add a deterministic Runtime Echo candidate, including its manifest, fixed identifiers, expected inputs, `result_token`, and expected output. Keep every runtime artifact in versioned portable paths.
4. Implement the runtime execution/correlation collector outside the renderer. Record command, device/Tasker version, candidate hash, transfer hash, runtime result, and recovered hash without embedding credentials.
5. Add focused tests for schemas, adapter, renderer compatibility, Runtime Echo candidate, and result correlation. Run the full test suite, static candidate checks, roundtrip comparator, and portable evidence verifier.
6. Close the new gate only after a real runtime run supplies a versioned evidence bundle with verified hashes and a declared Typed IR/runtime verdict. Do not promote unrelated Project actions from the roundtrip gate to runtime coverage.
