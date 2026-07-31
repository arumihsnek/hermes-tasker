# XML evidence support levels

Support is explicit and monotonic only when its required evidence is recorded.

- `catalog_only`: the official catalog identifies a component and its declared positions/types. It never authorizes XML generation or acceptance as an authored shape.
- `fixture_backed`: an immutable real export with provenance exists. It describes an observed shape but does not authorize the renderer.
- `renderer_golden`: a contract, exact golden bytes, deterministic test, and validator pass exist. This authorizes rendering.
- `roundtrip_exact`: a rendered artifact was imported and re-exported byte-for-byte identically, with evidence referencing both files and the comparison gate.
- `runtime_verified`: roundtrip evidence is supplemented by target-device execution evidence.
- `unsupported`: deliberately rejected because evidence is missing, contradictory, incompatible, or unsafe.

The catalog can establish only `catalog_only`. A transition requires the evidence fields and tests for the target level; documentation cannot promote a form. A missing or contradictory prerequisite demotes the form to `unsupported` for authoring. Runtime verification never makes a form renderable without the lower levels.
