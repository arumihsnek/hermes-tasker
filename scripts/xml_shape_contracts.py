"""Loader for small, evidence-backed XML shape contracts."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = ROOT / "data" / "xml-shape-contracts"

def load_shape_contract(path: str | Path) -> dict[str, Any]:
    target = ROOT / path if not Path(path).is_absolute() else Path(path)
    data = json.loads(target.read_text(encoding="utf-8"))
    errors = validate_shape_contract(data)
    if errors: raise ValueError("invalid XML shape contract: " + "; ".join(errors))
    return data

def resolve_shape_contract(kind: str, identifier: str, variant: str | None = None) -> dict[str, Any] | None:
    for path in sorted(CONTRACT_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("kind") == kind and str(data.get("identifier")) == str(identifier) and (variant is None or variant in data.get("variants", [])):
            return data
    return None

def validate_shape_contract(data: dict[str, Any]) -> list[str]:
    errors=[]
    required={"kind","identifier","evidence","tag","required_attributes","optional_attributes","forbidden_attributes","children_order","mutable_fields","fixed_fields","variants","tasker_version"}
    errors.extend(f"missing {key}" for key in sorted(required-set(data)))
    if set(data.get("mutable_fields", [])) & set(data.get("fixed_fields", [])): errors.append("mutable/fixed overlap")
    evidence=data.get("evidence", {})
    if not evidence.get("source") or not evidence.get("fixture"): errors.append("contract without evidence")
    if len(data.get("children_order", [])) != len(set(data.get("children_order", []))): errors.append("duplicate child order")
    return errors
