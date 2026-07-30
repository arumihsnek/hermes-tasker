"""Tests for the Tasker XML roundtrip comparator."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"

CANDIDATE = SKILL_DIR / "fixtures/candidates/project-renderer-gate-v1/artifact.prj.xml"


def run_script(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=SKILL_DIR,
    )


def _load_result(proc) -> dict:
    """Parse comparator JSON from stdout."""
    return json.loads(proc.stdout)


# ---------------------------------------------------------------------------
# Synthetic XML builders
# ---------------------------------------------------------------------------

_BASE_XML = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    "<TaskerData sr=\"\" dvi=\"1\" tv=\"6.7.6-beta\">\n"
    "  <Profile sr=\"prof1001\" ve=\"2\">\n"
    "    <cdate>1784991726196</cdate>\n"
    "    <edate>1784991726196</edate>\n"
    "    <flags>40</flags>\n"
    "    <id>1001</id>\n"
    "    <mid0>2001</mid0>\n"
    "    <nme>Gate Test Profile</nme>\n"
    "    <Event>\n"
    "      <code>599</code>\n"
    "      <pri>0</pri>\n"
    "      <Str sr=\"arg0\" ve=\"3\">com.example.TEST</Str>\n"
    "      <Int sr=\"arg1\" val=\"0\" />\n"
    "      <Int sr=\"arg2\" val=\"0\" />\n"
    "      <Str sr=\"arg3\" ve=\"3\" />\n"
    "      <Str sr=\"arg4\" ve=\"3\" />\n"
    "    </Event>\n"
    "  </Profile>\n"
    "  <Project sr=\"proj0\" ve=\"2\">\n"
    "    <cdate>1784991726196</cdate>\n"
    "    <id>a1b2c3d4-e5f6-7890-abcd-ef1234567890</id>\n"
    "    <name>Project Renderer Gate v1</name>\n"
    "    <pids>1001</pids>\n"
    "    <tids>2001</tids>\n"
    "  </Project>\n"
    "  <Task sr=\"task2001\">\n"
    "    <cdate>1785182236814</cdate>\n"
    "    <edate>1785182236814</edate>\n"
    "    <id>2001</id>\n"
    "    <Action sr=\"act0\" ve=\"7\">\n"
    "      <code>548</code>\n"
    "      <Str sr=\"arg0\" ve=\"3\">Flash</Str>\n"
    "      <Int sr=\"arg1\" val=\"0\" />\n"
    "      <Int sr=\"arg2\" val=\"1\" />\n"
    "      <Str sr=\"arg3\" ve=\"3\" />\n"
    "      <Str sr=\"arg4\" ve=\"3\" />\n"
    "      <Str sr=\"arg5\" ve=\"3\" />\n"
    "      <Str sr=\"arg6\" ve=\"3\" />\n"
    "      <Str sr=\"arg7\" ve=\"3\" />\n"
    "      <Str sr=\"arg8\" ve=\"3\" />\n"
    "      <Int sr=\"arg9\" val=\"1\" />\n"
    "      <Str sr=\"arg10\" ve=\"3\" />\n"
    "      <Int sr=\"arg11\" val=\"1\" />\n"
    "      <Int sr=\"arg12\" val=\"0\" />\n"
    "      <Str sr=\"arg13\" ve=\"3\" />\n"
    "      <Int sr=\"arg14\" val=\"0\" />\n"
    "      <Str sr=\"arg15\" ve=\"3\" />\n"
    "    </Action>\n"
    "  </Task>\n"
    "</TaskerData>"
)

_INDENT_NONE = (
    "<?xml version='1.0' encoding='utf-8'?>\n"
    "<TaskerData sr=\"\" dvi=\"1\" tv=\"6.7.6-beta\">\n"
    "<Profile sr=\"prof1001\" ve=\"2\">\n"
    "<cdate>1784991726196</cdate>\n"
    "<edate>1784991726196</edate>\n"
    "<flags>40</flags>\n"
    "<id>1001</id>\n"
    "<mid0>2001</mid0>\n"
    "<nme>Gate Test Profile</nme>\n"
    "<Event>\n"
    "<code>599</code>\n"
    "<pri>0</pri>\n"
    "<Str sr=\"arg0\" ve=\"3\">com.example.TEST</Str>\n"
    "<Int sr=\"arg1\" val=\"0\" />\n"
    "<Int sr=\"arg2\" val=\"0\" />\n"
    "<Str sr=\"arg3\" ve=\"3\" />\n"
    "<Str sr=\"arg4\" ve=\"3\" />\n"
    "</Event>\n"
    "</Profile>\n"
    "<Project sr=\"proj0\" ve=\"2\">\n"
    "<cdate>1784991726196</cdate>\n"
    "<id>a1b2c3d4-e5f6-7890-abcd-ef1234567890</id>\n"
    "<name>Project Renderer Gate v1</name>\n"
    "<pids>1001</pids>\n"
    "<tids>2001</tids>\n"
    "</Project>\n"
    "<Task sr=\"task2001\">\n"
    "<cdate>1785182236814</cdate>\n"
    "<edate>1785182236814</edate>\n"
    "<id>2001</id>\n"
    "<Action sr=\"act0\" ve=\"7\">\n"
    "<code>548</code>\n"
    "<Str sr=\"arg0\" ve=\"3\">Flash</Str>\n"
    "<Int sr=\"arg1\" val=\"0\" />\n"
    "<Int sr=\"arg2\" val=\"1\" />\n"
    "<Str sr=\"arg3\" ve=\"3\" />\n"
    "<Str sr=\"arg4\" ve=\"3\" />\n"
    "<Str sr=\"arg5\" ve=\"3\" />\n"
    "<Str sr=\"arg6\" ve=\"3\" />\n"
    "<Str sr=\"arg7\" ve=\"3\" />\n"
    "<Str sr=\"arg8\" ve=\"3\" />\n"
    "<Int sr=\"arg9\" val=\"1\" />\n"
    "<Str sr=\"arg10\" ve=\"3\" />\n"
    "<Int sr=\"arg11\" val=\"1\" />\n"
    "<Int sr=\"arg12\" val=\"0\" />\n"
    "<Str sr=\"arg13\" ve=\"3\" />\n"
    "<Int sr=\"arg14\" val=\"0\" />\n"
    "<Str sr=\"arg15\" ve=\"3\" />\n"
    "</Action>\n"
    "</Task>\n"
    "</TaskerData>"
)

_TASK_BLOCK = (
    "  <Task sr=\"task2001\">\n"
    "    <cdate>1785182236814</cdate>\n"
    "    <edate>1785182236814</edate>\n"
    "    <id>2001</id>\n"
    "    <Action sr=\"act0\" ve=\"7\">\n"
    "      <code>548</code>\n"
    "      <Str sr=\"arg0\" ve=\"3\">Flash</Str>\n"
    "      <Int sr=\"arg1\" val=\"0\" />\n"
    "      <Int sr=\"arg2\" val=\"1\" />\n"
    "      <Str sr=\"arg3\" ve=\"3\" />\n"
    "      <Str sr=\"arg4\" ve=\"3\" />\n"
    "      <Str sr=\"arg5\" ve=\"3\" />\n"
    "      <Str sr=\"arg6\" ve=\"3\" />\n"
    "      <Str sr=\"arg7\" ve=\"3\" />\n"
    "      <Str sr=\"arg8\" ve=\"3\" />\n"
    "      <Int sr=\"arg9\" val=\"1\" />\n"
    "      <Str sr=\"arg10\" ve=\"3\" />\n"
    "      <Int sr=\"arg11\" val=\"1\" />\n"
    "      <Int sr=\"arg12\" val=\"0\" />\n"
    "      <Str sr=\"arg13\" ve=\"3\" />\n"
    "      <Int sr=\"arg14\" val=\"0\" />\n"
    "      <Str sr=\"arg15\" ve=\"3\" />\n"
    "    </Action>\n"
    "  </Task>\n"
)


class TestCompareTaskerRoundtrip(unittest.TestCase):
    """14 minimum tests for the roundtrip comparator."""

    def _compare(self, candidate_xml: str, reexport_xml: str) -> dict:
        """Write XMLs to temp files and run comparator."""
        with tempfile.TemporaryDirectory() as tmp:
            cand = Path(tmp) / "candidate.xml"
            rexp = Path(tmp) / "reexport.xml"
            cand.write_text(candidate_xml, encoding="utf-8")
            rexp.write_text(reexport_xml, encoding="utf-8")
            result = run_script("compare_tasker_roundtrip.py", cand, rexp)
            self.assertEqual(result.returncode, 0, result.stderr)
            return _load_result(result)

    # --- Test 1: Identical files ---
    def test_identical_files_exact_pass(self):
        """Identical files → EXACT_PASS, byte_equal=true."""
        cand = CANDIDATE.read_text(encoding="utf-8")
        result = self._compare(cand, cand)
        self.assertTrue(result["custody"]["byte_equal"])
        self.assertEqual(result["verdict"], "EXACT_PASS")

    # --- Test 2: Indentation differs ---
    def test_indentation_differs(self):
        """Only indentation differs → byte_equal=false, not SEMANTIC_FAIL."""
        result = self._compare(_BASE_XML, _INDENT_NONE)
        self.assertFalse(result["custody"]["byte_equal"])
        self.assertNotEqual(result["verdict"], "SEMANTIC_FAIL")
        serial_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "serialization_difference"]
        self.assertGreater(len(serial_diffs), 0,
                           "Expected at least one serialization_difference")

    # --- Test 3: Attributes reordered ---
    def test_attributes_reordered(self):
        """Attribute order changed → serialization_difference."""
        # Swap sr and dvi attributes on TaskerData
        rexp = _BASE_XML.replace(
            '<TaskerData sr="" dvi="1" tv="6.7.6-beta">',
            '<TaskerData dvi="1" sr="" tv="6.7.6-beta">',
        )
        result = self._compare(_BASE_XML, rexp)
        serial_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "serialization_difference"]
        self.assertGreater(len(serial_diffs), 0,
                           "Expected serialization_difference for attribute reordering")

    # --- Test 4: Project ID changed ---
    def test_project_id_changed(self):
        """Project UUID changed → semantic_difference."""
        rexp = _BASE_XML.replace(
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
            "deadbeef-1234-5678-abcd-ef1234567890",
        )
        result = self._compare(_BASE_XML, rexp)
        sem_diffs = [d for d in result["differences"]
                     if d["provisional_class"] == "semantic_difference"]
        self.assertGreater(len(sem_diffs), 0,
                           "Expected semantic_difference for project ID change")

    # --- Test 5: Task ID changed AND references updated ---
    def test_task_id_changed_with_references(self):
        """Task ID changed + tids/mid0 updated → structural_difference (IDs moved)."""
        rexp = (
            _BASE_XML
            .replace('sr="task2001"', 'sr="task3001"')
            .replace("<id>2001</id>", "<id>3001</id>")
            .replace("<mid0>2001</mid0>", "<mid0>3001</mid0>")
            .replace("<tids>2001</tids>", "<tids>3001</tids>")
        )
        result = self._compare(_BASE_XML, rexp)
        sem_diffs = [d for d in result["differences"]
                     if d["provisional_class"] == "semantic_difference"]
        struct_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "structural_difference"]
        self.assertEqual(len(sem_diffs), 0,
                         "No semantic differences expected for consistent ID move")
        self.assertGreater(len(struct_diffs), 0,
                           "Expected structural_difference for consistent ID move")

    # --- Test 6: Task ID changed WITHOUT updating mid0 ---
    def test_task_id_changed_without_mid0(self):
        """Task ID changed but mid0 not updated → semantic_difference (broken ref)."""
        rexp = (
            _BASE_XML
            .replace('sr="task2001"', 'sr="task3001"')
            .replace("<id>2001</id>", "<id>3001</id>")
            # mid0 stays at 2001 — not updated
        )
        result = self._compare(_BASE_XML, rexp)
        sem_diffs = [d for d in result["differences"]
                     if d["provisional_class"] == "semantic_difference"]
        self.assertGreater(len(sem_diffs), 0,
                           "Expected semantic_difference for broken reference")

    # --- Test 7: Action code changed ---
    def test_action_code_changed(self):
        """Action code changed (548→547) → semantic_difference."""
        rexp = _BASE_XML.replace("<code>548</code>", "<code>547</code>", 1)
        result = self._compare(_BASE_XML, rexp)
        sem_diffs = [d for d in result["differences"]
                     if d["provisional_class"] == "semantic_difference"]
        self.assertGreater(len(sem_diffs), 0,
                           "Expected semantic_difference for action code change")

    # --- Test 8: Flash argument changed ---
    def test_flash_argument_changed(self):
        """Flash argument (arg0 value) changed → semantic_difference."""
        rexp = _BASE_XML.replace(">Flash<", ">Hello World<", 1)
        result = self._compare(_BASE_XML, rexp)
        sem_diffs = [d for d in result["differences"]
                     if d["provisional_class"] == "semantic_difference"]
        self.assertGreater(len(sem_diffs), 0,
                           "Expected semantic_difference for argument value change")

    # --- Test 9: Task omitted ---
    def test_task_omitted(self):
        """Task element omitted → structural_difference."""
        rexp = _BASE_XML.replace(_TASK_BLOCK, "")
        result = self._compare(_BASE_XML, rexp)
        struct_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "structural_difference"]
        self.assertGreater(len(struct_diffs), 0,
                           "Expected structural_difference for omitted task")

    # --- Test 10: Task duplicated ---
    def test_task_duplicated(self):
        """Task element duplicated → structural_difference."""
        # Insert duplicate task before closing </TaskerData>
        rexp = _BASE_XML.replace("</TaskerData>", _TASK_BLOCK + "</TaskerData>")
        result = self._compare(_BASE_XML, rexp)
        struct_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "structural_difference"]
        self.assertGreater(len(struct_diffs), 0,
                           "Expected structural_difference for duplicated task")

    # --- Test 11: tids empty ---
    def test_tids_empty(self):
        """Project tids changed to empty → structural_difference."""
        rexp = _BASE_XML.replace("<tids>2001</tids>", "<tids></tids>")
        result = self._compare(_BASE_XML, rexp)
        all_diffs = result["differences"]
        self.assertGreater(len(all_diffs), 0,
                           "Expected differences for empty tids")

    # --- Test 12: Incorrect nesting ---
    def test_incorrect_nesting(self):
        """Project/Profile/Task nested incorrectly → structural_difference."""
        rexp = (
            "<?xml version='1.0' encoding='utf-8'?>\n"
            '<TaskerData sr="" dvi="1" tv="6.7.6-beta">\n'
            '  <Profile sr="prof1001" ve="2">\n'
            "    <id>1001</id>\n"
            "    <mid0>2001</mid0>\n"
            "    <nme>Gate Test Profile</nme>\n"
            "    <Event>\n"
            "      <code>599</code>\n"
            "      <pri>0</pri>\n"
            '      <Str sr="arg0" ve="3">com.example.TEST</Str>\n'
            '      <Int sr="arg1" val="0" />\n'
            '      <Int sr="arg2" val="0" />\n'
            "    </Event>\n"
            "  </Profile>\n"
            '  <Project sr="proj0" ve="2">\n'
            '    <id>a1b2c3d4-e5f6-7890-abcd-ef1234567890</id>\n'
            "    <name>Project Renderer Gate v1</name>\n"
            "    <pids>1001</pids>\n"
            "    <tids>2001</tids>\n"
            '    <Task sr="task2001">\n'
            "      <id>2001</id>\n"
            '      <Action sr="act0" ve="7">\n'
            "        <code>548</code>\n"
            '        <Str sr="arg0" ve="3">Flash</Str>\n'
            '        <Int sr="arg1" val="0" />\n'
            '        <Int sr="arg2" val="1" />\n'
            "      </Action>\n"
            "    </Task>\n"
            "  </Project>\n"
            "</TaskerData>"
        )
        result = self._compare(_BASE_XML, rexp)
        struct_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "structural_difference"]
        self.assertGreater(len(struct_diffs), 0,
                           "Expected structural_difference for incorrect nesting")

    # --- Test 13: XML malformed ---
    def test_xml_malformed(self):
        """Malformed XML → UNPARSABLE."""
        result = self._compare(_BASE_XML, "<invalid")
        self.assertEqual(result["verdict"], "UNPARSABLE")

    # --- Test 14: Optional fields added by Tasker ---
    def test_optional_fields_added(self):
        """Optional fields (e.g., <note>) added by Tasker → serialization_difference."""
        rexp = _BASE_XML.replace(
            "    <id>2001</id>",
            '    <id>2001</id>\n    <note>Added by Tasker</note>',
        )
        result = self._compare(_BASE_XML, rexp)
        serial_diffs = [d for d in result["differences"]
                        if d["provisional_class"] == "serialization_difference"]
        self.assertGreater(len(serial_diffs), 0,
                           "Expected serialization_difference for optional fields")


if __name__ == "__main__":
    unittest.main()
