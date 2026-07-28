#!/usr/bin/env python3
"""Compare two Tasker XML files across four layers: custody, lexical, structural, semantic.

Usage:
    python scripts/compare_tasker_roundtrip.py <candidate.xml> <reexport.xml> [--output result.json]
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import action_by_code, context_by_code, json_result

VERDICT_EXACT = "EXACT_PASS"
VERDICT_STRUCT_REVIEW = "STRUCTURAL_PASS_SEMANTIC_REVIEW_REQUIRED"
VERDICT_SEMANTIC_NORM = "SEMANTIC_PASS_WITH_UNAPPROVED_NORMALIZATION"
VERDICT_SEMANTIC_FAIL = "SEMANTIC_FAIL"
VERDICT_UNPARSABLE = "UNPARSABLE"

ARGUMENT_TAGS = {"Str", "Int", "Bundle", "Img", "App", "ConditionList"}

# Elements that Tasker may add/remove during re-export without changing semantics
OPTIONAL_ELEMENTS = {"cdate", "edate", "note", "timer", "Highlight", "Loop", "Timeout"}


# ---------------------------------------------------------------------------
# Layer 1 — Custody (byte-level)
# ---------------------------------------------------------------------------

def compare_custody(candidate_bytes: bytes, reexport_bytes: bytes) -> dict:
    cand_sha = hashlib.sha256(candidate_bytes).hexdigest()
    rexp_sha = hashlib.sha256(reexport_bytes).hexdigest()
    return {
        "candidate_sha256": cand_sha,
        "reexport_sha256": rexp_sha,
        "byte_equal": candidate_bytes == reexport_bytes,
        "candidate_size": len(candidate_bytes),
        "reexport_size": len(reexport_bytes),
    }


# ---------------------------------------------------------------------------
# Layer 2 — Lexical (diagnostic only, does NOT decide semantics)
# ---------------------------------------------------------------------------

def compare_lexical(candidate_text: str, reexport_text: str) -> dict:
    differences = []
    cand_lines = candidate_text.splitlines(keepends=True)
    rexp_lines = reexport_text.splitlines(keepends=True)

    # XML declaration
    cand_decl = cand_lines[0] if cand_lines else ""
    rexp_decl = rexp_lines[0] if rexp_lines else ""
    if cand_decl != rexp_decl:
        differences.append({
            "path": "/xml_declaration",
            "candidate": repr(cand_decl),
            "reexport": repr(rexp_decl),
            "provisional_class": "serialization_difference",
            "suppressed": False,
        })

    # Line endings
    cand_ends = set()
    for line in cand_lines:
        if line.endswith("\r\n"):
            cand_ends.add("CRLF")
        elif line.endswith("\n"):
            cand_ends.add("LF")
        elif line.endswith("\r"):
            cand_ends.add("CR")
    rexp_ends = set()
    for line in rexp_lines:
        if line.endswith("\r\n"):
            rexp_ends.add("CRLF")
        elif line.endswith("\n"):
            rexp_ends.add("LF")
        elif line.endswith("\r"):
            rexp_ends.add("CR")
    if cand_ends != rexp_ends:
        differences.append({
            "path": "/line_endings",
            "candidate": ",".join(sorted(cand_ends)),
            "reexport": ",".join(sorted(rexp_ends)),
            "provisional_class": "serialization_difference",
            "suppressed": False,
        })

    # Encoding
    if "encoding=" in cand_decl and "encoding=" in rexp_decl:
        cand_enc = cand_decl.split("encoding=")[1].split("'")[0].split('"')[0]
        rexp_enc = rexp_decl.split("encoding=")[1].split("'")[0].split('"')[0]
        if cand_enc != rexp_enc:
            differences.append({
                "path": "/xml_declaration/encoding",
                "candidate": cand_enc,
                "reexport": rexp_enc,
                "provisional_class": "serialization_difference",
                "suppressed": False,
            })

    # General formatting detection: compare raw text to catch indentation,
    # whitespace, attribute order, empty-element syntax, etc.
    if candidate_text != reexport_text:
        # Check for indentation differences
        cand_indent = [len(line) - len(line.lstrip()) for line in cand_lines
                       if line.strip()]
        rexp_indent = [len(line) - len(line.lstrip()) for line in rexp_lines
                       if line.strip()]
        if cand_indent != rexp_indent:
            differences.append({
                "path": "/formatting/indentation",
                "candidate": str(cand_indent[:5]) + ("..." if len(cand_indent) > 5 else ""),
                "reexport": str(rexp_indent[:5]) + ("..." if len(rexp_indent) > 5 else ""),
                "provisional_class": "serialization_difference",
                "suppressed": False,
            })

        # Check for attribute order differences
        import re as _re
        cand_attrs = _re.findall(r'<(\w+)([^>]*?)/?>', candidate_text)
        rexp_attrs = _re.findall(r'<(\w+)([^>]*?)/?>', reexport_text)
        if cand_attrs != rexp_attrs:
            differences.append({
                "path": "/formatting/attribute_order",
                "candidate": str(len(cand_attrs)) + " elements",
                "reexport": str(len(rexp_attrs)) + " elements",
                "provisional_class": "serialization_difference",
                "suppressed": False,
            })

    return {"differences": differences}


# ---------------------------------------------------------------------------
# Layer 3 — Structural
# ---------------------------------------------------------------------------

def _children_order(root: ET.Element) -> list[str]:
    return [child.tag for child in root]


def _essential_children(elem: ET.Element) -> list[str]:
    """Child tags excluding optional Tasker-added elements."""
    return [child.tag for child in elem if child.tag not in OPTIONAL_ELEMENTS]


def _check_nesting(root: ET.Element) -> list[str]:
    errors = []
    for project in root.findall("Project"):
        for child in project:
            if child.tag in ("Profile", "Task"):
                errors.append(
                    f"Project contains nested <{child.tag}> element at "
                    f"/Project/{child.tag}"
                )
    return errors


def compare_structural(candidate_root: ET.Element, reexport_root: ET.Element) -> dict:
    differences = []
    cand_proj = {}
    rexp_proj = {}

    # Root tag
    cand_proj["root_tag"] = candidate_root.tag
    rexp_proj["root_tag"] = reexport_root.tag
    if candidate_root.tag != reexport_root.tag:
        differences.append({
            "path": "/root_tag",
            "candidate": candidate_root.tag,
            "reexport": reexport_root.tag,
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # Children order (top-level)
    cand_order = _children_order(candidate_root)
    rexp_order = _children_order(reexport_root)
    cand_proj["children_order"] = cand_order
    rexp_proj["children_order"] = rexp_order
    if cand_order != rexp_order:
        differences.append({
            "path": "/children_order",
            "candidate": str(cand_order),
            "reexport": str(rexp_order),
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # Counts
    for tag in ("Profile", "Project", "Task"):
        cand_count = len(candidate_root.findall(tag))
        rexp_count = len(reexport_root.findall(tag))
        cand_proj[f"count_{tag}"] = cand_count
        rexp_proj[f"count_{tag}"] = rexp_count
        if cand_count != rexp_count:
            differences.append({
                "path": f"/count_{tag}",
                "candidate": str(cand_count),
                "reexport": str(rexp_count),
                "provisional_class": "structural_difference",
                "suppressed": False,
            })

    # Nesting check
    cand_nesting_errors = _check_nesting(candidate_root)
    rexp_nesting_errors = _check_nesting(reexport_root)
    if cand_nesting_errors != rexp_nesting_errors:
        differences.append({
            "path": "/nesting",
            "candidate": str(cand_nesting_errors),
            "reexport": str(rexp_nesting_errors),
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # sr and ve attributes on each element
    for tag in ("Profile", "Project", "Task"):
        cand_elems = candidate_root.findall(tag)
        rexp_elems = reexport_root.findall(tag)
        for i, (c, r) in enumerate(zip(cand_elems, rexp_elems)):
            path_base = f"/{tag}[{i}]"
            for attr in ("sr", "ve"):
                cand_val = c.get(attr)
                rexp_val = r.get(attr)
                cand_proj[f"{path_base}/@{attr}"] = cand_val
                rexp_proj[f"{path_base}/@{attr}"] = rexp_val
                if cand_val != rexp_val:
                    differences.append({
                        "path": f"{path_base}/@{attr}",
                        "candidate": str(cand_val),
                        "reexport": str(rexp_val),
                        "provisional_class": "structural_difference",
                        "suppressed": False,
                    })

            # Essential inner elements order (excluding optional Tasker-added elements)
            cand_inner = _essential_children(c)
            rexp_inner = _essential_children(r)
            if cand_inner != rexp_inner:
                differences.append({
                    "path": f"{path_base}/children_order",
                    "candidate": str(cand_inner),
                    "reexport": str(rexp_inner),
                    "provisional_class": "structural_difference",
                    "suppressed": False,
                })
            else:
                # Check if optional elements differ — those are serialization
                cand_all = [ch.tag for ch in c]
                rexp_all = [ch.tag for ch in r]
                if cand_all != rexp_all:
                    differences.append({
                        "path": f"{path_base}/optional_elements",
                        "candidate": str(cand_all),
                        "reexport": str(rexp_all),
                        "provisional_class": "serialization_difference",
                        "suppressed": False,
                    })

    return {"differences": differences, "candidate": cand_proj, "reexport": rexp_proj}


# ---------------------------------------------------------------------------
# Layer 4 — Semantic projection
# ---------------------------------------------------------------------------

def _extract_args(element: ET.Element) -> dict:
    """Extract arguments from an Action or Event/State element."""
    args = {}
    for child in element:
        if child.tag not in ARGUMENT_TAGS:
            continue
        source = child.get("sr", "")
        if source.startswith("arg"):
            try:
                idx = int(source[3:])
            except ValueError:
                continue
            if child.tag == "Int":
                args[f"arg{idx}"] = int(child.get("val", "0"))
            elif child.tag == "Str":
                args[f"arg{idx}"] = child.text or ""
            else:
                args[f"arg{idx}"] = f"<{child.tag}>"
    return dict(sorted(args.items()))


def build_projection(root: ET.Element) -> dict:
    """Build a serialization-independent semantic projection."""
    proj = {
        "tasker_version": root.get("tv"),
        "projects": [],
        "profiles": [],
        "tasks": [],
        "references": [],
    }

    # Projects
    for project in root.findall("Project"):
        p = {
            "id": project.findtext("id"),
            "name": project.findtext("name"),
            "pids": _parse_csv_ints(project.findtext("pids")),
            "tids": _parse_csv_ints(project.findtext("tids")),
        }
        proj["projects"].append(p)

    # Profiles
    for profile in root.findall("Profile"):
        prof = {
            "id": _safe_int(profile.findtext("id")),
            "nme": profile.findtext("nme"),
            "flags": _safe_int(profile.findtext("flags")),
            "mid0": _safe_int(profile.findtext("mid0")),
            "mid1": _safe_int(profile.findtext("mid1")),
        }
        event = profile.find("Event")
        state = profile.find("State")
        if event is not None:
            prof["context_type"] = "Event"
            prof["code"] = _safe_int(event.findtext("code"))
            prof["args"] = _extract_args(event)
        elif state is not None:
            prof["context_type"] = "State"
            prof["code"] = _safe_int(state.findtext("code"))
            prof["args"] = _extract_args(state)
        else:
            prof["context_type"] = None
            prof["code"] = None
            prof["args"] = {}
        proj["profiles"].append(prof)

    # Tasks
    for task in root.findall("Task"):
        t = {
            "id": _safe_int(task.findtext("id")),
            "nme": task.findtext("nme"),
            "priority": _safe_int(task.findtext("pri")),
            "actions": [],
            "conditions": [],
        }
        for action in task.findall("Action"):
            act = {
                "code": _safe_int(action.findtext("code")),
                "args": _extract_args(action),
            }
            t["actions"].append(act)
        proj["tasks"].append(t)

    return proj


def _parse_csv_ints(text: str | None) -> list[int]:
    if not text:
        return []
    result = []
    for part in text.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


def _safe_int(text: str | None) -> int | None:
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# ID-move reclassification
# ---------------------------------------------------------------------------

def _apply_id_mapping(proj: dict, id_mapping: dict) -> None:
    """Apply ID mapping to a projection in-place."""
    for project in proj.get("projects", []):
        project["pids"] = [id_mapping.get(p, p) for p in project["pids"]]
        project["tids"] = [id_mapping.get(t, t) for t in project["tids"]]
    for profile in proj.get("profiles", []):
        if profile.get("id") in id_mapping:
            profile["id"] = id_mapping[profile["id"]]
        if profile.get("mid0") in id_mapping:
            profile["mid0"] = id_mapping[profile["mid0"]]
        if profile.get("mid1") in id_mapping:
            profile["mid1"] = id_mapping[profile["mid1"]]
    for task in proj.get("tasks", []):
        if task.get("id") in id_mapping:
            task["id"] = id_mapping[task["id"]]


def _reclassify_id_moves(cand_proj: dict, rexp_proj: dict,
                         differences: list[dict]) -> list[dict]:
    """Reclassify consistent ID renumbering as structural_difference.

    When all IDs and references change consistently (pure renumbering),
    the difference is structural, not semantic.
    """
    id_mapping: dict[int, int] = {}

    # Task ID mapping (by position)
    cand_tasks = cand_proj.get("tasks", [])
    rexp_tasks = rexp_proj.get("tasks", [])
    for i in range(min(len(cand_tasks), len(rexp_tasks))):
        c_id = cand_tasks[i].get("id")
        r_id = rexp_tasks[i].get("id")
        if c_id is not None and r_id is not None and c_id != r_id:
            id_mapping[c_id] = r_id

    # Profile ID mapping (by position)
    cand_profiles = cand_proj.get("profiles", [])
    rexp_profiles = rexp_proj.get("profiles", [])
    for i in range(min(len(cand_profiles), len(rexp_profiles))):
        c_id = cand_profiles[i].get("id")
        r_id = rexp_profiles[i].get("id")
        if c_id is not None and r_id is not None and c_id != r_id:
            id_mapping[c_id] = r_id

    if not id_mapping:
        return differences

    # Apply mapping to candidate projection and check if it matches reexport
    normalized = copy.deepcopy(cand_proj)
    _apply_id_mapping(normalized, id_mapping)

    if normalized == rexp_proj:
        # All differences are consistent ID renumbering → structural
        for diff in differences:
            if diff["provisional_class"] == "semantic_difference":
                diff["provisional_class"] = "structural_difference"

    return differences


def compare_semantic(candidate_root: ET.Element, reexport_root: ET.Element) -> dict:
    cand_proj = build_projection(candidate_root)
    rexp_proj = build_projection(reexport_root)
    differences = []

    def _diff_values(cand_val, rexp_val, path):
        if cand_val != rexp_val:
            differences.append({
                "path": path,
                "candidate": json.dumps(cand_val, ensure_ascii=False),
                "reexport": json.dumps(rexp_val, ensure_ascii=False),
                "provisional_class": "semantic_difference",
                "suppressed": False,
            })

    # tasker_version
    _diff_values(cand_proj["tasker_version"], rexp_proj["tasker_version"],
                 "/tasker_version")

    # Projects
    for i, (c, r) in enumerate(zip(cand_proj["projects"], rexp_proj["projects"])):
        for key in ("id", "name", "pids", "tids"):
            _diff_values(c[key], r[key], f"/projects[{i}]/{key}")

    if len(cand_proj["projects"]) != len(rexp_proj["projects"]):
        differences.append({
            "path": "/projects/count",
            "candidate": str(len(cand_proj["projects"])),
            "reexport": str(len(rexp_proj["projects"])),
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # Profiles
    for i, (c, r) in enumerate(zip(cand_proj["profiles"], rexp_proj["profiles"])):
        for key in ("id", "nme", "flags", "mid0", "mid1", "context_type", "code"):
            _diff_values(c[key], r[key], f"/profiles[{i}]/{key}")
        for arg_key in set(list(c.get("args", {}).keys()) + list(r.get("args", {}).keys())):
            _diff_values(c.get("args", {}).get(arg_key), r.get("args", {}).get(arg_key),
                         f"/profiles[{i}]/args/{arg_key}")

    if len(cand_proj["profiles"]) != len(rexp_proj["profiles"]):
        differences.append({
            "path": "/profiles/count",
            "candidate": str(len(cand_proj["profiles"])),
            "reexport": str(len(rexp_proj["profiles"])),
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # Tasks
    for i, (c, r) in enumerate(zip(cand_proj["tasks"], rexp_proj["tasks"])):
        for key in ("id", "nme", "priority"):
            _diff_values(c[key], r[key], f"/tasks[{i}]/{key}")
        for j, (ca, ra) in enumerate(zip(c.get("actions", []), r.get("actions", []))):
            _diff_values(ca["code"], ra["code"], f"/tasks[{i}]/actions[{j}]/code")
            for arg_key in set(list(ca.get("args", {}).keys()) + list(ra.get("args", {}).keys())):
                _diff_values(ca.get("args", {}).get(arg_key), ra.get("args", {}).get(arg_key),
                             f"/tasks[{i}]/actions[{j}]/args/{arg_key}")
        if len(c.get("actions", [])) != len(r.get("actions", [])):
            differences.append({
                "path": f"/tasks[{i}]/actions/count",
                "candidate": str(len(c.get("actions", []))),
                "reexport": str(len(r.get("actions", []))),
                "provisional_class": "structural_difference",
                "suppressed": False,
            })

    if len(cand_proj["tasks"]) != len(rexp_proj["tasks"]):
        differences.append({
            "path": "/tasks/count",
            "candidate": str(len(cand_proj["tasks"])),
            "reexport": str(len(rexp_proj["tasks"])),
            "provisional_class": "structural_difference",
            "suppressed": False,
        })

    # Reclassify consistent ID moves as structural
    differences = _reclassify_id_moves(cand_proj, rexp_proj, differences)

    return {"candidate": cand_proj, "reexport": rexp_proj, "differences": differences}


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def compute_verdict(custody: dict, structural: dict, semantic: dict) -> tuple[str, str]:
    """Compute verdict from the comparison layers."""
    if custody.get("parsing_error"):
        return VERDICT_UNPARSABLE, custody["parsing_error"]

    if custody["byte_equal"]:
        return VERDICT_EXACT, "Files are byte-identical"

    active_semantic = [d for d in semantic["differences"] if not d["suppressed"]]
    active_structural = [d for d in structural["differences"] if not d["suppressed"]]

    if active_semantic and active_structural:
        return (
            VERDICT_SEMANTIC_FAIL,
            f"{len(active_semantic)} semantic difference(s), "
            f"{len(active_structural)} structural difference(s) — requires human review",
        )

    if active_semantic:
        return (
            VERDICT_STRUCT_REVIEW,
            f"{len(active_semantic)} semantic difference(s) — "
            f"structural layer matches but semantic review required",
        )

    if active_structural:
        return (
            VERDICT_SEMANTIC_NORM,
            f"{len(active_structural)} structural difference(s) — "
            f"semantically equivalent but normalization applied (unapproved)",
        )

    return VERDICT_EXACT, "No substantive differences detected"


# ---------------------------------------------------------------------------
# Main comparison
# ---------------------------------------------------------------------------

def compare(candidate_path: str | Path, reexport_path: str | Path) -> dict:
    """Compare two Tasker XML files. Returns the full result dict."""
    cand = Path(candidate_path)
    rexp = Path(reexport_path)

    candidate_bytes = cand.read_bytes()
    reexport_bytes = rexp.read_bytes()

    # Layer 1 — Custody
    custody = compare_custody(candidate_bytes, reexport_bytes)

    # Layer 2 — Lexical
    candidate_text = candidate_bytes.decode("utf-8", errors="replace")
    reexport_text = reexport_bytes.decode("utf-8", errors="replace")
    lexical = compare_lexical(candidate_text, reexport_text)

    # Layer 3 & 4 — Structural and Semantic
    try:
        candidate_root = ET.fromstring(candidate_bytes)
        reexport_root = ET.fromstring(reexport_bytes)
    except ET.ParseError as error:
        custody["parsing_error"] = f"XML parse error: {error}"
        result = {
            "custody": custody,
            "lexical": lexical,
            "structural": {"differences": [], "candidate": {}, "reexport": {}},
            "semantic": {"candidate": {}, "reexport": {}, "differences": []},
            "differences": [],
            "verdict": VERDICT_UNPARSABLE,
            "verdict_reason": f"XML parse error: {error}",
        }
        return result

    structural = compare_structural(candidate_root, reexport_root)
    semantic = compare_semantic(candidate_root, reexport_root)

    # Combine all differences (structural + semantic + lexical)
    all_diffs = structural["differences"] + semantic["differences"] + lexical["differences"]

    verdict, verdict_reason = compute_verdict(custody, structural, semantic)

    return {
        "custody": custody,
        "lexical": lexical,
        "structural": structural,
        "semantic": semantic,
        "differences": all_diffs,
        "verdict": verdict,
        "verdict_reason": verdict_reason,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare two Tasker XML files across 4 layers"
    )
    parser.add_argument("candidate", help="Path to candidate XML file")
    parser.add_argument("reexport", help="Path to re-exported XML file")
    parser.add_argument("--output", "-o", help="Write result JSON to file")
    args = parser.parse_args()

    result = compare(args.candidate, args.reexport)

    output_json = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(output_json, encoding="utf-8")
        print(f"Result written to {args.output}")
    else:
        print(output_json)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
