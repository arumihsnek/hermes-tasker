import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from xml_shape_contracts import validate_shape_contract, resolve_shape_contract

def test_no_unbacked_contracts_are_authorized():
    assert resolve_shape_contract("action", "548") is None

def test_contract_requires_evidence_and_rejects_duplicate_order():
    data={"kind":"action","identifier":"548","evidence":{},"tag":"Action","required_attributes":[],"optional_attributes":[],"forbidden_attributes":[],"children_order":["code","code"],"mutable_fields":[],"fixed_fields":[],"variants":[],"tasker_version":"6.7.6-beta"}
    errors=validate_shape_contract(data)
    assert "contract without evidence" in errors
    assert "duplicate child order" in errors
