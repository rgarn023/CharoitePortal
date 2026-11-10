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



# Wine29 V28 issue drafts are manually submitted by the owner; no tokens/API.
# This schema does not alter historical Wine28 V9 reporting or its classifier.
V28_PREFIX = "[device-report] Wine29 V28 "
V28_FIELDS = (
    "wineboot_finished", "internal_defaultinstall_seen", "helper_attempted",
    "helper_finished", "helper_log_cap", "helper_timeout", "inf_open_failure",
    "setupapi_error", "arm64_section_seen", "rpcss_creation_attempt_seen",
    "scm_query_attempted", "scm_error_1060", "scm_service_state",
    "rpcss_registry_root", "rpcss_registry_imagepath",
    "rpcss_registry_start", "rpcss_registry_type",
)
V28_HEADER = "Charoite Next V28 report. Sanitized fixed markers only."
V28_SUFFIX = ". This issue does not authorize another Wine test."


def _object_without_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Repeated report key")
        result[key] = value
    return result


def validate_v28(title: str, body: str):
    """Strictly validate the PUBLIC issue; never print or execute its contents."""
    if not title.startswith(V28_PREFIX) or len(body.encode("utf-8")) > 4096:
        raise ValueError("Unexpected Wine29 V28 title/length")
    rows = body.splitlines()
    if len(rows) != 5 or rows[0] != V28_HEADER or rows[1] or rows[3]:
        raise ValueError("Unexpected Wine29 V28 issue envelope")
    raw = rows[2]
    report = json.loads(raw, object_pairs_hook=_object_without_duplicate_keys)
    fixed = {"schema", "package", "generation", "submission_read_only",
             "collector_executed_wine", "result", *V28_FIELDS}
    if not isinstance(report, dict) or set(report) != fixed:
        raise ValueError("Unsupported Wine29 V28 schema keys")
    if (report["schema"] != "charoite-next.phone-wine29-v28.v1"
            or report["package"] != "com.charoitx"
            or report["generation"] != "wine29-v28"
            or report["submission_read_only"] is not True
            or report["collector_executed_wine"] is not False
            or report["result"] not in ("OBSERVED", "PARTIAL", "BLOCKED", "FAIL", "UNKNOWN")):
        raise ValueError("Invalid Wine29 V28 report identity")
    for name in V28_FIELDS:
        if report[name] is not None and type(report[name]) is not bool:
            raise ValueError("Invalid Wine29 V28 marker type")
    report_id = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    if title != V28_PREFIX + report_id or rows[4] != "Report ID " + report_id + V28_SUFFIX:
        raise ValueError("Mismatched Wine29 V28 report fingerprint")
    return report_id, report


def triage_v28(title: str, body: str) -> str:
    report_id, r = validate_v28(title, body)
    if r["helper_log_cap"] is True:
        blocker = "DefaultInstall helper exceeded bounded diagnostic output"
        next_check = "Narrow helper tracing in a NEW, unconsumed generation"
    elif r["helper_timeout"] is True:
        blocker = "DefaultInstall helper reached bounded execution deadline"
        next_check = "Examine source-level blocking calls before designing a NEW generation"
    elif r["inf_open_failure"] is True:
        blocker = "Reported SetupAPI INF-open failure marker"
        next_check = "Verify isolated C: INF mapping and pinned SetupAPI behavior"
    elif r["setupapi_error"] is True:
        blocker = "Reported SetupAPI error marker"
        next_check = "Review source for the specific SetupAPI failure stage"
    elif r["rpcss_registry_root"] is False:
        blocker = "Finalized V28 registry scan reports exact RpcSs root absent"
        next_check = "Examine INF AddService registration path in source; never rerun V28"
    elif r["scm_query_attempted"] is False:
        blocker = "RpcSs SCM query was blocked by an earlier safety gate"
        next_check = "Diagnose Wineboot/DefaultInstall gate before a new generation"
    elif r["rpcss_registry_root"] is True and r["scm_service_state"] is True:
        blocker = "Phone reports RpcSs registry root and SCM service-state markers"
        next_check = "Treat as preliminary evidence only; verify behavior separately"
    else:
        blocker = "No confirmed RpcSs registration from selected phone markers"
        next_check = "Engineering source review required before another diagnostic"
    def yes_no_unknown(value):
        return "yes" if value is True else "no" if value is False else "unknown"
    return (
        "Automated Charoite Next Wine29 V28 intake: **validated fixed-marker schema**.\n\n"
        + "- Report ID: " + report_id + "\n"
        + "- Result reported by device: " + r["result"] + "\n"
        + "- Classification: " + blocker + "\n"
        + "- Helper ran: " + yes_no_unknown(r["helper_attempted"]) + "\n"
        + "- Helper log cap exceeded: " + yes_no_unknown(r["helper_log_cap"]) + "\n"
        + "- SCM query attempted: " + yes_no_unknown(r["scm_query_attempted"]) + "\n"
        + "- Exact RpcSs registry root present: " + yes_no_unknown(r["rpcss_registry_root"]) + "\n"
        + "- SCM service state observed: " + yes_no_unknown(r["scm_service_state"]) + "\n"
        + "- Recommended NEXT source investigation: " + next_check + "\n\n"
        + "**Do not rerun, delete, clean, or repurpose consumed V28 or earlier Wine scratch.** "
        + "This comment did not execute Wine, open old evidence, publish an APK, "
        + "modify source, or invoke a paid AI API. A browser submission is not phone attestation."
    )


def validate(title: str, body: str):
    if title.startswith(V28_PREFIX):
        return validate_v28(title, body)
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
    if title.startswith(V28_PREFIX):
        return triage_v28(title, body)
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
