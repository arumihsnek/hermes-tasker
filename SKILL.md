---
name: tasker-artifact-generator
description: Use when authoring Tasker .tsk.xml, .prf.xml, or .prj.xml from requirements with evidence-bound XML generation.
version: 0.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [tasker, xml, task, profile, project, validation, artifacts]
    related_skills: [tasker-capability-runtime, tasker-integration]
---

# Tasker Artifact Generator

## Overview

Author Tasker artifacts from natural-language intent **only after** selecting an artifact type and proving every emitted XML node against authoritative sources. This skill authors and validates artifacts; `tasker-capability-runtime` imports, runs, and verifies them.

**Evidence gate:** never infer an Action, Context, code, argument position/type, Bundle, plugin configuration, output variable, flag, or XML ordering by analogy. When proof is absent, return `unsupported` and request the smallest target-version export needed.

## When to Use

- A user asks to design or generate a Tasker Task (`.tsk.xml`), Profile (`.prf.xml`), or Project (`.prj.xml`).
- An existing Tasker XML artifact needs catalog, graph, policy, or source-evidence validation.
- A new official Tasker catalog or exported fixture needs normalization and comparison.

Do **not** use this skill to import, execute, or confirm a Tasker artifact. Hand the validated output to `tasker-capability-runtime` for the runtime phase.

## Current Evidence Boundary

Target version: **Tasker 6.7.6-beta** on Pixel 8.

| Artifact | Status | Reason |
|---|---|---|
| Standalone Task | Supported, explicit typed spec only | Official Action catalog and standalone Task contract are normalized. |
| Profile with Intent Received Event | Supported | Official catalog + real 6.7.6-beta exports from Pixel 8. |
| Profile with State context | Supported | Real 6.7.6-beta backup profile fixtures: Battery Level (140), Display State (123), Orientation (120), HDMI Plugged (12), Keyboard Out (50), Unread Text (147), Variable Value (165). |
| Profile with Day context | Supported | Official Day contract plus 4 purpose-built Pixel 8 Hermes fixtures. |
| Profile with Location (`Loc`) context | Supported | Official Loc contract plus named/unnamed Pixel 8 Hermes fixtures. |
| Profile with exit task (mid1) | Supported | Real backup profiles with entry + exit tasks. |
| Project containing profiles | Supported | Real exports: Hermes_Task_Runtime_v2.prj.xml, Hermes___Java_Runtime.prj.xml. |
| Java Code (code 474) | Supported for static reviewed source | Official catalog + Java Code instructions + Pixel 8 exports. |
| Termux:Tasker Run Command | Supported with evidence template | Termux:Tasker 0.9.0 exact Bundle clone; typed replacements are restricted. |
| AutoTools actions | Supported as exact evidence templates | AutoTools 2.3.19 templates: Connectivity, Launcher, Web Screen, Dialog, Report, Sensors. |
| JavaScriptlet (code 129) | Supported for static reviewed gateway/capability source | Real Pixel 8 exports + official Intent Received / JavaScriptlet variable contract supplied for v2.1. |
| Other plugin configuration/non-empty Bundle | Unsupported | Requires real exported fixture and a template entry. |

Read `references/source-inventory.md` before broadening scope. Never promote an old example or a local runtime artifact into target-version proof.

## Mandatory Workflow

1. **Inventory sources.** Run `scripts/inspect_sources.py`; classify each input as normative, catalog, fixture valid, partial example, experiment, or secondary documentation. Record conflicts instead of silently merging them. Done when `references/source-inventory.md` reflects the available evidence.
2. **Normalize official catalogs.** Run `scripts/normalize_catalogs.py --source <official-file> --output-dir data`. The generated JSON preserves code, argument position/type, constraints, outputs, version, and source line. Done when catalog item counts are reported and tests pass.
3. **Classify the request before XML.** Use `references/artifact-selection.md` and report: `artifact_type`, `reason`, `trigger_model`, `reusable_named_tasks`, `persistent_state`, `import_method`, and `confirmation_required`.
4. **Design a typed spec.** Model `ArtifactSpec → TaskSpec/ProfileSpec/ProjectSpec → ContextSpec/ActionSpec/ArgumentSpec/ConditionSpec`. For every element, identify catalog source, code, complete parameter list, XML type, position, permitted values, output variables, Tasker version, and fixture/test evidence. Missing one means unsupported.
5. **Validate the spec and render.** Use `scripts/generate_tasker_artifact.py` only for the supported Task subset. It requires the complete exact argument set for each Action; it does not add defaults.
6. **Validate the artifact.** Run both XML/catalog/policy and graph validation. Done only when both return `PASS`.
7. **Create the companion manifest.** Declare inputs, outputs, effects, requirements, risk, idempotence, import method, and confirmation. Do not claim a runtime result.
8. **For runtime/dogfood, hand off.** Explicitly state that import/execution belongs to `tasker-capability-runtime`; it must use the established runtime contract and verify results independently.

## Typed Request and Result

Input is governed by `schemas/request.schema.json`. A safe Task request must include `artifact_spec` with Task ID, name, Effects/Requirements, and every Action’s catalog code plus complete typed arguments.

```bash
python3 scripts/generate_tasker_artifact.py \
  --request request.json --output-dir out/
python3 scripts/validate_tasker_xml.py out/artifact.tsk.xml --policy
python3 scripts/validate_tasker_graph.py out/artifact.tsk.xml
```

The result follows `schemas/generation-result.schema.json`. A valid response includes artifact and manifest paths plus XML/catalog/graph validation states. Unsupported responses identify `missing_evidence` instead of manufacturing XML.

## Capability Rules

For runtime-invocable Tasks:

- Name: `Hermes · Capability · <Domain> · <Action> v<N>`.
- Inputs: `%par1`, `%par2`; prefer JSON in `%par1` only with catalog-backed structured parsing.
- Include a catalog-backed `Return` action and declare structured output/effects/requirements.
- No production Flash unless it is the explicit contract.
- No remote dynamic code, `eval(`, secrets, or undocumented global variables.

The policy validator rejects `eval(` and a capability name without `Return`. It cannot prove JSON result semantics until a target-version Return fixture exists; do not overclaim that validation.

## Catalog and XML Rules

- Every Action/Event/State code and argument comes from `data/*.json`.
- Argument positions must exactly match the catalog. No default Bundles or omitted “optional” arguments unless the catalog/fixture proves their serialized representation.
- `Event` and `State` are distinct catalogs; Event `%evtprm` follows catalog parameter order, while State has no implicit `%evtprm`.
- XML content is serialized by an XML library, never manually concatenated.
- `scripts/validate_tasker_graph.py` verifies IDs, `mid0`, `mid1`, `pids`, and `tids`; it does not claim Tasker will repair errors.
- Do not normalize action `sr` behavior for `act10` / `act2` until a real >10-action import/re-export fixture proves semantics.

See `references/task-xml-contract.md`, `references/variables.md`, `references/java-code.md`, and `references/unsupported.md`.

## Roundtrip Discipline

`compare_tasker_export.py generated reexported` currently performs an exact diff. It ignores **nothing** because volatile fields and non-semantic ordering have not been demonstrated. Add each permitted normalizer only after a documented target-version roundtrip test.

### Project re-import collision procedure (Pixel 8 / Tasker 6.7.6-beta)

A Project import with a new Project name but existing **Task names** may not duplicate or visibly replace the Tasks. In an observed runtime update, Tasker created a new Project containing duplicated Profiles, left that new Project's `tids` empty, and rebound those Profiles to the pre-existing global Task IDs; the existing Tasks' action bodies were updated. Therefore:

1. Backup/export the old Project and a full Tasker backup; record Project `pids`/`tids`, Profile IDs, entry Task IDs, and enabled states.
2. Disable all listener Profiles for the affected actions before importing.
3. If the canonical Project name collides, rename the old Project to a distinct backup name, then import the intended Project through Tasker's **Import Project** UI.
4. Immediately audit the post-import backup: count Projects, Profiles per action, Project `tids`, Profile `mid0`, and actual Task action bodies. Do not rely on Project tab contents alone.
5. If Tasker creates a Profiles-only Project (`tids` empty) while updating existing Tasks, keep the Project that owns the updated Tasks, delete only the empty duplicate using **Delete Contents** after a post-import backup, then rename the valid Project to the canonical name.
6. Reaudit installed/enabled consumer counts before re-enabling Profiles. Never send a broadcast while count differs from one.

This is target-version behavior evidence, not a general Tasker XML rule.

### HTTP Request callback local-variable limitation (Pixel-verified)

In Tasker 6.7.6-beta, values produced by a JavaScriptlet did **not** propagate to subsequent Tasker actions: `HTTP Request` body received literals such as `%import_result_json` / `%result_json`, and URL query expansion received literal `%callback_payload`. Native `Variable Set` (self-assignment and local-to-global) did not change the behavior. Incoming Intent extras do expand, but JavaScriptlet-created values do not. Treat local-JSON → Tasker-HTTP callback as blocked until a target-version-supported serialization or separately approved transport is demonstrated. A static XML audit of callback order is only structural evidence; do not mark E2E PASS on it or on a `200` broadcast alone. Require a fresh correlated JSON callback accepted by the collector.

## Common Pitfalls

1. **Using 6.5.x examples as 6.7.6-beta templates.** They are useful historical examples, not target-version serialization proof.
2. **Generating a Profile/Project because the context/action code is known.** Structure, flags, order, and references still require current fixtures.
3. **Treating a `Bundle` as optional.** It is emitted only when the specific catalog declares it; non-empty content requires a fixture.
4. **Confusing authoring with runtime.** This skill never silently imports or executes artifacts.
5. **Treating a plugin UI label as an XML configuration.** Request a minimal real export.
6. **Emitting JavaScriptlet or dynamic code.** Both are outside the evidence boundary.

## Verification Checklist

- [ ] Source inventory completed and conflicts recorded.
- [ ] Normalized catalog records source authority/line and correct counts.
- [ ] Artifact classification reported before rendering.
- [ ] Every emitted Action/Context code, argument, and output variable has evidence.
- [ ] XML/catalog/policy validator passes.
- [ ] Graph validator passes.
- [ ] Manifest validates against its schema.
- [ ] Unsupported features return evidence requests, not plausible XML.
- [ ] Runtime import/execution delegated to `tasker-capability-runtime`.
