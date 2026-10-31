# Charoite Next — cost-free, chat-led development (CURRENT)

**Decision (October 30, 2026):** The owner chose to avoid separately billed OpenAI API usage. The normal development route is **semi-automated and uses NO OpenAI API key**.

- **Already verified:** Charoite Next v0.56 sends explicitly opted-in, sanitized read-only phone diagnostics to public GitHub Issue #1; GitHub Actions validates and classifies them without invoking OpenAI API.
- **ChatGPT in an active conversation:** inspects the repository and classified issue, researches the Wine28 failure, edits code directly on `main` using connected GitHub tools, and checks Actions build/test results. ChatGPT does not keep developing between chats.
- **GitHub Actions:** runs static regressions and can build signed APK artifacts from ordinary source updates. Avoid unneeded CI runs for documentation-only changes by using `[skip ci]`.
- **User:** installs verified APK updates in place and explicitly approves any new isolated Wine experiment. Never rerun v1–v9 scratch or touch prefixes, games, saves or rootfs.
- **No API key needed.** Do NOT configure `OPENAI_API_KEY` or `CHAROITE_AGENT_ENABLED` for this free workflow.

## Paid agent parked, not active

The experimental `.github/workflows/charoite-controlled-codex.yml` is retained for possible future use but **its scheduled trigger has been REMOVED**. It can now reach a Codex API action only after an owner deliberately:
1. Obtains and adds a separately billed `OPENAI_API_KEY` repository secret;
2. Sets the repository Actions variable `CHAROITE_AGENT_ENABLED=true`; **and**
3. Manually dispatches the workflow and checks `paid_api_consent=true` for that specific run.

None of these steps is necessary or recommended for current cost-free development. No autonomous paid developer, auto-merge, auto-release, Wine execution or unattended phone install runs in this mode. GitHub Actions platform quotas and mobile/network charges are separate from OpenAI API billing.

## Existing safe automation files

- `charoite-agent-selftest.yml` — offline security/patch scope contract tests; no API, no Wine.
- `charoite-agent-pr-check.yml` — static Next tests for draft PRs; no API or signing key.
- `select_issue.py` — selects only owner-authored, schema-verified, GitHub-bot-classified reports.
- `guard_patch.py` — validates minimal Wine source/patch/test changes, rejecting sensitive paths.
- `charoite-controlled-codex.yml` — dormant, **manual-only** separately billed option, not the current development path.

## Current engineering focus

Wine28 ARM64 wineboot internal child still fails `get_new_process_info success=0 exit_code=1`; parent `kernel32.dll c0000135` remains unresolved. Affected v9 evidence is read-only and preserved. Investigate pinned loader paths/import resolution using repository source and safely selected diagnostics, then design a separately approved NEW scratch-generation test only when justified.

The public repo remains https://github.com/rgarn023/CharoitePortal; device evidence: https://github.com/rgarn023/CharoitePortal/issues/1 ; current canonical handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md .
