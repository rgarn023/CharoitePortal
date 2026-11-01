#!/usr/bin/env python3
"""Read-only allowlist validation for PUBLIC Charoite Next phone issues.

Never eval GitHub issue data or execute any code supplied by a phone.
"""
import hashlib
import json
import sys

PREFIX = "[device-report] Wine28 v9 "
FIELDS_V1 = {
    "schema": str, "package": str, "generation": str,
    "read_only": bool, "collector_executed_wine": bool,
    "pe_bytes": int, "server_bytes": int,
    "server_new_process_calls": int, "server_new_process_success": bool,
    "internal_child_failed": bool, "pe_kernel32_missing": bool,
    "pe_apiset_failed": bool, "server_no_such_file": int,
    "internal_wineboot_init": bool, "prefix_read": bool,
    "games_or_saves_read": bool,
}
# Preserve exact compatibility with already uploaded V1 issue reports.
FIELDS_V2 = {**FIELDS_V1, "host_page_size_bytes": int}


def validate(title: str, body: str):
    if not title.startswith(PREFIX) or len(body.encode("utf-8")) > 8192:
        raise ValueError("Unexpected title or oversized report")
    rows = body.splitlines()
    if len(rows) < 5 or rows[0] != "Automated Charoite Next phone diagnosis. Sanitized JSON only.":
        raise ValueError("Unexpected report envelope")
    raw = rows[2]
    report = json.loads(raw)
    if not isinstance(report, dict):
        raise ValueError("Unexpected JSON report")
    schema = report.get("schema")
    fields = (FIELDS_V1 if schema == "charoite-next.phone-diagnostics.v1"
              else FIELDS_V2 if schema == "charoite-next.phone-diagnostics.v2"
              else None)
    if fields is None or set(report) != set(fields):
        raise ValueError("Unknown or missing report keys")
    for k, t in fields.items():
        if type(report[k]) is not t:
            raise ValueError("Invalid report field type: " + k)
    if (report["package"] != "com.charoitx"
            or report["generation"] != "wine28-v9-readonly"
            or not report["read_only"] or report["collector_executed_wine"]
            or report["prefix_read"] or report["games_or_saves_read"]):
        raise ValueError("Unsupported or unsafe report")
    for k in ("pe_bytes", "server_bytes", "server_new_process_calls",
              "server_no_such_file"):
        if report[k] < 0 or report[k] > 2 * 1024 * 1024:
            raise ValueError("Invalid report size or count")
    if schema == "charoite-next.phone-diagnostics.v2":
        page_size = report["host_page_size_bytes"]
        if page_size < 4096 or page_size > 65536 or page_size & (page_size - 1):
            raise ValueError("Invalid Android page size")
    report_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    if title != PREFIX + report_id or ("Report ID " + report_id) not in body:
        raise ValueError("Mismatched report ID")
    return report_id, report


def triage(title: str, body: str) -> str:
    report_id, report = validate(title, body)
    if report["internal_child_failed"]:
        blocker = "Wineboot child process initialization failed"
    elif report["pe_kernel32_missing"]:
        blocker = "PE loader could not load kernel32.dll"
    else:
        blocker = "No known Wineboot failure pattern found"
    page_note = ""
    if "host_page_size_bytes" in report:
        page = report["host_page_size_bytes"]
        page_note = ("- Android host memory page size: " + str(page) + " bytes\n"
                     + "- Wine 10.0 ARM64 4 KiB page prerequisite: "
                     + ("satisfied" if page == 4096 else "NOT satisfied")
                     + " (not proof of Wineboot root cause)\n")
    return (
        "Automated Charoite Next diagnostic intake: **validated**.\n\n"
        + "- Report ID: " + report_id + "\n"
        + "- Generation: Wine28 v9 **read-only**\n"
        + "- Classification: " + blocker + "\n"
        + "- Kernel32 load error: "
        + ("yes" if report["pe_kernel32_missing"] else "no") + "\n"
        + page_note
        + "- Wine executed by collector: **no**\n"
        + "- Engineering review required; **do not rerun v9**.\n\n"
        + "Deterministic classification only; no AI-driven fixes were made."
    )
