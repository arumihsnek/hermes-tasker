#!/usr/bin/env python3
"""Evidence-only XML, catalog, and Hermes policy validator."""
from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import action_by_code, context_by_code

ARGUMENT_TAGS = {"Str", "Int", "Bundle", "Img", "App", "ConditionList"}
CAPABILITY_PREFIX = "Hermes · Capability · "


def element_arguments(element: ET.Element) -> dict[int, ET.Element]:
    result: dict[int, ET.Element] = {}
    for child in element:
        if child.tag not in ARGUMENT_TAGS:
            continue
        source = child.get("sr", "")
        match = re.fullmatch(r"arg(\d+)", source)
        if match:
            result[int(match.group(1))] = child
    return result


def plugin_templates_for_code(code: int) -> list[dict]:
    data = Path(__file__).resolve().parents[1] / "data" / "plugin-templates.json"
    if not data.exists():
        return []
    return [
        t for t in json.loads(data.read_text(encoding="utf-8")).get("templates", [])
        if t.get("action_code") == code
    ]


def validate_plugin_action(element: ET.Element, templates: list[dict]) -> list[str]:
    """Accept only a Bundle layout exactly observed in an extracted template."""
    actual_signature = [
        {"tag": child.tag, "sr": child.get("sr", "")}
        for child in element if child.tag != "code"
    ]
    for template in templates:
        if actual_signature != template.get("argument_signature"):
            continue
        if element.findtext("Str[@sr='arg1']", "") != template.get("package", ""):
            continue
        if element.findtext("Str[@sr='arg2']", "") != template.get("activity", ""):
            continue
        expected = ET.fromstring(template["action_xml"])
        actual_vals = element.find("./Bundle/Vals")
        expected_vals = expected.find("./Bundle/Vals")
        if actual_vals is None or expected_vals is None:
            continue
        if [node.tag for node in actual_vals] != [node.tag for node in expected_vals]:
            continue
        return []
    return [
        f"plugin Action code {element.findtext('code')} does not match an evidence-backed Bundle template"
    ]


def validate_component(element: ET.Element, kind: str) -> list[str]:
    errors: list[str] = []
    code_text = element.findtext("code")
    label = element.tag
    if code_text is None or not code_text.isdigit():
        return [f"{label} missing integer code"]
    item = action_by_code(int(code_text)) if kind == "Action" else context_by_code(kind, int(code_text))
    if item is None:
        if kind == "Action":
            templates = plugin_templates_for_code(int(code_text))
            if templates:
                return validate_plugin_action(element, templates)
        return [f"unknown {'action' if kind == 'Action' else kind.lower() + ' context'} code {code_text}"]
    expected = {argument["position"]: argument for argument in item["arguments"]}
    actual = element_arguments(element)
    if set(actual) != set(expected):
        errors.append(f"{label} code {code_text} arguments {sorted(actual)} do not exactly match catalog positions {sorted(expected)}")
        return errors
    for position, node in actual.items():
        expected_type = expected[position]["xml_type"]
        if node.tag != expected_type:
            errors.append(f"{label} code {code_text} arg{position} type {node.tag} does not match catalog {expected_type}")
    return errors


def validate_day_context(element: ET.Element) -> list[str]:
    if element.get("sr") is None:
        return ["Day context requires sr"]
    children = list(element)
    if not children:
        return ["Day context requires at least one selection"]
    seen: dict[str, list[int]] = {"mnth": [], "wday": [], "mday": []}
    rules = {"mnth": (0, 11), "wday": (1, 7), "mday": (1, 31)}
    for child in children:
        match = re.fullmatch(r"(mnth|wday|mday)(\d+)", child.tag)
        if not match or child.text is None or not child.text.isdigit():
            return [f"invalid Day child {child.tag}"]
        prefix, index = match.group(1), int(match.group(2))
        value = int(child.text)
        low, high = rules[prefix]
        if not low <= value <= high:
            return [f"Day {child.tag} value {value} outside [{low}, {high}]"]
        seen[prefix].append(index)
    for prefix, indexes in seen.items():
        if indexes and sorted(indexes) != list(range(len(indexes))):
            return [f"Day {prefix} indexes must be consecutive from 0"]
    return []


def validate_location_context(element: ET.Element) -> list[str]:
    if element.get("sr") is None:
        return ["Loc context requires sr"]
    expected = ["lat", "long", "rad"]
    tags = [child.tag for child in element]
    if tags not in (expected, ["cname", *expected]):
        return ["Loc children must be lat,long,rad or cname,lat,long,rad"]
    for key in expected:
        try:
            float(element.findtext(key, ""))
        except ValueError:
            return [f"Loc {key} must be numeric"]
    if "cname" in tags and not (element.findtext("cname") or "").strip():
        return ["Loc cname must be non-empty when present"]
    return []


def validate_root(root: ET.Element) -> list[str]:
    errors: list[str] = []
    if root.tag != "TaskerData":
        return [f"root must be TaskerData, got {root.tag}"]
    if root.get("sr") != "":
        errors.append("TaskerData sr must be empty")
    if root.get("dvi") is None or root.get("tv") is None:
        errors.append("TaskerData requires dvi and tv")
    return errors


def validate_policy(root: ET.Element) -> list[str]:
    errors: list[str] = []
    # Inspect executable Tasker strings only. Plugin Bundle metadata contains
    # documentation placeholders such as `%s`, which are not Tasker variables.
    variable_text = "\n".join(node.text or "" for node in root.findall(".//Str"))
    for token in re.findall(r"%([A-Za-z][A-Za-z0-9_]*)", variable_text):
        base = token.rstrip("0123456789")
        if len(base) < 3:
            errors.append(f"invalid Tasker variable base name %{token}: minimum length is 3")
    for task in root.findall("Task"):
        name = task.findtext("nme", "")
        if not name.startswith(CAPABILITY_PREFIX):
            continue
        if not re.search(r" v\d+$", name):
            errors.append(f"capability task {name!r} lacks version suffix")
        task_xml = ET.tostring(task, encoding="unicode")
        if re.search(r"eval\s*\(", task_xml, flags=re.IGNORECASE):
            errors.append(f"capability task {name!r} contains eval()")
        action_names = []
        for action in task.findall("Action"):
            code = action.findtext("code")
            if code and code.isdigit():
                item = action_by_code(int(code))
                action_names.append(item["name"] if item else "")
        if "Return" not in action_names:
            errors.append(f"capability task {name!r} requires a Return action")
    return errors


def validate(root: ET.Element, policy: bool) -> list[str]:
    errors = validate_root(root)
    for action in root.findall(".//Action"):
        errors.extend(validate_component(action, "Action"))
    for event in root.findall(".//Event"):
        errors.extend(validate_component(event, "Event"))
    for state in root.findall(".//State"):
        errors.extend(validate_component(state, "State"))
    for day in root.findall(".//Day"):
        errors.extend(validate_day_context(day))
    for loc in root.findall(".//Loc"):
        errors.extend(validate_location_context(loc))
    if policy:
        errors.extend(validate_policy(root))
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xml")
    parser.add_argument("--policy", action="store_true")
    args = parser.parse_args()
    try:
        root = ET.parse(args.xml).getroot()
    except ET.ParseError as error:
        print(f"XML parse error: {error}")
        return 1
    errors = validate(root, args.policy)
    print("PASS" if not errors else "\n".join(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
