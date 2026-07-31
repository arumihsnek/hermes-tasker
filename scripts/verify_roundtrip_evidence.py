#!/usr/bin/env python3
"""Verify the portable byte-exact Project roundtrip evidence pair."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

from compare_tasker_roundtrip import compare


REPO = Path(__file__).resolve().parents[1]
EXPECTED_SHA256 = "0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1"
DEFAULT_CANDIDATE = REPO / "fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml"
DEFAULT_REEXPORT = REPO / "fixtures/exported/project-renderer-gate-v1/artifact.reexported.prj.xml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", nargs="?", type=Path, default=DEFAULT_CANDIDATE)
    parser.add_argument("reexport", nargs="?", type=Path, default=DEFAULT_REEXPORT)
    args = parser.parse_args()
    if not args.candidate.is_file() or not args.reexport.is_file():
        print(json.dumps({"verdict": "MISSING_EVIDENCE"}, sort_keys=True))
        return 1
    result = compare(args.candidate, args.reexport)
    result["candidate"] = {"path": str(args.candidate), "sha256": sha256(args.candidate)}
    result["reexport"] = {"path": str(args.reexport), "sha256": sha256(args.reexport)}
    result["byte_equal"] = result["candidate"]["sha256"] == result["reexport"]["sha256"]
    print(json.dumps(result, sort_keys=True))
    return int(not (
        result["verdict"] == "EXACT_PASS"
        and result["byte_equal"]
        and result["candidate"]["sha256"] == EXPECTED_SHA256
    ))


if __name__ == "__main__":
    sys.exit(main())
