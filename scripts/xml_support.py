"""Fail-closed lookup for explicitly authorized XML shapes."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "data" / "xml-support-matrix.json"
RENDER_LEVELS = {"renderer_golden", "roundtrip_exact", "runtime_verified"}

def load_support_matrix(path: Path = MATRIX) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def find_support_entry(kind: str, identifier: str, path: Path = MATRIX) -> dict[str, Any] | None:
    return next((e for e in load_support_matrix(path)["entries"] if e["kind"] == kind and e["identifier"] == str(identifier)), None)

def is_render_authorized(kind: str, identifier: str, variant: str | None = None, path: Path = MATRIX) -> bool:
    entry = find_support_entry(kind, identifier, path)
    if not entry or not entry["renderer_support"] or entry["evidence_level"] not in RENDER_LEVELS:
        return False
    return variant is None or variant in entry["supported_variants"]

def require_render_support(kind: str, identifier: str, variant: str | None = None, path: Path = MATRIX) -> dict[str, Any]:
    entry = find_support_entry(kind, identifier, path)
    if not is_render_authorized(kind, identifier, variant, path):
        raise ValueError(f"unsupported XML shape: {kind}/{identifier} variant={variant!r}; catalog presence does not authorize rendering")
    return entry  # type: ignore[return-value]

def validate_support_entry(entry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if set(entry.get("mutable_fields", [])) & set(entry.get("fixed_fields", [])):
        errors.append("mutable_fields and fixed_fields overlap")
    if entry.get("renderer_support") and (entry.get("evidence_level") not in RENDER_LEVELS or not entry.get("contract_path") or not entry.get("golden_paths")):
        errors.append("renderer_support requires authorized level, contract, and golden")
    if entry.get("evidence_level") in {"catalog_only", "unsupported"} and entry.get("renderer_support"):
        errors.append("catalog_only/unsupported cannot authorize rendering")
    return errors
