#!/usr/bin/env python3
"""Regenerate the Runtime Echo v1 derived candidate into a supplied directory."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from runtime_echo import RuntimeEchoInvocation, RuntimeEchoSpec


REPO = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_candidate(spec_path: Path, output_dir: Path) -> dict[str, Path]:
    spec = RuntimeEchoSpec.from_mapping(json.loads(spec_path.read_text(encoding="utf-8")))
    invocation = RuntimeEchoInvocation.from_spec(spec)
    output_dir.mkdir(parents=True, exist_ok=True)
    ir_path = output_dir / "invocation.json"
    request_path = output_dir / "renderer-request.json"
    ir_path.write_text(invocation.to_json() + "\n", encoding="utf-8")
    request_path.write_text(json.dumps(invocation.to_legacy_tasker_request(), sort_keys=True) + "\n", encoding="utf-8")
    rendered = output_dir / "rendered"
    result = subprocess.run(
        [sys.executable, str(REPO / "scripts/generate_tasker_artifact.py"), "--request", str(request_path), "--output-dir", str(rendered)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stdout or result.stderr)
    response = json.loads(result.stdout)
    xml_path = Path(response["artifact_path"])
    output_xml = output_dir / "artifact.tsk.xml"
    output_xml.write_bytes(xml_path.read_bytes() + b"\n")
    manifest = {
        "capability": spec.capability,
        "command_id": spec.command_id,
        "expected_result": invocation.expected_result(),
        "generator": "scripts/regenerate_runtime_echo_candidate.py",
        "hashes": {"ir_sha256": digest(ir_path), "spec_sha256": digest(spec_path), "xml_sha256": digest(output_xml)},
        "result_token": spec.result_token,
        "schema_version": "runtime-echo-candidate-v1",
        "validation_commands": [
            "python3 scripts/verify_runtime_echo_candidate.py",
            "python3 scripts/validate_tasker_xml.py fixtures/candidates/runtime-echo-v1/artifact.tsk.xml --policy",
            "python3 scripts/validate_tasker_graph.py fixtures/candidates/runtime-echo-v1/artifact.tsk.xml",
        ],
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    return {"ir": ir_path, "xml": output_xml, "manifest": manifest_path}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, default=REPO / "fixtures/specs/runtime-echo-v1/spec.json")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    paths = write_candidate(args.spec, args.output_dir)
    print(json.dumps({key: str(value) for key, value in sorted(paths.items())}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
