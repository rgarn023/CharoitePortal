# Charoite Next — controlled agent workflow

**Current status:** Source and offline guards are installed. The actual Codex
API call and PR creation are **OFF** unless the repository owner explicitly
enables them. The phone's existing GitHub issue upload/triage keeps working.

## Owner's one-time setup (NEVER put API keys in an issue or APK)

1. Obtain a separately billed OpenAI API key at
   https://platform.openai.com/api-keys (ChatGPT subscriptions do not
   automatically supply API billing).
2. Open https://github.com/rgarn023/CharoitePortal/settings/secrets/actions
   and add a **repository Actions secret** named `OPENAI_API_KEY`. Never
   insert the key in source, an Android app, issue, chat message or workflow
   variable.
3. In https://github.com/rgarn023/CharoitePortal/settings/actions
   check whether GitHub Actions is permitted to **create pull requests**
   using the built-in `GITHUB_TOKEN`. If this restriction prevents draft
   PR creation, enable that repository setting; no automatic approvals or
   merges are performed.
4. Only after reviewing the scope/cost controls, create a repository
   Actions **variable** named `CHAROITE_AGENT_ENABLED` with the literal
   value `true` at
   https://github.com/rgarn023/CharoitePortal/settings/variables/actions .
   Set it to `false` or delete it at any time to disable AI calls.

Once enabled, GitHub periodically checks **at most one** eligible, owner-
submitted, schema-verified and GitHub-bot-classified diagnostic issue every
three hours. For an eligible issue, the repository's Codex Action investigates
the known Wine28 child-process loader problem and may propose a small patch.
Only allowlisted Wine Java, versioned Wine patches and matching tests may
cross the patch boundary. The next job re-checks the patch independently and
may open a **DRAFT** pull request. There is no automatic merging or release,
no automatic Android installation, and no Wine execution or scratch cleanup.

If Codex finds insufficient evidence and produces no change, the issue is
marked as analyzed and is not charged again automatically. A draft PR branch
or a previous agent-result comment also blocks repeated analysis.

## Workflow files

- `charoite-controlled-codex.yml` — scheduled and manually dispatchable,
  guarded by the repository variable. The OpenAI API key exists ONLY in
  the Codex action step, never in the PR-writing job.
- `select_issue.py` — accepts only real `rgarn023` phone issues whose exact
  canonical JSON and hashed ID were validated by GitHub Actions.
- `guard_patch.py` — checks path allowlist, mode, sizes, count, diff/check,
  rejects deletion/binary/symlink, and re-verifies after applying the patch.
- `charoite-agent-selftest.yml` — offline, **no secret**, no AI spending,
  no Wine execution; tests eligibility, allowed paths and workflow structure.

## Safety and status

Do NOT rerun v1–v9 Wine tests. Preserve the original stable Portal, Wine22,
all games, prefixes, saved data and rootfs. The modern Wine28 startup
`get_new_process_info success=0 exit_code=1` and `kernel32 c0000135`
remain unresolved until a real, independently verified fix is tested.
The GitHub repository remains PUBLIC. Every draft PR requires review.
The system cannot run device hardware checks or install APKs silently.

The confirmed phone diagnostic is Issue #1:
https://github.com/rgarn023/CharoitePortal/issues/1 .
