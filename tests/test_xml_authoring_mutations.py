import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from xml_support import is_render_authorized, require_render_support

@pytest.mark.parametrize("kind,identifier,variant", [
    ("action", "548", None),
    ("event", "2080", None),
    ("plugin", "termux-tasker.run-command.v1002", None),
    ("action", "548", "invented-variant"),
])
def test_catalog_or_unbacked_variant_is_fail_closed(kind, identifier, variant):
    assert not is_render_authorized(kind, identifier, variant)
    with pytest.raises(ValueError, match="unsupported XML shape"):
        require_render_support(kind, identifier, variant)
