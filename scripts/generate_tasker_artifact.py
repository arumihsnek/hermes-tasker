#!/usr/bin/env python3
"""Render catalog-backed Tasker Tasks, Profiles, and Projects from a typed request spec."""
from __future__ import annotations

import argparse
import json
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import action_by_code, context_by_code, json_result
from validate_tasker_graph import validate as validate_graph
from validate_tasker_xml import validate

CAPABILITY_PREFIX = "Hermes · Capability · "
SKILL_DIR = Path(__file__).resolve().parents[1]


def unsupported(message: str) -> int:
    print(json_result(False, status="unsupported", missing_evidence=[message]))
    return 2


def add_argument(parent: ET.Element, parameter: dict, supplied: dict) -> None:
    tag = parameter["xml_type"]
    position = parameter["position"]
    value = supplied.get("value")
    node = ET.SubElement(parent, tag, {"sr": f"arg{position}"})
    if tag == "Int":
        if not isinstance(value, int):
            raise ValueError(f"arg{position} requires integer value")
        node.set("val", str(value))
    elif tag == "Bundle":
        if value not in (None, {}, {"Vals": {}}):
            raise ValueError(
                f"arg{position} Bundle requires an exported fixture for non-empty configuration"
            )
        ET.SubElement(node, "Vals", {"sr": "val"})
    elif tag == "App":
        if not isinstance(value, dict) or set(value) != {"appClass", "appPkg", "label"}:
            raise ValueError(f"arg{position} App requires appClass, appPkg, and label")
        for key in ("appClass", "appPkg", "label"):
            ET.SubElement(node, key).text = str(value[key])
    elif tag == "Img":
        if value not in (None, {}):
            raise ValueError(
                f"arg{position} Img requires an exported fixture for configured image sources"
            )
    elif tag == "Str":
        if not isinstance(value, str):
            raise ValueError(f"arg{position} requires string value")
        node.set("ve", "3")
        node.text = value
    else:
        raise ValueError(f"unsupported evidence-backed argument type {tag} for arg{position}")


def plugin_template_by_id(template_id: str) -> dict | None:
    data_path = SKILL_DIR / "data" / "plugin-templates.json"
    if not data_path.exists():
        return None
    for template in json.loads(data_path.read_text(encoding="utf-8")).get("templates", []):
        if template.get("id") == template_id:
            return template
    return None


def _append_plugin_action(parent: ET.Element, index: int, action_spec: dict) -> None:
    """Clone an evidence-backed plugin Action; no generic Bundle synthesis."""
    template_id = action_spec.get("plugin_template")
    template = plugin_template_by_id(template_id) if isinstance(template_id, str) else None
    if template is None:
        raise ValueError(f"unknown or unsupported plugin template {template_id!r}")
    replacements = action_spec.get("bundle_replacements", {})
    if not isinstance(replacements, dict):
        raise ValueError("bundle_replacements must be an object")
    permitted = set(template.get("mutable_bundle_keys", []))
    unknown = set(replacements) - permitted
    if unknown:
        raise ValueError(
            f"plugin template {template_id} does not permit replacements for {sorted(unknown)}"
        )
    try:
        action = ET.fromstring(template["action_xml"])
    except (ET.ParseError, KeyError) as exc:
        raise ValueError(f"plugin template {template_id} is corrupted") from exc
    action.set("sr", f"act{index}")
    for key, value in replacements.items():
        if not isinstance(value, (str, bool, int)):
            raise ValueError(f"plugin replacement {key} must be scalar")
        value_node = action.find(f"./Bundle/Vals/{key}")
        type_node = action.find(f"./Bundle/Vals/{key}-type")
        if value_node is None or type_node is None:
            raise ValueError(f"template {template_id} lacks typed Bundle key {key}")
        type_name = type_node.text
        if type_name == "java.lang.Boolean" and not isinstance(value, bool):
            raise ValueError(f"plugin replacement {key} must be boolean")
        if type_name == "java.lang.Integer" and (not isinstance(value, int) or isinstance(value, bool)):
            raise ValueError(f"plugin replacement {key} must be integer")
        if type_name == "java.lang.String" and not isinstance(value, str):
            raise ValueError(f"plugin replacement {key} must be string")
        value_node.text = str(value).lower() if isinstance(value, bool) else str(value)
    parent.append(action)


def append_action(parent: ET.Element, index: int, action_spec: dict) -> None:
    """Append either an official-catalog Action or an exact plugin template."""
    if "plugin_template" in action_spec:
        _append_plugin_action(parent, index, action_spec)
        return
    code = action_spec.get("code")
    if not isinstance(code, int):
        raise ValueError(f"action {index} has no integer code")
    catalog = action_by_code(code)
    if catalog is None:
        raise ValueError(f"action {index} uses unknown catalog code {code}")
    action = ET.SubElement(parent, "Action", {"sr": f"act{index}", "ve": "7"})
    ET.SubElement(action, "code").text = str(code)
    supplied = {item["position"]: item for item in action_spec.get("arguments", [])}
    expected = {item["position"]: item for item in catalog["arguments"]}
    if set(supplied) != set(expected):
        raise ValueError(
            f"action {catalog['name']} requires exact arguments "
            f"{sorted(expected)}, got {sorted(supplied)}"
        )
    if code == 548 and supplied[2].get("value") != 1:
        raise ValueError("Flash requires arg2 Tasker Layout=1 per official instruction")
    for position in sorted(expected):
        add_argument(action, expected[position], supplied[position])


def _ts() -> str:
    return str(int(time.time() * 1000))


def render_task(spec: dict, version: str) -> ET.Element:
    root = ET.Element("TaskerData", {"sr": "", "dvi": "1", "tv": version})
    task = ET.SubElement(root, "Task", {"sr": f"task{spec['id']}"})
    ET.SubElement(task, "id").text = str(spec["id"])
    ET.SubElement(task, "nme").text = spec["name"]
    for index, action_spec in enumerate(spec.get("actions", [])):
        append_action(task, index, action_spec)
    return root


def _context_extra(context: ET.Element, spec: dict) -> None:
    """Add extra non-argument children (e.g. <pri>) inside a context."""
    pri = spec.get("pri")
    if pri is not None:
        ET.SubElement(context, "pri").text = str(pri)


def _append_profile_task(root: ET.Element, task_spec: dict) -> None:
    """Profile-linked Tasks are anonymous root siblings of <Profile>."""
    task = ET.SubElement(root, "Task", {"sr": f"task{task_spec['id']}"})
    ET.SubElement(task, "cdate").text = str(task_spec.get("cdate", _ts()))
    ET.SubElement(task, "edate").text = str(task_spec.get("edate", _ts()))
    ET.SubElement(task, "id").text = str(task_spec["id"])
    if task_spec.get("nme"):
        raise ValueError("profile-linked Tasks must be anonymous; omit task.nme")
    for index, action_spec in enumerate(task_spec.get("actions", [])):
        append_action(task, index, action_spec)


def _append_day_context(profile: ET.Element, spec: dict) -> None:
    day = ET.SubElement(profile, "Day", {"sr": spec.get("sr", "con0")})
    groups = (
        ("months", "mnth", 0, 11),
        ("weekdays", "wday", 1, 7),
        ("days_of_month", "mday", 1, 31),
    )
    emitted = 0
    for field, tag_prefix, low, high in groups:
        values = spec.get(field, [])
        if not isinstance(values, list):
            raise ValueError(f"day.{field} must be a list")
        for index, value in enumerate(values):
            if not isinstance(value, int) or isinstance(value, bool) or not low <= value <= high:
                raise ValueError(f"day.{field}[{index}] must be integer in [{low}, {high}]")
            ET.SubElement(day, f"{tag_prefix}{index}").text = str(value)
            emitted += 1
    if not emitted:
        raise ValueError("Day context requires at least one month, weekday, or day-of-month")


def _append_location_context(profile: ET.Element, spec: dict) -> None:
    loc = ET.SubElement(profile, "Loc", {"sr": spec.get("sr", "con0")})
    for key in ("lat", "long", "rad"):
        value = spec.get(key)
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"location.{key} requires a number")
        ET.SubElement(loc, key).text = str(value)
    cname = spec.get("cname")
    if cname is not None:
        if not isinstance(cname, str) or not cname:
            raise ValueError("location.cname must be a non-empty string when supplied")
        # Canonical fixture order: cname before coordinates.
        loc.remove(loc.find("lat")); loc.remove(loc.find("long")); loc.remove(loc.find("rad"))
        ET.SubElement(loc, "cname").text = cname
        for key in ("lat", "long", "rad"):
            ET.SubElement(loc, key).text = str(spec[key])


def render_profile(spec: dict, version: str) -> ET.Element:
    """Render a Profile using the canonical order observed in real 6.7.6-beta exports."""
    root = ET.Element("TaskerData", {"sr": "", "dvi": "1", "tv": version})
    prof_sr = spec.get("sr", f"prof{spec['id']}")
    profile = ET.SubElement(root, "Profile", {"sr": prof_sr, "ve": "2"})
    ET.SubElement(profile, "cdate").text = spec.get("cdate", _ts())
    if spec.get("clp"):
        ET.SubElement(profile, "clp").text = "true"
    ET.SubElement(profile, "edate").text = str(spec.get("edate", _ts()))
    ET.SubElement(profile, "flags").text = str(spec.get("flags", "40"))
    ET.SubElement(profile, "id").text = str(spec["id"])
    ET.SubElement(profile, "mid0").text = str(spec["mid0"])
    mid1 = spec.get("mid1")
    if mid1 is not None:
        ET.SubElement(profile, "mid1").text = str(mid1)
    if spec.get("nme"):
        ET.SubElement(profile, "nme").text = spec["nme"]
    # Context: Day and Loc have their own documented non-code serialization.
    if spec.get("day") is not None:
        _append_day_context(profile, spec["day"])
    elif spec.get("location") is not None:
        _append_location_context(profile, spec["location"])
    else:
        for ctx_key in ("Event", "State", "Time", "App"):
            ctx_spec = spec.get(ctx_key.lower())
            if ctx_spec is None:
                continue
            ctx_el = ET.SubElement(profile, ctx_key)
            code = ctx_spec.get("code")
            if code is not None:
                ET.SubElement(ctx_el, "code").text = str(code)
            _context_extra(ctx_el, ctx_spec)
            catalog = context_by_code(ctx_key, code) if code else None
            if catalog:
                supplied = {a["position"]: a for a in ctx_spec.get("arguments", [])}
                expected = {a["position"]: a for a in catalog["arguments"]}
                if set(supplied) != set(expected):
                    raise ValueError(
                        f"{ctx_key} code {code} requires arguments "
                        f"{sorted(expected)}, got {sorted(supplied)}"
                    )
                for pos in sorted(expected):
                    add_argument(ctx_el, expected[pos], supplied[pos])
            break
        else:
            raise ValueError("profile requires an evidence-backed Event, State, Day, Location, Time, or App context")
    if "task" in spec:
        _append_profile_task(root, spec["task"])
    if "exit_task" in spec:
        if mid1 is None:
            raise ValueError("exit_task requires mid1")
        _append_profile_task(root, spec["exit_task"])
    return root


def _check_task_conflict(tid: int, existing: dict, new: dict) -> None:
    """Raise ValueError if two task specs with the same integer ID differ."""
    def _normalize(t: dict) -> tuple:
        return (
            t.get("nme"),
            t.get("pri"),
            tuple(json.dumps(a, sort_keys=True, default=str) for a in t.get("actions", [])),
        )
    if _normalize(existing) != _normalize(new):
        raise ValueError(f"conflicting definitions for task id {tid}")


def _collect_project_tasks(spec: dict) -> list[dict]:
    """Collect and deduplicate Tasks from profiles and the explicit task list.

    Returns deduplicated tasks in first-definition order.
    """
    seen: dict[int, dict] = {}  # integer id -> first task spec

    for pspec in spec.get("profiles", []):
        for tkey in ("task", "exit_task"):
            tspec = pspec.get(tkey)
            if tspec is None:
                continue
            if tkey == "exit_task" and pspec.get("mid1") is None:
                raise ValueError("exit_task requires mid1")
            tid = int(tspec["id"])
            if tid in seen:
                _check_task_conflict(tid, seen[tid], tspec)
            else:
                seen[tid] = tspec

    for tspec in spec.get("tasks", []):
        tid = int(tspec["id"])
        if tid in seen:
            _check_task_conflict(tid, seen[tid], tspec)
        else:
            seen[tid] = tspec

    return list(seen.values())


def _append_project_profile(root: ET.Element, pspec: dict) -> None:
    """Append a Profile as a root sibling with canonical 6.7.6-beta element order."""
    p = ET.SubElement(root, "Profile", {"sr": f"prof{pspec['id']}", "ve": "2"})
    ET.SubElement(p, "cdate").text = pspec.get("cdate", _ts())
    if pspec.get("clp"):
        ET.SubElement(p, "clp").text = "true"
    ET.SubElement(p, "edate").text = str(pspec.get("edate", _ts()))
    ET.SubElement(p, "flags").text = str(pspec.get("flags", "40"))
    ET.SubElement(p, "id").text = str(pspec["id"])
    ET.SubElement(p, "mid0").text = str(pspec["mid0"])
    mid1 = pspec.get("mid1")
    if mid1 is not None:
        ET.SubElement(p, "mid1").text = str(mid1)
    if pspec.get("nme"):
        ET.SubElement(p, "nme").text = pspec["nme"]
    # Context: Day and Location have dedicated helpers matching render_profile()
    if pspec.get("day") is not None:
        _append_day_context(p, pspec["day"])
    elif pspec.get("location") is not None:
        _append_location_context(p, pspec["location"])
    else:
        for ctx_key in ("Event", "State", "Time", "App"):
            ctx_spec = pspec.get(ctx_key.lower())
            if ctx_spec is None:
                continue
            ctx_el = ET.SubElement(p, ctx_key)
            code = ctx_spec.get("code")
            if code is not None:
                ET.SubElement(ctx_el, "code").text = str(code)
            _context_extra(ctx_el, ctx_spec)
            catalog = context_by_code(ctx_key, code) if code else None
            if catalog:
                supplied = {a["position"]: a for a in ctx_spec.get("arguments", [])}
                expected = {a["position"]: a for a in catalog["arguments"]}
                if set(supplied) != set(expected):
                    raise ValueError(
                        f"{ctx_key} code {code} requires arguments "
                        f"{sorted(expected)}, got {sorted(supplied)}"
                    )
                for pos in sorted(expected):
                    add_argument(ctx_el, expected[pos], supplied[pos])
            break
        else:
            raise ValueError(
                "profile requires an evidence-backed Event, State, Day, Location, Time, or App context"
            )


def _append_project_task(root: ET.Element, tspec: dict) -> None:
    """Append a Task as a root sibling with cdate, edate, id, optional nme, and actions."""
    task = ET.SubElement(root, "Task", {"sr": f"task{tspec['id']}"})
    ET.SubElement(task, "cdate").text = str(tspec.get("cdate", _ts()))
    ET.SubElement(task, "edate").text = str(tspec.get("edate", _ts()))
    ET.SubElement(task, "id").text = str(tspec["id"])
    if tspec.get("nme"):
        ET.SubElement(task, "nme").text = tspec["nme"]
    for index, action_spec in enumerate(tspec.get("actions", [])):
        append_action(task, index, action_spec)


def render_project(spec: dict, version: str) -> ET.Element:
    """Render a Project using root-sibling layout as observed in real 6.7.6-beta exports.

    Root children order: Profile*, Project, Task*
    Profiles are root siblings (not nested inside Project).
    Tasks are root siblings (not nested inside Project).
    pids/tids are derived from the emitted graph.
    """
    root = ET.Element("TaskerData", {"sr": "", "dvi": "1", "tv": version})

    # 1. Collect and deduplicate tasks (must happen before emitting)
    tasks = _collect_project_tasks(spec)

    # 2. Emit Profiles as root siblings (preserves input order)
    for pspec in spec.get("profiles", []):
        _append_project_profile(root, pspec)

    # 3. Derive pids/tids from the emitted graph
    profile_ids = [int(p["id"]) for p in spec.get("profiles", [])]
    task_ids = [int(t["id"]) for t in tasks]

    derived_pids = ",".join(str(pid) for pid in profile_ids)
    derived_tids = ",".join(str(tid) for tid in task_ids)

    # Validate legacy pids/tids if supplied (order-independent set comparison)
    if spec.get("pids"):
        legacy_pids = [int(x.strip()) for x in spec["pids"].split(",")]
        if len(legacy_pids) != len(set(legacy_pids)):
            raise ValueError("supplied pids contains duplicates")
        if set(legacy_pids) != set(profile_ids):
            raise ValueError(
                f"supplied pids {spec['pids']} does not match "
                f"emitted profile IDs {derived_pids}"
            )

    if spec.get("tids"):
        legacy_tids = [int(x.strip()) for x in spec["tids"].split(",")]
        if len(legacy_tids) != len(set(legacy_tids)):
            raise ValueError("supplied tids contains duplicates")
        if set(legacy_tids) != set(task_ids):
            raise ValueError(
                f"supplied tids {spec['tids']} does not match "
                f"emitted task IDs {derived_tids}"
            )

    # 4. Emit Project as root sibling (after all profiles, before tasks)
    project_id = spec.get("id", str(_ts()))
    proj = ET.SubElement(root, "Project", {"sr": "proj0", "ve": "2"})
    ET.SubElement(proj, "cdate").text = spec.get("cdate", _ts())
    ET.SubElement(proj, "id").text = project_id
    ET.SubElement(proj, "name").text = spec.get("name", "")
    if profile_ids:
        ET.SubElement(proj, "pids").text = derived_pids
    if task_ids:
        ET.SubElement(proj, "tids").text = derived_tids

    # 5. Emit deduplicated Tasks as root siblings
    for tspec in tasks:
        _append_project_task(root, tspec)

    return root


def contains_return(root: ET.Element) -> bool:
    for action in root.findall(".//Action"):
        code_text = action.findtext("code")
        if code_text and code_text.isdigit():
            item = action_by_code(int(code_text))
            if item and item["name"] == "Return":
                return True
    return False


def _export(root: ET.Element, kind: str, version: str, name: str, spec: dict, output_dir: Path) -> int:
    ext = {"task": "tsk", "profile": "prf", "project": "prj"}.get(kind, "xml")
    slug = "artifact"
    artifact_path = output_dir / f"{slug}.{ext}.xml"
    manifest_path = output_dir / f"{slug}.manifest.json"
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(artifact_path, encoding="utf-8", xml_declaration=True)
    manifest = {
        "schema": "hermes-tasker-artifact/v1",
        "artifact_type": kind,
        "tasker_version": version,
        "name": name,
        "effects": spec.get("effects", []),
        "requirements": spec.get("requirements", {"tasker": True}),
        "import_method": {
            "task": "silent_task_import",
            "profile": "visual_profile_import",
            "project": "visual_project_import",
        }.get(kind, "visual_profile_import"),
        "confirmation_required": kind != "task",
        "source_evidence": "official_catalog_and_6_7_6_beta_exports",
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json_result(
        True,
        artifact_type=kind,
        reason=f"explicit {kind} spec backed by catalog and real 6.7.6-beta fixtures",
        artifact_path=str(artifact_path),
        manifest_path=str(manifest_path),
        validation={"xml": "pass", "catalog": "pass", "graph": "pass"},
        import_method=manifest["import_method"],
        confirmation_required=manifest["confirmation_required"],
        requirements=manifest["requirements"],
        warnings=[],
    ))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    request = json.loads(args.request.read_text(encoding="utf-8"))
    spec = request.get("artifact_spec", {})
    kind = spec.get("artifact_type")
    version = request.get("tasker_version", "6.7.6-beta")
    if version != "6.7.6-beta":
        return unsupported(f"no evidence bundle is installed for Tasker version {version}")
    if kind not in ("task", "profile", "project"):
        return unsupported("artifact_spec.artifact_type must be task, profile, or project")
    try:
        if kind == "task":
            root = render_task(spec, version)
            name = spec["name"]
            if name.startswith(CAPABILITY_PREFIX) and not contains_return(root):
                return unsupported(
                    "Hermes capability Tasks require a catalog-backed Return action"
                )
        elif kind == "profile":
            root = render_profile(spec, version)
            name = spec.get("nme", spec.get("name", "unnamed"))
        elif kind == "project":
            root = render_project(spec, version)
            name = spec.get("name", "unnamed")
        else:
            return unsupported(f"unknown artifact type {kind}")
    except (KeyError, TypeError, ValueError) as error:
        print(json_result(False, status="invalid_request", error_message=str(error)))
        return 1
    # XML/catalog/policy validation
    errors = validate(root, policy=True)
    if errors:
        print(json_result(False, status="validation_failed", errors=errors))
        return 1

    # Graph validation (in-process, for projects)
    if root.find("Project") is not None:
        graph_errors = validate_graph(root)
        if graph_errors:
            print(json_result(False, status="graph_validation_failed", errors=graph_errors))
            return 1

    args.output_dir.mkdir(parents=True, exist_ok=True)
    return _export(root, kind, version, name, spec, args.output_dir)


if __name__ == "__main__":
    raise SystemExit(main())
