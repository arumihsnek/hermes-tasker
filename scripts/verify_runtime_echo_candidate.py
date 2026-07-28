#!/usr/bin/env python3
"""Verify the immutable Runtime Echo v1 static candidate."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from regenerate_runtime_echo_candidate import REPO, write_candidate


ROOT = REPO
SPEC = ROOT / "fixtures/specs/runtime-echo-v1/spec.json"
IR = ROOT / "fixtures/ir/runtime-echo-v1/invocation.json"
XML = ROOT / "fixtures/candidates/runtime-echo-v1/artifact.tsk.xml"
MANIFEST = ROOT / "fixtures/manifests/runtime-echo-v1/manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fail(reason: str) -> int:
    print(json.dumps({"gate": "RUNTIME_ECHO_STATIC_GATE", "reason": reason, "verdict": "FAIL"}, sort_keys=True))
    return 1


def main() -> int:
    if not all(path.is_file() for path in (SPEC, IR, XML, MANIFEST)):
        return fail("missing candidate input")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = manifest.get("hashes", {})
    tracked = {"spec_sha256": SPEC, "ir_sha256": IR, "xml_sha256": XML}
    for key, path in tracked.items():
        if expected.get(key) != sha256(path):
            return fail(f"hash mismatch: {key}")
    with tempfile.TemporaryDirectory() as directory:
        generated = write_candidate(SPEC, Path(directory))
        for key, tracked_path in (("ir", IR), ("xml", XML), ("manifest", MANIFEST)):
            if generated[key].read_bytes() != tracked_path.read_bytes():
                return fail(f"regeneration mismatch: {key}")
    for command in (
        [sys.executable, str(ROOT / "scripts/validate_tasker_xml.py"), str(XML), "--policy"],
        [sys.executable, str(ROOT / "scripts/validate_tasker_graph.py"), str(XML)],
    ):
        if subprocess.run(command, text=True, capture_output=True).returncode:
            return fail("validator failure")
    print(json.dumps({"gate": "RUNTIME_ECHO_STATIC_GATE", "verdict": "PASS"}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
