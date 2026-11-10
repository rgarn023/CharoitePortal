#!/usr/bin/env python3
"""Free, deterministic repair CANDIDATE for stale Next-version test literals.

No AI, network, Wine, phone access, source changes, signing, releases, or merge.
Only five reviewed static regression tests may change. This is never a fix for
new runtime bugs; the workflow opens a DRAFT PR requiring human review.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re

TARGETS = (
    "next-generation/tests/test_wine29_v28_free_issue_intake.py",
    "next-generation/tests/test_wine29_v28_preserved_readonly_contract.py",
    "next-generation/tests/test_wine29_v28_scoped_triage_contract.py",
    "next-generation/tests/test_next_system_reporting_update_contract.py",
    "next-generation/tests/test_next_inapp_install_contract.py",
)
MAX_CHANGED = 5
MAX_REPLACEMENTS = 80
MAX_FILE_BYTES = 96 * 1024


class UnsafeVersionDrift(ValueError):
    """Fail closed when the authoritative release metadata disagree."""


def exactly_one(pattern: str, data: str, label: str) -> str:
    matches = re.findall(pattern, data)
    if len(matches) != 1:
        raise UnsafeVersionDrift("Missing or ambiguous " + label)
    return matches[0]


def current_version(root: Path) -> tuple[int, str]:
    prep = (root / "next-generation/prepare_next.py").read_text(encoding="utf-8")
    workflow = (root / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")
    code = int(exactly_one(
        r'text = text\.replace\("versionCode 33", "versionCode ([1-9][0-9]*)"\)',
        prep, "Next versionCode"))
    name = exactly_one(
        r'''text = text\.replace\('versionName "11\.2"', 'versionName "([^"]+)"'\)''',
        prep, "Next versionName")
    if re.fullmatch(r"11\.2-next\.0\.[1-9][0-9]*", name) is None:
        raise UnsafeVersionDrift("Unsupported Next version identity")
    aapt = exactly_one(
        r"package: name='com\.charoitx' versionCode='([0-9]+)' versionName='([^']+)'",
        workflow, "APK identity gate")
    # exactly_one returns a tuple for the two capture groups.
    if tuple(aapt) != (str(code), name):
        raise UnsafeVersionDrift("APK version gate differs from source")
    tag = exactly_one(r"TAG=charoite-next-vc([0-9]+)", workflow, "versioned release tag")
    if int(tag) != code:
        raise UnsafeVersionDrift("Next tag differs from APK version")
    if code < 2:
        raise UnsafeVersionDrift("Invalid versionCode")
    return code, name


def plan(root: Path) -> dict[str, str]:
    """Return scoped replacement file content without writing anything."""
    code, name = current_version(root)
    patch = int(name.rsplit(".", 1)[1])
    if patch < 1:
        raise UnsafeVersionDrift("Cannot identify previous patch")
    prior = name.rsplit(".", 1)[0] + "." + str(patch - 1)
    old_code = str(code - 1)
    substitutions = (
        ("versionCode='" + old_code + "'", "versionCode='" + str(code) + "'"),
        ("versionCode " + old_code, "versionCode " + str(code)),
        ("charoite-next-vc" + old_code, "charoite-next-vc" + str(code)),
        (prior, name),
    )
    changes: dict[str, str] = {}
    total = 0
    for relative in TARGETS:
        file = root / relative
        if file.is_symlink() or not file.is_file() or file.stat().st_size > MAX_FILE_BYTES:
            raise UnsafeVersionDrift("Missing/unsafe allowlisted test file")
        original = file.read_text(encoding="utf-8")
        updated = original
        for before, after in substitutions:
            count = updated.count(before)
            total += count
            if count:
                updated = updated.replace(before, after)
        if updated != original:
            changes[relative] = updated
    if len(changes) > MAX_CHANGED or total > MAX_REPLACEMENTS:
        raise UnsafeVersionDrift("Candidate exceeds tiny static-test bound")
    return changes


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true",
                        help="Modify only reviewed version-literal regression tests")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    changes = plan(root)
    if args.apply:
        for name, content in changes.items():
            (root / name).write_text(content, encoding="utf-8")
    print("CHAROITE_FREE_KNOWN_TEST_DRIFT=" +
          ("DRAFT_CANDIDATE" if changes else "NO_CHANGE"))
    for name in changes:
        print("ALLOWLISTED_TEST=" + name)
    print("FILES=" + str(len(changes)))
    print("NO_AI_NO_WINE_NO_RELEASE_NO_MERGE=PASS")


if __name__ == "__main__":
    main()
