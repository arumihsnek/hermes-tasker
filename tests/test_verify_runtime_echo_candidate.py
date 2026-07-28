import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class RuntimeEchoCandidateTests(unittest.TestCase):
    def test_portable_static_gate_passes(self):
        result = subprocess.run(
            [sys.executable, "scripts/verify_runtime_echo_candidate.py"],
            cwd=ROOT, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"verdict": "PASS"', result.stdout)


if __name__ == "__main__":
    unittest.main()
