"""Portable verification for the canonical assisted-project roundtrip pair."""
import json
import subprocess
import sys
import unittest
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_roundtrip_evidence.py"
EVIDENCE_MANIFEST = REPO / "fixtures/exported/project-renderer-gate-v1/roundtrip-evidence.manifest.json"


class VerifyRoundtripEvidenceTests(unittest.TestCase):
    def test_canonical_pair_has_verified_exact_pass(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)],
            cwd=REPO,
            text=True,
            capture_output=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertEqual(result["verdict"], "EXACT_PASS")
        self.assertTrue(result["byte_equal"])
        self.assertEqual(result["candidate"]["sha256"], result["reexport"]["sha256"])
        self.assertEqual(result["candidate"]["sha256"], "0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1")

    def test_portable_manifest_records_provenance_without_external_dependency(self):
        manifest = json.loads(EVIDENCE_MANIFEST.read_text())
        self.assertEqual(manifest["run_id"], "run-20260728T004816Z-43023f")
        self.assertEqual(manifest["candidate"]["sha256"], "0ec73026b83dedade63905d74bb3f3e502f7dc6e10f617d58232dbd03b3e3ba1")
        self.assertEqual(manifest["reexport"]["sha256"], manifest["candidate"]["sha256"])
        self.assertTrue(manifest["external_source"]["provenance_only"])
