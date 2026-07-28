#!/usr/bin/env python3
from __future__ import annotations
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from xml_support import ROOT, load_support_matrix, validate_support_entry

def main() -> int:
    errors: list[str] = []
    try: data = load_support_matrix()
    except Exception as exc: print(f"XML_SUPPORT_MATRIX_FAIL: {exc}"); return 2
    if not data.get("tasker_version"): errors.append("missing tasker_version")
    seen: set[tuple[str,str]] = set()
    for entry in data.get("entries", []):
        key=(entry.get("kind",""), str(entry.get("identifier","")))
        if key in seen: errors.append(f"duplicate support entry {key}")
        seen.add(key); errors.extend(f"{key}: {e}" for e in validate_support_entry(entry))
        for p, expected in zip(entry.get("fixture_paths", []), entry.get("fixture_hashes", [])):
            target=ROOT / p
            if not target.exists(): errors.append(f"{key}: missing fixture {p}")
            elif hashlib.sha256(target.read_bytes()).hexdigest() != expected: errors.append(f"{key}: fixture hash mismatch {p}")
        for field in ("contract_path",):
            if entry.get(field) and not (ROOT / entry[field]).exists(): errors.append(f"{key}: missing {field}")
        for p in entry.get("golden_paths", []):
            if not (ROOT / p).exists(): errors.append(f"{key}: missing golden {p}")
    if errors:
        print("XML_SUPPORT_MATRIX_FAIL")
        print("\n".join(f"- {e}" for e in errors)); return 1
    print(f"XML_SUPPORT_MATRIX_PASS entries={len(data.get('entries', []))}"); return 0
if __name__ == "__main__": raise SystemExit(main())
