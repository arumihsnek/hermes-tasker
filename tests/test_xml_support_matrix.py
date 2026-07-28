import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from xml_support import is_render_authorized, validate_support_entry

def test_empty_matrix_is_valid_and_fail_closed():
    assert not is_render_authorized("action", "548")
    result = subprocess.run([sys.executable, "scripts/validate_xml_support_matrix.py"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

def test_catalog_only_cannot_render():
    entry = {"evidence_level":"catalog_only", "renderer_support":True, "contract_path":None, "golden_paths":[]}
    assert validate_support_entry(entry)

def test_fixed_and_mutable_overlap_is_rejected():
    entry = {"evidence_level":"renderer_golden", "renderer_support":False, "mutable_fields":["x"], "fixed_fields":["x"]}
    assert "mutable_fields and fixed_fields overlap" in validate_support_entry(entry)

def test_matrix_shape_has_required_top_level_fields():
    data = json.loads((ROOT / "data/xml-support-matrix.json").read_text())
    assert data == {"schema_version": 1, "tasker_version": "6.7.6-beta", "entries": []}
