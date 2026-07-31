# TASKER_PROJECT_SAFE_UPDATE_GATE_V1 — Project Plan & Checkpoints

**RUN_ID:** `run-20260730T145207Z-1785423127`
**BOARD:** `tasker-safe-update-v1`
**TENANT:** `tasker-safe-update-v1`
**STARTED_AT:** 2026-07-30T14:52:07Z

---

## Baseline Reference: Runner 2.4 (Hermes Task Runtime v2.4)

**Source artifact:** `/home/ubuntu/.hermes/cache/documents/doc_904d3961fe7b_Hermes_Task_Runtime_v2.4.prj.xml` (Tasker Project XML)

### Key Components in Runner 2.4
| Component | ID | Type | Purpose |
|-----------|----|------|---------|
| Project | `01e03660-af47-448c-ba6a-8781dd45954e` | Project | "Hermes Task Runtime v2.4" |
| Profile: Remote Task Import | 560 | Profile | Event: `com.hermes.tasker.v2.4.IMPORT_TASK` → Task 554 |
| Profile: Result Probe | 561 | Profile | Event: `com.hermes.tasker.v2.4.PROBE_RESULT` → Task 553 |
| Profile: Remote Task Runner | 562 | Profile | Event: `com.hermes.tasker.v2.4.RUN_TASK` → Task 551 |
| Task: Run Task v2.4 | 551 | Task | Main runner with validation, execution, result submission |
| Task: Capability Smoke v1 | 552 | Task | Test capability returning structured JSON |
| Task: Result Probe v2.4 | 553 | Task | Probe endpoint via ContentProvider |
| Task: Import Task v2.4 | 554 | Task | Silent Task import + deferred Profile/Project import with human confirmation |
| Task: Confirm Import v2.4 | 555 | Task | Load staged import, verify hash, open Tasker native import UI |
| Task: Capability Runtime Status v1 | 563 | Task | Diagnostics: last import/run/probe/provider-reply |

### Contracts Verified in Runner 2.4
- **Import flow:** Silent Task import (RUN_TASK → Import Task v2.4) + deferred Profile/Project import with human confirmation (Notify → Confirm Import v2.4)
- **Result channel:** ContentProvider `content://com.hermesandroid.bridge.taskerresult` method `submit_result` / `submit_progress`
- **Envelope schema:** `hermes-tasker-result/v1` with `operation: "import" | "run" | "probe"`
- **Validation:** SHA-256, XML structure, artifact type detection, prefix rules
- **Error codes:** `missing_task_name`, `task_not_allowed`, `invalid_priority`, `perform_task_failed`, `missing_return`, `validation_failed`, `import_data_failed`, `stage_failed`, `sha256_mismatch`, `pending_key_mismatch`, `unsupported_deferred_type`

---

## Phase Gates & Checkpoints

### Phase A — Discovery & Baseline (CURRENT)
| Card | Profile | Status | Gate |
|------|---------|--------|------|
| A1 — Inspeccionar Kanban, gateway y perfiles | investigator | ✅ DONE | — |
| **A2 — Localizar runner 2.4** | investigator | 🔄 RUNNING | **PHASE_A_RUNNER_2_4_BASELINE=PASS** |
| **A3 — Inspeccionar concurrencia Git** | investigator | 🔄 RUNNING | — |
| A4 — Diseñar aislamiento y bases | software-architect | ⏳ PENDING (depends on A2,A3) | — |
| A5 — Crear worktrees y evidence bundle | operator | ⏳ PENDING (depends on A4) | — |
| A6 — Revisar baseline | reviewer | ⏳ PENDING (depends on A5) | **PHASE_A_RUNNER_2_4_BASELINE=PASS** |

**Checkpoint A:** `checkpoint-phase-A.json` — after A6 ACCEPT

---

### Phase B — Contrato de Update
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| B1 — Diseñar contrato de actualización | software-architect | A6 | — |
| B2 — Contrastar con Tasker real | investigator | A6 | — |
| B3 — Diseñar candidates v1/v2 | software-architect | B1,B2 | — |
| B4 — Revisión arquitectónica | reviewer | B3 | — |
| B5 — Resolver hallazgos | software-architect | B4 | **PHASE_B_SAFE_UPDATE_CONTRACT=PASS** |

**Checkpoint B:** `checkpoint-phase-B.json`

---

### Phase C — Candidates Versionados
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| C1 — Implementar candidates | coder | B5 | — |
| C2 — Validar invariantes | coder | C1 | — |
| C3 — Regresión runner 2.4 | coder | C1 | — |
| C4 — Review agrupada | reviewer | C2,C3 | **PHASE_C_VERSIONED_CANDIDATES=PASS** |

**Checkpoint C:** `checkpoint-phase-C.json`

---

### Phase D — Inventario Instalado
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| D1 — Diseñar schema | software-architect | C4 | — |
| D2 — Implementar inventario | coder | D1 | — |
| D3 — Implementar drift detection | coder | D2 | — |
| D4 — Tests | coder | D3 | — |
| D5 — Review | reviewer | D4 | **PHASE_D_INSTALLATION_INVENTORY=PASS** |

**Checkpoint D:** `checkpoint-phase-D.json`

---

### Phase E — Update Planner
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| E1 — Diseño | software-architect | D5 | — |
| E2 — Implementación | coder | E1 | — |
| E3 — Tests positivos/negativos | coder | E2 | — |
| E4 — Review | reviewer | E3 | **PHASE_E_UPDATE_PLANNER=PASS** |

**Checkpoint E:** `checkpoint-phase-E.json`

---

### Phase F — Rollback Package
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| F1 — Diseño | software-architect | E4 | — |
| F2 — Implementación | coder | F1 | — |
| F3 — Tests | coder | F2 | — |
| F4 — Review | reviewer | F3 | **PHASE_F_ROLLBACK_PACKAGE=PASS** |

**Checkpoint F:** `checkpoint-phase-F.json`

---

### Phase G — Integración Local
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| G1 — Suite completa hermes-tasker | coder | F4 | — |
| G2 — Suite completa hermes-android | coder | F4 | — |
| G3 — XML policy + graph validator | coder | G1,G2 | — |
| G4 — Candidates v1/v2 + determinismo | coder | G3 | — |
| G5 — Inventario + drift + planner + rollback | coder | G4 | — |
| G6 — Simulación update/rollback/retirada | coder | G5 | — |
| G7 — Regresión runner 2.4 | coder | G6 | — |
| G8 — Inspección trabajo concurrente | investigator | G7 | — |
| G9 — Review independiente | reviewer | G8 | **PHASE_G_LOCAL_INTEGRATION=PASS** |

**Checkpoint G:** `checkpoint-phase-G.json` — **NO PIXEL BEFORE THIS GATE**

---

### Phase H — Preflight del Pixel
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| H1 — Verificar dispositivo (Pixel 8, Android 17, Tasker 6.7.6-beta, Shizuku UID 2000) | operator | G9 | — |
| **H_GATE — Backup nativo Tasker confirmado** | operator | H1 | **BLOCKED needs_input** |
| H2 — Auditar estado inicial (matching_projects=0, etc.) | operator | H_GATE | **PHASE_H_PIXEL_BASELINE=PASS** |

**Checkpoint H:** `checkpoint-phase-H.json`

---

### Phase I — Instalar y Probar v1
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| I1 — Transferir v1, triple SHA, URI, MIME, permisos | operator | H2 | — |
| **H_GATE — Importación v1 confirmada** | operator | I1 | **BLOCKED needs_input** |
| I2 — Auditar estructura, registrar inventario | operator | H_GATE | — |
| I3 — Activar, consumidor único, emitir comando, correlacionar | operator | I2 | — |
| I4 — Desactivar, prueba negativa, reexportar, recuperar, comparar | operator | I3 | **PHASE_I_V1_BASELINE_INSTALLED=PASS** |

**Checkpoint I:** `checkpoint-phase-I.json`

---

### Phase J — Preflight de v2
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| J1 — Observar v1, comparar inventario, plan-update, preparar rollback | operator | I4 | — |
| J2 — Registrar Project/Profiles/Tasks, IDs, referencias, pids/tids/mid0/mid1 | operator | J1 | — |
| J3 — Verificar consumidor único, v1 desactivada, expected delta | operator | J2 | **PHASE_J_V2_UPDATE_PREFLIGHT=PASS** |

**Checkpoint J:** `checkpoint-phase-J.json`

---

### Phase K — Actualizar a v2
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| **K_GATE — Actualización v2 confirmada** | operator | J3 | **BLOCKED needs_input** |
| K1 — Auditar Projects/Profiles/Tasks globales/membresías/entry-exit/consumidores | operator | K_GATE | — |
| K2 — Clasificar cambios, actualizar inventario post-observación, verificar rollback | operator | K1 | **PHASE_K_V2_UPDATE_APPLIED=PASS** |

**Checkpoint K:** `checkpoint-phase-K.json`

---

### Phase L — Runtime v2
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| L1 — Activar 1 consumidor, verificar estado, emitir comando, recoger resultado | operator | K2 | — |
| L2 — Correlacionar, verificar comportamiento v2, ausencia v1 | operator | L1 | — |
| L3 — Desactivar, prueba negativa, reexportar, recuperar, comparar | operator | L2 | **PHASE_L_V2_RUNTIME=PASS** |

**Checkpoint L:** `checkpoint-phase-L.json`

---

### Phase M — Rollback a v1
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| **M_GATE — Rollback a v1 confirmado** | operator | L3 | **BLOCKED needs_input** |
| M1 — Verificar rollback package, observar v2, desactivar consumidores | operator | M_GATE | — |
| M2 — Ejecutar estrategia, auditar, verificar v1 lógica, consumidor único | operator | M1 | — |
| M3 — Runtime v1, ausencia v2, desactivar, prueba negativa, reexportar, comparar, actualizar inventario | operator | M2 | **PHASE_M_ROLLBACK_TO_V1=PASS** |

**Checkpoint M:** `checkpoint-phase-M.json`

---

### Phase N — Retirada Segura
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| **N_GATE — Retirada confirmada** | operator | M3 | **BLOCKED needs_input** |
| N1 — Backup confirmado, rollback disponible, inventario, snapshot, listas exactas, consumidores desactivados | operator | N_GATE | — |
| N2 — Project propio ausente, Profile propio ausente, Task propia ausente, Task compartida intacta, consumidor ausente, runtime action sin listener, inventario REMOVED, ningún objeto ajeno modificado | operator | N1 | — |
| N3 — Prueba negativa: matching_consumers=0, NO_MATCHED_RESULT | operator | N2 | **PHASE_N_SAFE_REMOVAL=PASS** |

**Checkpoint N:** `checkpoint-phase-N.json`

---

### Phase O — Restauración (si policy lo requiere)
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| O1 — software-architect selecciona policy: RESTORE_AFTER_REMOVAL_REQUIRED / RESTORE_FROM_BACKUP_ONLY_ON_FAILURE / REMOVAL_IS_FINAL_STATE | software-architect | N3 | — |
| **O_GATE — Restauración confirmada** | operator | O1 | **BLOCKED needs_input** (si aplica) |
| O2 — Usar rollback/backup, verificar hashes, restaurar, auditar, ausencia duplicados, runtime, desactivar, reexportar, comparar, actualizar inventario | operator | O_GATE | **PHASE_O_RESTORATION=PASS** (si aplica) |

**Checkpoint O:** `checkpoint-phase-O.json`

---

### Phase P — Documentación y Publicación
| Card | Profile | Depends On | Gate |
|------|---------|------------|------|
| P1 — Actualizar docs/roadmap: RUNNER_2_4_E2E_PASS, SAFE_UPDATE_V1_PASS, ROLLBACK_PASS, SAFE_REMOVAL_PASS, RESTORATION_PASS|NOT_REQUIRED | kanban-coordinator | O2 (or N3 if no restoration) |
| P2 — Review final | reviewer | P1 | **ACCEPT** |
| P3 — Push ramas dedicadas, abrir PRs, publicar informe sanitizado | kanban-coordinator | P2 | — |

**Final Gate:** `TASKER_PROJECT_SAFE_UPDATE_GATE_V1=PASS|FAIL|BLOCKED`

---

## Human Gates (Pre-created, Blocked)

| Gate ID | Card ID | Phase | Kind | Reason |
|---------|---------|-------|------|--------|
| H_GATE_BACKUP | t_0b73ee1e | H | needs_input | Backup nativo Tasker confirmado |
| H_GATE_IMPORT_V1 | t_b8d4812b | I | needs_input | Importación v1 en Tasker UI confirmada |
| K_GATE_UPDATE_V2 | t_6ed2e07f | K | needs_input | Actualización v2 en Tasker UI confirmada |
| M_GATE_ROLLBACK_V1 | t_2085cb2e | M | needs_input | Rollback a v1 en Tasker UI confirmado |
| N_GATE_REMOVAL | t_7ae4b3e2 | N | needs_input | Retirada segura confirmada |
| O_GATE_RESTORATION | t_a8aadbca | O | needs_input | Restauración confirmada (si policy lo requiere) |

---

## Evidence Directory Structure

```
/home/ubuntu/evidence/tasker-safe-update/<RUN_ID>/
├── kanban/
│   ├── board-initial.json
│   ├── board-final.json
│   ├── task-map.json
│   ├── card-results/
│   └── reviews/
├── provenance/
│   ├── runner-2.4-baseline.json
│   ├── repositories.json
│   ├── worktrees.json
│   └── concurrent-work.json
├── design/
│   ├── update-contract.md
│   ├── identity-model.md
│   ├── rollback-policy.md
│   ├── collision-taxonomy.md
│   └── lifecycle-state-machine.md
├── candidates/
│   ├── v1/
│   └── v2/
├── local/
│   ├── tests-tasker.json
│   ├── tests-android.json
│   ├── regression-runner-2.4.json
│   ├── update-planner-tests.json
│   └── rollback-tests.json
├── pixel/
│   ├── preflight.json
│   ├── backup.json
│   ├── initial-state/
│   ├── install-v1/
│   ├── update-v2/
│   ├── rollback-v1/
│   ├── removal/
│   └── restoration/
├── exports/
│   ├── initial/
│   ├── v1/
│   ├── v2/
│   ├── rollback/
│   └── final/
├── comparison/
│   ├── v1-install.json
│   ├── v1-to-v2.json
│   ├── v2-runtime.json
│   ├── v2-to-v1-rollback.json
│   ├── removal.json
│   └── restoration.json
└── final/
    └── final-report.md
```

---

## Final Report Required Fields

```
RUN_ID=
BOARD=
TENANT=
STARTED_AT=
FINISHED_AT=

RUNNER_2_4_TASKER_COMMIT=
RUNNER_2_4_ANDROID_COMMIT=

HERMES_TASKER_FINAL=
HERMES_ANDROID_FINAL=

DEVICE=
ANDROID_VERSION=
TASKER_VERSION=
BRIDGE_VERSION=

PHASE | STATUS | CARDS | PROFILES | COMMITS | TESTS | EVIDENCE | NOTES
...
RUNNER_2_4_REGRESSION=PASS|FAIL|BLOCKED
TASKER_PROJECT_SAFE_UPDATE_GATE_V1=PASS|FAIL|BLOCKED
FINAL_VERDICT=PASS|FAIL|BLOCKED
```

If BLOCKED:
```
BLOCK_REASON=
LAST_COMPLETED_PHASE=
LAST_COMPLETED_CARD=
SAFE_RESUME_POINT=
WORKTREES=
BRANCHES=
FILES_CHANGED=
UNCOMMITTED_STATE=
DEVICE_STATE=
INVENTORY_STATE=
REQUIRED_HUMAN_ACTION=
```

---

## Current Status (2026-07-30T14:52:07Z)

- ✅ Board created: `tasker-safe-update-v1`
- ✅ RUN_ID generated: `run-20260730T145207Z-1785423127`
- ✅ A1 completed (Kanban/gateway/profiles inspected)
- 🔄 A2 running (Runner 2.4 discovery — **this document is the baseline evidence**)
- 🔄 A3 running (Git concurrency inspection)
- ⏸️ 6 human gates created and blocked with `needs_input`
- ✅ Profile preflight PASS (all 8 required profiles exist with correct skills)
- ✅ Dispatcher pass executed (A1 done, A2/A3 running, gates blocked)

**Next:** Complete A2/A3 → A4 (software-architect) → A5 (operator) → A6 (reviewer) → PHASE_A_RUNNER_2_4_BASELINE gate