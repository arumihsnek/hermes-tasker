"""Shared evidence-only helpers for Tasker artifact tools."""
from __future__ import annotations

import json
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = SKILL_DIR / "data"


def load_catalog(kind: str) -> dict:
    path = DATA_DIR / f"{kind}.json"
    if not path.exists():
        raise FileNotFoundError(
            f"Missing normalized catalog: {path}. Run scripts/normalize_catalogs.py "
            "with the official source before generating artifacts."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def action_by_code(code: int) -> dict | None:
    for item in load_catalog("actions")["items"]:
        if item["code"] == code:
            return item
    return None


def context_by_code(kind: str, code: int) -> dict | None:
    filename = "event-contexts" if kind == "Event" else "state-contexts"
    for item in load_catalog(filename)["items"]:
        if item["code"] == code:
            return item
    return None


def json_result(ok: bool, **data: object) -> str:
    return json.dumps({"ok": ok, **data}, ensure_ascii=False, indent=2)
