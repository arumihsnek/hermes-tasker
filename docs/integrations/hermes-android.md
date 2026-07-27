# Integration: hermes-tasker ↔ hermes-android

This document defines the contract boundary between the standalone Tasker toolchain (`hermes-tasker`) and the Android transport layer (`hermes-android`).

## Ownership Boundary

| Layer | Repository | Responsibilities |
|---|---|---|
| **Artifact Production** | `hermes-tasker` | Generate Tasks, Profiles, Projects from typed specs; catalog-backed XML rendering; XML policy validation; graph structural validation; fixture-backed contracts; candidate generation; roundtrip semantic comparison |
| **Transport & Runtime** | `hermes-android` | Android device communication (Bridge, ADB, Shizuku); assisted visual import orchestration; human confirmation flow; Pixel interaction; device evidence collection; Tasker re-export retrieval; result-channel and Bridge telemetry; runtime execution |

## Artifact/Manifest Boundary

`hermes-tasker` produces:

1. **Artifact XML** (`.tsk.xml`, `.prf.xml`, `.prj.xml`) — the Tasker-importable file
2. **Manifest JSON** — metadata for transport and confirmation:
   ```json
   {
     "artifact_type": "project",
     "artifact_path": "out/artifact.prj.xml",
     "manifest_path": "out/artifact.manifest.json",
     "validation": {
       "xml_policy": "PASS",
       "graph": "PASS",
       "catalog": "PASS"
     },
     "import_method": "assisted_visual",
     "confirmation_required": true,
     "effects": ["ui.flash"],
     "requirements": {"tasker": true, "accessibility": true, "root": false}
   }
   ```

`hermes-android` consumes:

- The artifact XML file path
- The manifest (especially `import_method`, `confirmation_required`, `requirements`)
- Uses Hermes Bridge as the **preferred** transport for delivery

## Bridge-Preferred Workflow

```
┌─────────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│   hermes-tasker     │     │   hermes-android     │     │      Pixel 8        │
│                     │     │                      │     │                     │
│  1. Generate XML    │────▶│  2. POST /intent     │────▶│  3. Tasker Import   │
│  2. Validate        │     │     (assisted)       │     │     UI              │
│  3. Emit manifest   │     │  4. Human confirm    │     │  5. Re-export       │
└─────────────────────┘     │  5. GET /screen      │     └─────────────────────┘
                            │  6. Roundtrip compare│
                            └──────────────────────┘
```

1. `hermes-tasker` generates artifact + manifest (static validation PASS)
2. `hermes-android` delivers artifact to Pixel via Hermes Bridge (`POST /intent` with `ACTION_VIEW` on `text/xml`)
3. Tasker Import UI appears — **human confirms** (mandatory per manifest)
4. `hermes-android` monitors import via Bridge screen API
5. `hermes-android` retrieves re-export via Bridge (`/screen` or `/shell` backup)
6. `hermes-android` invokes `hermes-tasker`'s `compare_tasker_export.py` for semantic roundtrip analysis

## Alternative Transports

The artifact XML is a standard Tasker `.prj.xml` / `.tsk.xml` / `.prf.xml`. It can be imported via:

- **Manual**: Copy to device → Tasker → Import
- **ADB**: `adb push` + `am broadcast -a android.intent.action.VIEW -d file://... -t text/xml`
- **Any file transfer** + Tasker's Import UI

**The manifest is optional for alternative transports** but recommended for confirmation and requirements awareness.

## Roundtrip Ownership

| Phase | Owner | Tool |
|---|---|---|
| Import delivery | `hermes-android` | Bridge, ADB, manual |
| Human confirmation | `hermes-android` | UI orchestration |
| Re-export retrieval | `hermes-android` | Bridge `/screen`, `/shell` backup |
| Semantic comparison | `hermes-tasker` | `compare_tasker_export.py` |
| Evidence recording | `hermes-android` | `docs/evidence/` |

## Repository Links

- `hermes-tasker`: https://github.com/arumihsnek/hermes-tasker
- `hermes-android`: https://github.com/hermes-android/hermes-android (internal)

## Import Method Values

| Value | Meaning | Confirmation |
|---|---|---|
| `assisted_visual` | Hermes Bridge delivers, Tasker Import UI shown, human taps "Import" | Required |
| `adb_broadcast` | ADB `am broadcast` with VIEW intent | Required (UI still appears) |
| `manual` | User copies file and uses Tasker Import manually | Required (UI) |
| `auto_bridge` | **NOT SUPPORTED** — no fully automated Tasker import exists | N/A |

## Confirmation Flow

The manifest field `confirmation_required: true` means:
- A human **must** explicitly tap "Import" in Tasker's UI
- No automated bypass exists on Android 14+ (cross-app broadcasts blocked)
- `hermes-android` must wait for confirmation before proceeding

## Version Compatibility

- `hermes-tasker` targets: **Tasker 6.7.6-beta**
- `hermes-android` tested on: **Pixel 8, Android 14**
- Hermes Bridge: **v0.4.0-fork** (relay + BroadcastReceiver)

## Related Documentation

- `hermes-tasker/README.md` — Toolchain overview
- `hermes-tasker/references/project-xml-contract.md` — Project XML structure
- `hermes-tasker/references/artifact-selection.md` — Artifact type decision
- `hermes-android` Bridge API docs (in hermes-android repo)