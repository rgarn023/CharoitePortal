#!/usr/bin/env python3
"""Classify trusted GitHub Actions Next build failures using METADATA ONLY.

Never open job logs, issues, source patches, private data, or device data.
No AI/API, Wine, APK or commands from an event. Fixed categories only.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


MAX_BYTES = 256 * 1024
STAGES = (
    ("Verify Next multi-engine isolation tests", "NEXT_STATIC_REGRESSION"),
    ("Verify game folder import never auto-launches", "PORTAL_IMPORT_REGRESSION"),
    ("Verify V28 historical SCM STATE and SetupAPI fixed classes", "V28_SYNTHETIC_JAVA_TEST"),
    ("Get pinned LGPL Winlator upstream source", "PINNED_UPSTREAM_SOURCE"),
    ("Install build dependencies", "BUILD_DEPENDENCIES"),
    ("Create immutable versioned Next public GitHub Release", "NEXT_RELEASE_PUBLICATION"),
)
# Other failures: no false diagnosis. Never emit arbitrary step names.
def classify(jobs: object) -> tuple[str, int]:
    if not isinstance(jobs, list) or len(jobs) > 100:
        raise ValueError("Invalid job list")
    failed = []
    for job in jobs:
        if not isinstance(job, dict):
            raise ValueError("Invalid job")
        if job.get("conclusion") != "failure":
            continue
        steps = job.get("steps", [])
        if not isinstance(steps, list) or len(steps) > 300:
            raise ValueError("Invalid step list")
        for step in steps:
            if not isinstance(step, dict):
                raise ValueError("Invalid step entry")
            if step.get("conclusion") == "failure":
                name = step.get("name", "")
                if not isinstance(name, str):
                    raise ValueError("Invalid step name")
                known = next((value for prefix, value in STAGES if name.startswith(prefix)), None)
                if known is None and "gradle" in name.lower():
                    known = "ANDROID_GRADLE_BUILD"
                if known is None and "sign" in name.lower():
                    known = "APK_SIGNING_GATE"
                if known is None and ("artifact" in name.lower() or "upload" in name.lower()):
                    known = "APK_ARTIFACT_GATE"
                failed.append(known or "OTHER_CI_STEP")
        if not any(step.get("conclusion") == "failure" for step in steps):
            failed.append("UNKNOWN_FAILED_JOB_STAGE")
    if not failed:
        return "NO_FAILED_JOB_IN_PAYLOAD", 0
    return (failed[0] if len(set(failed)) == 1 else "MULTIPLE_CI_FAILURE_STAGES",
            len(failed))


def render(jobs: object, run_id: str, commit: str, repo: str) -> str:
    if not re.fullmatch(r"[1-9][0-9]{0,19}", run_id):
        raise ValueError("Invalid run ID")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid source commit")
    if repo != "rgarn023/CharoitePortal":
        raise ValueError("Unexpected repository")
    category, count = classify(jobs)
    link = "https://github.com/" + repo + "/actions/runs/" + run_id
    return ("# Charoite Next CI failure watch (free)\n\n"
            + "Generated from GitHub Actions **step-status metadata only**. "
            + "No logs, error contents or phone data were read or copied.\n\n"
            + "- Failed trusted main run: [" + run_id + "](" + link + ")\n"
            + "- Source commit: `" + commit + "`\n"
            + "- Bounded failure classification: **" + category + "**\n"
            + "- Failed steps detected: **" + str(count) + "**\n"
            + "- [Project handoff](https://github.com/" + repo
            + "/blob/main/docs/CURRENT_HANDOFF.md)\n\n"
            + "**Action:** Open the linked CI run for details. This category is NOT a "
            + "root cause diagnosis. Known one-version-stale test assertions may separately "
            + "produce a DRAFT PR; all other errors require engineering review.\n\n"
            + "**Safety:** No paid AI/API, no Wine, no APK install, no old generation "
            + "access, no source edits and no automatic PR merge. "
            + "Only the latest observed failure is shown here.\n")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--jobs", required=True)
    p.add_argument("--run-id", required=True)
    p.add_argument("--commit", required=True)
    p.add_argument("--repo", required=True)
    p.add_argument("--out", required=True)
    args = p.parse_args()
    file = Path(args.jobs)
    if file.is_symlink() or file.stat().st_size > MAX_BYTES:
        raise ValueError("Missing or oversized CI metadata")
    payload = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("jobs"), list):
        raise ValueError("Expected GitHub jobs object")
    data = render(payload["jobs"], args.run_id, args.commit, args.repo)
    output = Path(args.out)
    output.write_text(data, encoding="utf-8")
    print("CHAROITE_FREE_FAILURE_WATCH=CLASSIFIED")
    print(classify(payload["jobs"])[0])


if __name__ == "__main__":
    main()
