# Charoite Next — free-first guarded automation (CURRENT)

## Active $0-separately-billed-API pipeline

- Owner submits a PUBLIC GitHub phone report only after explicitly reviewing and approving its fixed, sanitized fields. Existing `charoite-phone-report-intake.yml` validates the exact schema, comments with deterministic triage and labels valid reports `charoite-validated-report` and `charoite-engineering-review`. Submission still needs the owner's browser confirmation; no phone token or remote auto-upload is installed.
- `charoite-next.yml` continues automatic Python/JVM/Android regression gates, artifact signing and immutable Next versioned release publication for trusted main changes. Existing stable Portal identity `com.charoite` and its release channel remain separate from experimental `com.charoitx`.
- `charoite-free-known-fix.yml` reacts to FAILED trusted main-branch Next builds. `known_test_drift.py` derives consistent code/name/tag from the source and offers changes ONLY for an exact one-build-outdated version assertion within five reviewed static test files. It runs offline gates and opens an isolated DRAFT PR plus requests a static CI check; nothing is auto-merged. Any compiler error, new Wine symptom or other issue is outside this repair rule. If PR creation is disallowed by repo Actions settings, a draft branch may be created but requires owner review and GitHub permissions adjustment.
- `charoite-free-status.yml` runs weekly each Monday and on manual dispatch, updates ONE public GitHub status issue and a workflow job summary with only GitHub release/CI metadata. It does not scrape phone logs or post individual private data.
- `charoite-free-ci-watch.yml` runs ONLY for failed trusted `main` Next builds, reads GitHub job-status metadata (NOT logs), and updates [the single public CI-failure issue #6](https://github.com/rgarn023/CharoitePortal/issues/6) with a fixed-category summary and run link. A separate regression fixture reproduces a prior archived-V23 AAPT-version ambiguity and verifies the active APK gate against the REAL repository. No AI inference or automatic Wine fixes are claimed.
- `charoite-agent-selftest.yml` runs all offline guards on automation changes and explicit dispatch, with NO OpenAI API use and NO Wine execution.

**Cost:** $0 in separately billed AI API requests. Public-repository standard GitHub Actions runners are generally free, subject to GitHub policies, storage limits and repo eligibility. Standard mobile network/energy costs are not included; self-hosted AI hardware is not provided. This is NOT an autonomous general-purpose AI developer.

**Hard safety limits:** no Wine/wineserver or device process creation by Actions, no V28 rerun, no old scratch accesses, no cleanup or prefix/game/save modification, no unattended APK install, no automated PR merges, no token in an APK, no edits to stable Portal. The owner explicitly approves new isolated runtime experiments and Android PackageInstaller confirmation. Historical V28 reviews still require separate bounded read-only authorization.

**Paid API agent remains DORMANT:** `charoite-controlled-codex.yml` is still manual-only with separate explicit API key, repo flag and per-run billing consent; we do not enable, dispatch or schedule it.

---

## Prior manual workflow (retained for historical context)

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
