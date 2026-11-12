# Charoite Portal — New Chat / Session Start

**Canonical project:** https://github.com/rgarn023/CharoitePortal (branch `main`).

## One-line instruction for a fresh ChatGPT conversation
**Continue Charoite Portal development from https://github.com/rgarn023/CharoitePortal/blob/main/docs/SESSION_START.md. Read the handoff and queue, inspect actual GitHub evidence, implement and commit a substantial safe batch, update both documents, and only ask me to act if essential.**

## Mandatory startup sequence
1. Fetch this file, [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md), and [DEVELOPMENT_QUEUE.md](DEVELOPMENT_QUEUE.md) from current `main` via GitHub connector. These are authoritative *project notes*, not proof of successful builds.
2. Check workflow run jobs, logs and artifacts when run IDs are known. Never claim a run passed merely because a commit exists or a screenshot suggests success.
3. Choose the highest-priority unblocked queue item. Prefer multiple closely related source-only fixes and static verification per session, rather than one tiny commit.
4. Commit safe changes on `main`; preserve existing source, prefixes, games and saves. Update queue status and prepend a concise handoff entry with commit links, verified/unverified evidence, next task and whether owner action is needed.
5. Respond briefly. **Owner wants notifications only when personal action is required.** In active sessions, concise completion acknowledgment is sufficient.

## Safety / authorization boundaries
- **Do not** uninstall or clear stable Portal (`com.charoite`), experimental Next (`com.charoitx`), games, saves, user prefixes, rootfs, Wine28, or historical Wine29 v1–v28 scratch.
- Historical V28 is permanently consumed. No retry, cleanup, reads of oversized logs, Wine process execution or scratch reuse.
- Current work is source-only pinned Wine29 ARM64 PE cross-build, **not** Android runtime verification.
- No phone tests, APK installs, independent Wine/Wineboot/wineserver/SCM executions without explicit owner consent.
- Keep verified build status separate from build attempts, imports separate from full dependency closure, and source builds separate from Android gameplay.
- Overall v1.0 completion estimate approximately **30%**, not an audited metric; only revise with new evidence.
- GitHub Actions is configured to build when relevant workflow/source paths change. The separate hourly ChatGPT Build Watch monitors; it is **not** an autonomous coding agent.
- GitHub updates cannot create a ChatGPT Project or automatically migrate chat history; owner may organize chats in a ChatGPT Project manually.

## Working links
- [Canonical handoff](CURRENT_HANDOFF.md)
- [Priority queue](DEVELOPMENT_QUEUE.md)
- [Wine29 source-only workflow](https://github.com/rgarn023/CharoitePortal/actions/workflows/wine29-first-provider-crossbuild.yml)
- [Missing provider closure issue #7](https://github.com/rgarn023/CharoitePortal/issues/7)

## End-of-session handoff contract
Always leave a **fresh summary at the top** of CURRENT_HANDOFF.md with: UTC date, commits, exact test evidence/run IDs (or unverified), next queue item, blockers, owner action needed YES/NO, and safety boundaries. Older notes are archival; never treat them as the latest state.
