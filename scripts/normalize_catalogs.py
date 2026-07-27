#!/usr/bin/env python3
"""Normalize the official Tasker AI generator catalogs without inventing fields."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SOURCE_LABELS = {
    "Event Context Catalog Data": "event-contexts",
    "State Context Catalog Data": "state-contexts",
    "Action Catalog Data": "actions",
    "Tasker Input Dialog Types Catalog JSON": "dialog-types",
    "Built-in Variable Catalog": "built-in-variables",
}


def find_payloads(source: Path) -> dict[str, tuple[int, dict]]:
    current = None
    found: dict[str, tuple[int, dict]] = {}
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        heading = line.strip()
        for label, key in SOURCE_LABELS.items():
            if heading.endswith(f"**{label}:**") and heading[:1].isdigit():
                current = key
                break
        stripped = line.strip()
        if current and stripped.startswith("*   `{") and stripped.endswith("}`"):
            payload = stripped[len("*   `"):-1]
            try:
                found[current] = (line_number, json.loads(payload))
            except json.JSONDecodeError as error:
                raise ValueError(f"Invalid official JSON at line {line_number}: {error}") from error
    missing = set(SOURCE_LABELS.values()) - set(found)
    if missing:
        raise ValueError(f"Missing official catalog payload(s): {', '.join(sorted(missing))}")
    return found


def normalize_component(item: dict, catalog: str, line: int) -> dict:
    params = item.get("p", {}).get("p", [])
    outputs = item.get("o", {}).get("v", [])
    return {
        "kind": "action" if catalog == "actions" else "event_context" if catalog == "event-contexts" else "state_context",
        "code": item["c"],
        "name": item["n"],
        "arguments": [
            {
                "position": param["u"],
                "xml_type": param["a"],
                "name": param.get("m", ""),
                "constraints": param.get("s", ""),
                "description": param.get("d", ""),
            }
            for param in params
        ],
        "output_variables": [
            {"name": output["n"], "description": output.get("d", "")}
            for output in outputs
        ],
        "tasker_version": "6.7.6-beta",
        "source": {"authority": "official_catalog", "file": "tasker_ai_system_instructions.txt", "line": line},
    }


def write_json(path: Path, content: dict) -> None:
    path.write_text(json.dumps(content, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    found = find_payloads(args.source)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for key in ("event-contexts", "state-contexts", "actions"):
        line, payload = found[key]
        raw_items = payload["c"] if key != "actions" else payload["a"]
        write_json(args.output_dir / f"{key}.json", {
            "schema": "hermes-tasker-catalog/v1",
            "source": {"authority": "official_catalog", "file": str(args.source), "line": line},
            "items": [normalize_component(item, key, line) for item in raw_items],
        })
    line, payload = found["dialog-types"]
    write_json(args.output_dir / "dialog-types.json", {"schema": "hermes-tasker-catalog/v1", "source": {"authority": "official_catalog", "file": str(args.source), "line": line}, "items": payload["d"]})
    line, payload = found["built-in-variables"]
    write_json(args.output_dir / "built-in-variables.json", {"schema": "hermes-tasker-catalog/v1", "source": {"authority": "official_catalog", "file": str(args.source), "line": line}, "items": payload["b"]})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
