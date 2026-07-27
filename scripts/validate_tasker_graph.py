#!/usr/bin/env python3
"""Validate Tasker ID uniqueness and Profile/Project references (supports UUID project IDs)."""
from __future__ import annotations

import argparse
import re
import xml.etree.ElementTree as ET


def _resolve_int(text: str | None) -> int | None:
    """Return int if text matches a basic integer, else None."""
    if text is None:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def validate(root: ET.Element) -> list[str]:
    errors: list[str] = []

    # 1. Direct root children only (reject nested topology)
    profiles = root.findall("Profile")
    projects = root.findall("Project")
    tasks = root.findall("Task")

    # Reject nested Profile/Task under Project
    for proj in projects:
        for nested in proj:
            if nested.tag in ("Profile", "Task"):
                errors.append(f"Project contains nested <{nested.tag}> element")

    # 2. Build typed ID sets
    profile_ids: set[int] = set()
    task_ids: set[int] = set()
    # Track every known integer ID and its associated kind(s) for pids/tids kind-checking.
    # Profile and Task IDs are SEPARATE namespaces — a Profile id and a Task id can overlap.
    known_kinds: dict[int, set[str]] = {}

    seen_profile_ids: set[int] = set()
    for prof in profiles:
        text = prof.findtext("id")
        if text is not None:
            try:
                val = int(text)
            except ValueError:
                errors.append(f"Profile has non-integer id {text!r}")
                continue
            if val in seen_profile_ids:
                errors.append(f"duplicate Profile id {val}")
            seen_profile_ids.add(val)
            profile_ids.add(val)
            known_kinds.setdefault(val, set()).add("Profile")

    seen_task_ids: set[int] = set()
    for task in tasks:
        text = task.findtext("id")
        if text is not None:
            try:
                val = int(text)
            except ValueError:
                errors.append(f"Task has non-integer id {text!r}")
                continue
            if val in seen_task_ids:
                errors.append(f"duplicate Task id {val}")
            seen_task_ids.add(val)
            task_ids.add(val)
            known_kinds.setdefault(val, set()).add("Task")

    # 3. Project uses UUID strings (already handled, keep as-is)
    project_str_ids: dict[str, str] = {}
    for proj in projects:
        text = proj.findtext("id")
        if text is not None:
            if text in project_str_ids:
                errors.append(f"duplicate project id {text!r}")
            project_str_ids[text] = "Project"

    # 4. mid0/mid1 must resolve to task_ids
    for profile in profiles:
        pid = profile.findtext("id", "?")
        for field in ("mid0", "mid1"):
            text = profile.findtext(field)
            if text is not None:
                try:
                    val = int(text)
                except ValueError:
                    errors.append(f"Profile {pid} {field} is non-integer {text!r}")
                    continue
                if val not in task_ids:
                    errors.append(f"Profile {pid} {field} references missing task id {val}")

    # 5. pids/tids strict validation
    for project in projects:
        # pids
        pids_text = project.findtext("pids")
        if pids_text is not None:
            pids_entries = []
            for entry in filter(None, pids_text.split(",")):
                entry = entry.strip()
                try:
                    val = int(entry)
                except ValueError:
                    errors.append(f"Project pids has non-integer entry {entry!r}")
                    continue
                if val in pids_entries:
                    errors.append(f"Project pids has duplicate entry {val}")
                pids_entries.append(val)
                if val not in known_kinds:
                    errors.append(f"Project pids references missing id {val}")
                elif "Profile" not in known_kinds[val]:
                    kinds_str = ", ".join(sorted(known_kinds[val]))
                    errors.append(f"Project pids entry {val} refers to {kinds_str}, expected Profile")
            # Every root Profile must appear in pids
            for pid in sorted(profile_ids):
                if pid not in pids_entries:
                    errors.append(f"Project pids missing root Profile id {pid}")

        # tids
        tids_text = project.findtext("tids")
        if tids_text is not None:
            tids_entries = []
            for entry in filter(None, tids_text.split(",")):
                entry = entry.strip()
                try:
                    val = int(entry)
                except ValueError:
                    errors.append(f"Project tids has non-integer entry {entry!r}")
                    continue
                if val in tids_entries:
                    errors.append(f"Project tids has duplicate entry {val}")
                tids_entries.append(val)
                if val not in known_kinds:
                    errors.append(f"Project tids references missing id {val}")
                elif "Task" not in known_kinds[val]:
                    kinds_str = ", ".join(sorted(known_kinds[val]))
                    errors.append(f"Project tids entry {val} refers to {kinds_str}, expected Task")
            # Every root Task must appear in tids
            for tid in sorted(task_ids):
                if tid not in tids_entries:
                    errors.append(f"Project tids missing root Task id {tid}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("xml")
    args = parser.parse_args()
    try:
        root = ET.parse(args.xml).getroot()
    except ET.ParseError as error:
        print(f"XML parse error: {error}")
        return 1
    errors = validate(root)
    print("PASS" if not errors else "\n".join(errors))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
