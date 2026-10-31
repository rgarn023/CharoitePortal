#!/usr/bin/env python3
"""Select ONE previously validated, owner-submitted Charoite phone report.

Runs on GitHub Actions without an OpenAI key. The issue and its comments are
UNTRUSTED data. Nothing in them is interpreted as a command or an AI prompt.
"""
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = "rgarn023/CharoitePortal"
MARKER = "Charoite autonomous agent result:"
AGENT_BRANCH_PREFIX = "automation/charoite-report-"

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "next-generation"))
from triage_phone_report import validate


def eligible(issue, comments, branch_exists=False):
    if issue.get("user", {}).get("login") != "rgarn023":
        return None
    if issue.get("state") != "open" or "pull_request" in issue:
        return None
    try:
        report_id, data = validate(issue.get("title", ""), issue.get("body", ""))
    except (ValueError, TypeError, KeyError, json.JSONDecodeError):
        return None
    if not (data["internal_child_failed"] and data["pe_kernel32_missing"]):
        return None
    authenticated = False
    for comment in comments:
        if comment.get("user", {}).get("login") != "github-actions[bot]":
            continue
        body = comment.get("body", "")
        if MARKER in body:
            return None  # Prevent repeated API charges; one attempt per issue.
        if ("Automated Charoite Next diagnostic intake: **validated**." in body
                and "Report ID: " + report_id in body
                and "Wineboot child process initialization failed" in body):
            authenticated = True
    if not authenticated or branch_exists:
        return None
    number = issue.get("number")
    if type(number) is not int or number < 1 or number > 99999999:
        return None
    return str(number), report_id


def api(path, token):
    url = "https://api.github.com/repos/" + REPO + "/" + path
    req = urllib.request.Request(url, headers={
        "Accept": "application/vnd.github+json",
        "Authorization": "Bearer " + token,
        "X-GitHub-Api-Version": "2022-11-28",
    })
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


def branch_exists(issue_no, token):
    # A prior branch is sufficient to skip retries, even if a PR was closed.
    path = "git/ref/heads/" + AGENT_BRANCH_PREFIX + str(issue_no)
    try:
        api(path, token)
        return True
    except urllib.error.HTTPError as ex:
        if ex.code == 404:
            return False
        raise


def pick(preferred=None):
    token = os.environ["GH_TOKEN"]
    if preferred is not None:
        if not re.fullmatch(r"[1-9][0-9]{0,7}", preferred):
            raise ValueError("Invalid issue number")
        issues = [api("issues/" + preferred, token)]
    else:
        issues = api("issues?state=open&sort=created&direction=desc&per_page=30", token)
    for issue in issues:
        number = issue.get("number")
        if type(number) is not int or number < 1:
            continue
        comments = api("issues/" + str(number) + "/comments?per_page=100", token)
        found = eligible(issue, comments, branch_exists(number, token))
        if found:
            return found
    return None


def main():
    preferred = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1] else None
    selection = pick(preferred)
    if selection:
        issue_no, report_id = selection
        print("Validated phone diagnostic Issue #" + issue_no
              + " (report ID " + report_id + ")")
    else:
        issue_no, report_id = "", ""
        print("No unprocessed, owner-verified phone diagnostic found.")
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as f:
        f.write("issue_number=" + issue_no + "\nreport_id=" + report_id + "\n")


if __name__ == "__main__":
    main()
