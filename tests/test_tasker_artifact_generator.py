import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS = SKILL_DIR / "scripts"
SOURCE = Path("/home/ubuntu/.hermes/webui/attachments/1a70f5adaf22/tasker_ai_system_instructions.txt")


def run_script(script, *args):
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *map(str, args)],
        capture_output=True,
        text=True,
        cwd=SKILL_DIR,
    )


_FLASH_ARGS = [
    {"position": 0, "value": "Flash"},
    {"position": 1, "value": 0}, {"position": 2, "value": 1},
    {"position": 3, "value": ""}, {"position": 4, "value": ""},
    {"position": 5, "value": ""}, {"position": 6, "value": ""},
    {"position": 7, "value": ""}, {"position": 8, "value": ""},
    {"position": 9, "value": 1}, {"position": 10, "value": ""},
    {"position": 11, "value": 1}, {"position": 12, "value": 0},
    {"position": 13, "value": ""}, {"position": 14, "value": 0},
    {"position": 15, "value": ""},
]

_INTENT_ARGS_5 = [
    {"position": 0, "value": "com.example.TEST"},
    {"position": 1, "value": 0}, {"position": 2, "value": 0},
    {"position": 3, "value": ""}, {"position": 4, "value": ""},
]


class TestNormalization(unittest.TestCase):
    def test_normalizes_complete_official_catalogs(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "data"
            result = run_script("normalize_catalogs.py", "--source", SOURCE, "--output-dir", output)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads((output / "actions.json").read_text())["items"]), 382)
            self.assertEqual(len(json.loads((output / "event-contexts.json").read_text())["items"]), 90)
            self.assertEqual(len(json.loads((output / "state-contexts.json").read_text())["items"]), 52)
            actions = json.loads((output / "actions.json").read_text())["items"]
            self.assertEqual(next(item for item in actions if item["code"] == 548)["name"], "Flash")


class TestSafeGeneration(unittest.TestCase):
    def test_generates_a_catalog_backed_task_and_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            request = work / "request.json"
            request.write_text(json.dumps({
                "request": "Show a flash message",
                "tasker_version": "6.7.6-beta",
                "target_device": "Pixel 8",
                "artifact_preference": "task",
                "artifact_spec": {
                    "artifact_type": "task",
                    "name": "Test Flash",
                    "id": 1001,
                    "actions": [{"code": 548, "arguments": _FLASH_ARGS}],
                    "effects": ["ui.flash"],
                    "requirements": {"tasker": True, "root": False, "shizuku": False, "device_owner": False, "accessibility": False}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", work)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["ok"])
            xml = Path(response["artifact_path"])
            root = ET.parse(xml).getroot()
            self.assertEqual(root.tag, "TaskerData")
            self.assertEqual(len(root.findall("Task")), 1)
            self.assertEqual(json.loads(Path(response["manifest_path"]).read_text())["artifact_type"], "task")

    def test_rejects_flash_without_required_tasker_layout(self):
        bad_flash = list(_FLASH_ARGS)
        bad_flash[2] = {"position": 2, "value": 0}
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task", "id": 1002, "name": "Bad Flash",
                    "actions": [{"code": 548, "arguments": bad_flash}]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("Flash requires arg2", result.stdout)

    def test_generates_intent_received_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile",
                    "id": 100, "mid0": 200, "nme": "Test Profile",
                    "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                    "task": {"id": 200, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["ok"])
            self.assertEqual(response["artifact_type"], "profile")
            root = ET.parse(Path(response["artifact_path"])).getroot()
            self.assertEqual(len(root.findall("Profile")), 1)
            prof = root.find("Profile")
            self.assertEqual(prof.findtext("nme"), "Test Profile")
            self.assertIsNotNone(prof.find("Event"))
            self.assertEqual(prof.find("Event").findtext("code"), "599")

    def _make_project_request(self, tmp, profiles, tasks):
        """Helper: write a project request file and return (request_path, output_dir)."""
        request = Path(tmp) / "request.json"
        request.write_text(json.dumps({
            "tasker_version": "6.7.6-beta",
            "artifact_spec": {
                "artifact_type": "project",
                "name": "Test Project",
                "profiles": profiles,
                "tasks": tasks,
            }
        }))
        output = Path(tmp) / "output"
        output.mkdir(parents=True, exist_ok=True)
        return request, output

    def _generate_project(self, tmp, profiles, tasks):
        """Helper: generate project and return (result, root)."""
        request, output = self._make_project_request(tmp, profiles, tasks)
        result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        response = json.loads(result.stdout)
        self.assertTrue(response["ok"])
        self.assertEqual(response["artifact_type"], "project")
        root = ET.parse(Path(response["artifact_path"])).getroot()
        return result, root, response

    def test_generates_project(self):
        """Project generates correct root-sibling layout: Profile, Project, Task elements are siblings under TaskerData."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "Project Profile",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            # Direct children of TaskerData should be: Profile, Project, Task, Task
            children_tags = [child.tag for child in root]
            self.assertEqual(children_tags, ["Profile", "Project", "Task", "Task"],
                             "Profile and Task must be root siblings of Project, not nested inside it")

            # Project element must have NO Profile or Task children
            project = root.find("Project")
            self.assertIsNotNone(project)
            self.assertEqual(project.findall("Profile"), [],
                             "Project must not contain nested Profile elements")
            self.assertEqual(project.findall("Task"), [],
                             "Project must not contain nested Task elements")

    def test_project_root_sibling_layout(self):
        """Profile, Project, and all Task elements must be direct children of TaskerData."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            # Every Profile, Project, and Task must be a DIRECT child of TaskerData
            direct_children = {child.tag for child in root}
            self.assertIn("Profile", direct_children,
                          "Profile must be a direct child of TaskerData")
            self.assertIn("Project", direct_children,
                          "Project must be a direct child of TaskerData")
            self.assertIn("Task", direct_children,
                          "Task must be a direct child of TaskerData")

            # Verify exact count: 1 Profile, 1 Project, 2 Tasks
            self.assertEqual(len(root.findall("Profile")), 1)
            self.assertEqual(len(root.findall("Project")), 1)
            self.assertEqual(len(root.findall("Task")), 2)

            # No Profile or Task anywhere inside Project
            project = root.find("Project")
            self.assertEqual(len(project.findall(".//Profile")), 0,
                             "No Profile element may exist inside Project")
            self.assertEqual(len(project.findall(".//Task")), 0,
                             "No Task element may exist inside Project")

    def test_project_contains_no_nested_profile_or_task(self):
        """Project element must not contain nested Profile or Task; they must be root siblings."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            project = root.find("Project")
            self.assertEqual(len(project.findall("Profile")), 0,
                             "Project must not nest Profile elements")
            self.assertEqual(len(project.findall("Task")), 0,
                             "Project must not nest Task elements")
            self.assertEqual(len(root.findall("Profile")), 1,
                             "Root must contain exactly 1 Profile")
            self.assertEqual(len(root.findall("Task")), 2,
                             "Root must contain exactly 2 Tasks")

    def test_project_derives_complete_pids(self):
        """Project element must derive pids from emitted profile IDs."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            project = root.find("Project")
            self.assertIsNotNone(project.find("pids"),
                                 "Project must have a pids element")
            self.assertEqual(project.find("pids").text, "101",
                             "pids must contain all profile IDs from the graph")

    def test_project_derives_complete_tids(self):
        """Project element must derive tids from all emitted task IDs."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            project = root.find("Project")
            self.assertIsNotNone(project.find("tids"),
                                 "Project must have a tids element")
            tids_text = project.find("tids").text
            tids_set = set(t.strip() for t in tids_text.split(","))
            self.assertEqual(tids_set, {"201", "202"},
                             "tids must contain all task IDs (201 from profile, 202 explicit)")

    def test_project_ids_are_unique(self):
        """All Profile and Task integer IDs must be unique — no overlap between element kinds."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            profile_ids = set()
            for p in root.findall("Profile"):
                pid = int(p.findtext("id"))
                profile_ids.add(pid)

            task_ids = set()
            for t in root.findall("Task"):
                tid = int(t.findtext("id"))
                task_ids.add(tid)

            # No overlap between profile and task IDs
            overlap = profile_ids & task_ids
            self.assertEqual(len(overlap), 0,
                             f"Profile and Task IDs must be unique, overlap: {overlap}")
            # Each kind internally unique
            self.assertEqual(len(profile_ids), len(root.findall("Profile")))
            self.assertEqual(len(task_ids), len(root.findall("Task")))

    def test_project_entry_exit_references(self):
        """Profile mid0 and mid1 must reference task IDs; both tasks must be root siblings."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "mid1": 202, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]},
                "exit_task": {"id": 202, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = []
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            profile = root.find("Profile")
            self.assertIsNotNone(profile)
            self.assertEqual(profile.find("mid0").text, "201")
            self.assertEqual(profile.find("mid1").text, "202")
            self.assertEqual(len(root.findall("Task")), 2,
                             "Both entry and exit tasks must be root siblings")
            task_ids = {t.findtext("id") for t in root.findall("Task")}
            self.assertEqual(task_ids, {"201", "202"})

    def test_project_shared_task_emitted_once(self):
        """When two profiles share the same task ID via mid0, that task must be emitted once at the root."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }, {
                "id": 102, "mid0": 201, "nme": "P2",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
            }]
            tasks = []
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            task_ids = [t.findtext("id") for t in root.findall("Task")]
            self.assertEqual(len(task_ids), 1,
                             "Shared task must be emitted exactly once at root")
            self.assertEqual(task_ids[0], "201")

    def test_generates_minimal_project_candidate(self):
        """Minimal project with one profile and no explicit tasks produces correct root layout."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 501, "mid0": 502, "nme": "Min Prof",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 502, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = []
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            children_tags = [child.tag for child in root]
            self.assertEqual(children_tags, ["Profile", "Project", "Task"],
                             "Minimal project must have exactly Profile, Project, Task as root siblings")

            project = root.find("Project")
            self.assertEqual(project.find("pids").text, "501")
            self.assertEqual(project.find("tids").text, "502")

    def test_project_with_entry_and_exit_tasks(self):
        """Profile with mid0 and mid1 plus entry/exit tasks must emit both tasks as root siblings."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 301, "mid0": 301, "mid1": 302, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 301, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]},
                "exit_task": {"id": 302, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = []
            _, root, _ = self._generate_project(tmp, profiles, tasks)

            self.assertEqual(len(root.findall("Task")), 2,
                             "Both entry (301) and exit (302) tasks must be root siblings")
            task_ids = {t.findtext("id") for t in root.findall("Task")}
            self.assertEqual(task_ids, {"301", "302"})
            self.assertEqual(root.find("Profile").find("mid1").text, "302")

    def test_task_generation_regression(self):
        """Regression: standalone Flash task still produces valid output."""
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task",
                    "name": "Regression Flash",
                    "id": 1001,
                    "actions": [{"code": 548, "arguments": _FLASH_ARGS}],
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["ok"])
            root = ET.parse(Path(response["artifact_path"])).getroot()
            self.assertEqual(root.tag, "TaskerData")
            tasks = root.findall("Task")
            self.assertEqual(len(tasks), 1)
            self.assertEqual(tasks[0].findtext("id"), "1001")
            self.assertEqual(tasks[0].findtext(".//Action/code"), "548")

    def test_profile_generation_regression(self):
        """Regression: standalone intent profile still produces Profile and Task as root siblings."""
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile",
                    "id": 100, "mid0": 200, "nme": "Regression Profile",
                    "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                    "task": {"id": 200, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["ok"])
            root = ET.parse(Path(response["artifact_path"])).getroot()
            self.assertEqual(len(root.findall("Profile")), 1)
            self.assertEqual(len(root.findall("Task")), 1)
            self.assertIsNone(root.find("Profile/Task"),
                              "Profile must not nest Task elements")
            self.assertEqual(root.find("Profile").findtext("mid0"), "200")

    def test_generator_executes_graph_validator(self):
        """The graph validation in the JSON response must be backed by real structure — not hardcoded."""
        with tempfile.TemporaryDirectory() as tmp:
            profiles = [{
                "id": 101, "mid0": 201, "nme": "P1",
                "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
            }]
            tasks = [{"id": 202, "nme": "T1", "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
            result, root, response = self._generate_project(tmp, profiles, tasks)

            # The response claims graph validation passed
            self.assertEqual(response["validation"]["graph"], "pass",
                             "Response claims graph validation passed")

            # The graph validation must have derived pids/tids in the Project element.
            # If pids/tids are missing, the graph validation metadata is hollow.
            project = root.find("Project")
            self.assertIsNotNone(project, "Project element must exist")
            pids_el = project.find("pids")
            tids_el = project.find("tids")
            self.assertIsNotNone(pids_el,
                                 "Graph validation must derive pids from emitted Profile IDs")
            self.assertIsNotNone(tids_el,
                                 "Graph validation must derive tids from emitted Task IDs")
            self.assertEqual(pids_el.text, "101",
                             "pids must list all Profile IDs in the graph")
            tids_set = set(t.strip() for t in tids_el.text.split(","))
            self.assertEqual(tids_set, {"201", "202"},
                             "tids must list all Task IDs in the graph")

    def test_profile_rejects_unsupported_state_context(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile",
                    "id": 300, "mid0": 400, "nme": "State Profile",
                    "state": {"code": 999999, "arguments": []}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("unknown", result.stdout)

    def test_generates_state_profile(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile",
                    "id": 400, "mid0": 401, "nme": "Battery State",
                    "state": {"code": 140, "arguments": [
                        {"position": 0, "value": 0}, {"position": 1, "value": 100}
                    ]},
                    "task": {"id": 401, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stderr)
            response = json.loads(result.stdout)
            self.assertTrue(response["ok"])
            self.assertEqual(response["artifact_type"], "profile")
            root = ET.parse(Path(response["artifact_path"])).getroot()
            self.assertEqual(len(root.findall("Profile")), 1)
            self.assertIsNotNone(root.find("Profile").find("State"))
            self.assertEqual(root.find("Profile").find("State").findtext("code"), "140")
    def test_generates_day_profile_from_hermes_fixture_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile", "id": 610, "mid0": 611,
                    "nme": "Weekday Profile",
                    "day": {"weekdays": [2, 4, 6]},
                    "task": {"id": 611, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout)
            root = ET.parse(Path(json.loads(result.stdout)["artifact_path"])).getroot()
            self.assertEqual([n.tag for n in root.find("Profile/Day")], ["wday0", "wday1", "wday2"])
            self.assertEqual(root.findtext("Profile/Day/wday1"), "4")
            self.assertIsNotNone(root.find("Task"))
            self.assertIsNone(root.find("Profile/Task"))

    def test_generates_named_location_profile_from_hermes_fixture_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile", "id": 620, "mid0": 621, "mid1": 622,
                    "nme": "Location Profile",
                    "location": {"cname": "Test location", "lat": 41.0, "long": 2.0, "rad": 100.0},
                    "task": {"id": 621, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]},
                    "exit_task": {"id": 622, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout)
            root = ET.parse(Path(json.loads(result.stdout)["artifact_path"])).getroot()
            loc = root.find("Profile/Loc")
            self.assertEqual([n.tag for n in loc], ["cname", "lat", "long", "rad"])
            self.assertEqual(root.findtext("Profile/mid1"), "622")
            self.assertEqual(len(root.findall("Task")), 2)

    def test_rejects_invalid_day_value(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "profile", "id": 630, "mid0": 631,
                    "day": {"months": [12]}
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("months[0]", result.stdout)

    def test_generates_static_java_code_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task", "id": 501, "name": "Static Java Code",
                    "actions": [{"code": 474, "arguments": [
                        {"position": 0, "value": 'tasker.setVariable("%result", "ok");'},
                        {"position": 1, "value": "%result"},
                        {"position": 2, "value": 0}
                    ]}]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout)
            root = ET.parse(Path(json.loads(result.stdout)["artifact_path"])).getroot()
            self.assertEqual(root.findtext(".//Action/code"), "474")

    def test_generates_termux_tasker_template_with_typed_replacements(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task", "id": 502, "name": "Termux Command",
                    "actions": [{
                        "plugin_template": "termux-tasker.run-command.v1002",
                        "bundle_replacements": {
                            "com.termux.tasker.extra.EXECUTABLE": "echo",
                            "com.termux.execute.arguments": "hello",
                            "com.termux.tasker.extra.WAIT_FOR_RESULT": True
                        }
                    }]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout)
            root = ET.parse(Path(json.loads(result.stdout)["artifact_path"])).getroot()
            self.assertEqual(root.findtext(".//Action/code"), "1256900802")
            self.assertEqual(root.findtext(".//com.termux.tasker.extra.EXECUTABLE"), "echo")

    def test_generates_exact_autotools_template(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task", "id": 503, "name": "AutoTools Launcher",
                    "actions": [{"plugin_template": "autotools.launcher.hyperion.v2"}]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 0, result.stdout)
            root = ET.parse(Path(json.loads(result.stdout)["artifact_path"])).getroot()
            self.assertEqual(root.findtext(".//plugintypeid"), "com.joaomgcd.autotools.intent.IntentLauncher")

    def test_rejects_untyped_autotools_mutation(self):
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "task", "id": 503, "name": "AutoTools",
                    "actions": [{
                        "plugin_template": "autotools.launcher.hyperion.v2",
                        "bundle_replacements": {"parameters": "{}"}
                    }]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not permit replacements", result.stdout)

    def test_rejects_conflicting_duplicate_task_definitions(self):
        """Two task specs with the same integer ID but different actions must be rejected."""
        with tempfile.TemporaryDirectory() as tmp:
            request = Path(tmp) / "request.json"
            request.write_text(json.dumps({
                "tasker_version": "6.7.6-beta",
                "artifact_spec": {
                    "artifact_type": "project",
                    "name": "Conflicting Tasks",
                    "profiles": [{
                        "id": 101, "mid0": 201, "mid1": 202, "nme": "P1",
                        "event": {"code": 599, "pri": 0, "arguments": _INTENT_ARGS_5},
                        "task": {"id": 201, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]},
                        "exit_task": {"id": 202, "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}
                    }],
                    "tasks": [{"id": 202, "nme": "Different Name",
                               "actions": [{"code": 548, "arguments": _FLASH_ARGS}]}]
                }
            }))
            result = run_script("generate_tasker_artifact.py", "--request", request, "--output-dir", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("conflicting definitions", result.stdout)


class TestValidators(unittest.TestCase):
    def test_catalog_validator_rejects_unknown_action_code(self):
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Task sr="task1"><id>1</id><nme>Test</nme><Action sr="act0" ve="7"><code>999999</code></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.tsk.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_xml.py", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown action code", result.stdout)

    def test_graph_validator_rejects_missing_profile_task_reference(self):
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Profile sr="prof1" ve="2"><flags>40</flags><id>1</id><mid0>99</mid0><nme>Test</nme></Profile></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.prf.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_graph.py", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing task id 99", result.stdout)

    def test_graph_validator_accepts_uuid_project_id(self):
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Project sr="proj0" ve="2"><name>Test</name><id>3fbe3636-1ee1-492a-8956-cb6d43769d0f</id></Project></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.prj.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_graph.py", path)
            self.assertEqual(result.returncode, 0)

    def test_policy_validator_rejects_dynamic_eval_and_missing_capability_return(self):
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Task sr="task1"><id>1</id><nme>Hermes · Capability · Bad v1</nme><Action sr="act0" ve="7"><code>1</code><Str sr="arg0" ve="3">eval(source)</Str></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.tsk.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_xml.py", path, "--policy")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("contains eval()", result.stdout)
            self.assertIn("requires a Return action", result.stdout)

    def test_policy_allows_eval_in_non_capability_tasks(self):
        """Java Runner and similar tasks should not be flagged for eval()."""
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Task sr="task1"><id>1</id><nme>Hermes · Java Runner</nme><Action sr="act0" ve="7"><code>547</code><Str sr="arg0" ve="3">eval(source)</Str><Str sr="arg1" ve="3">1</Str><Int sr="arg2" val="0"/><Int sr="arg3" val="0"/><Int sr="arg4" val="0"/><Int sr="arg5" val="3"/><Int sr="arg6" val="0"/></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "ok.tsk.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_xml.py", path, "--policy")
            self.assertEqual(result.returncode, 0, result.stdout)

    def test_policy_rejects_short_tasker_variable_base_name(self):
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Task sr="task1"><id>1</id><nme>Test</nme><Action sr="act0" ve="7"><code>547</code><Str sr="arg0" ve="3">%i</Str><Str sr="arg1" ve="3">1</Str><Int sr="arg2" val="0"/><Int sr="arg3" val="0"/><Int sr="arg4" val="0"/><Int sr="arg5" val="3"/><Int sr="arg6" val="0"/></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad-variable.tsk.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_xml.py", path, "--policy")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("invalid Tasker variable base name", result.stdout)

    def test_graph_rejects_missing_reference(self):
        """Graph validator must reject a Profile mid0 referencing a nonexistent Task."""
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Profile sr="prof1" ve="2"><flags>40</flags><id>1</id><mid0>999</mid0><nme>Bad Ref</nme></Profile></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "missing_ref.prf.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_graph.py", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing", result.stdout.lower())

    def test_graph_rejects_duplicate_id(self):
        """Graph validator must reject two Tasks sharing the same integer id."""
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Task sr="task1"><id>42</id><nme>A</nme><Action sr="act0" ve="7"><code>548</code></Action></Task><Task sr="task2"><id>42</id><nme>B</nme><Action sr="act0" ve="7"><code>548</code></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "dup_id.tsk.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_graph.py", path)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("duplicate", result.stdout.lower())

    def test_graph_rejects_wrong_reference_kind(self):
        """Graph validator must reject a Project pids that references a Task id instead of a Profile id."""
        xml = '''<TaskerData sr="" dvi="1" tv="6.7.6-beta"><Profile sr="prof1" ve="2"><flags>40</flags><id>10</id><mid0>20</mid0><nme>P</nme></Profile><Project sr="proj0" ve="2"><id>uuid-1</id><name>Test</name><pids>20</pids></Project><Task sr="task20"><id>20</id><nme>T</nme><Action sr="act0" ve="7"><code>548</code></Action></Task></TaskerData>'''
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "wrong_kind.prj.xml"
            path.write_text(xml)
            result = run_script("validate_tasker_graph.py", path)
            self.assertNotEqual(result.returncode, 0,
                                "Graph validator must reject pids referencing a Task id (20) instead of a Profile id")
            output = result.stdout.lower()
            self.assertTrue("wrong" in output or "type" in output or "kind" in output or "task" in output,
                            f"Validator should indicate wrong reference kind, got: {result.stdout}")


if __name__ == "__main__":
    unittest.main()
