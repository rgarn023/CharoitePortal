# Charoite continuous development

Target: main. Coordination PR uses automation/charoite-continuous-development.

Only a completion signal for .github/workflows/wine29-first-provider-crossbuild.yml is engineering work. Validate the run through GitHub, including repository, main branch, completed status, SHA, attempt, actual jobs, steps and logs. Workflow success is not diagnostic success. This workflow produces PE candidates, NOT an APK.

Safety: $0 additional; standard public GitHub-hosted Ubuntu only, no paid API, runners or services. Never access or modify existing Wine generations, prefixes, games, saves, environments, rootfs, com.charoite or com.charoitx data. CI-only scratch. Owner consent required for phone testing or data-affecting changes.

One bounded development cycle per completed run ID. Reruns of an already processed ID are review-only unless explicitly authorized. Never react to unrelated comments, own commits, lock writes or status reports. Never post @codex to trigger work. Never use PR commit updates as wake-ups. Each cycle may implement one evidence-supported milestone, validate it, update CURRENT_HANDOFF.md and record the run ID. Stop when blocked or functional evidence is insufficient. No automatic retry or no-change rebuild loop.

Both hourly and event workers must use the same GitHub content-SHA compare-and-swap lock at .github/automation/development-state.json on automation/charoite-continuous-development. Read it fresh; if owner is non-null, exit without edits. Acquire by update_file with the observed blob SHA and a unique owner token. A conflict means exit. Do not steal a lock automatically, even if old; report stuck ownership. Re-read ownership before every engineering mutation. Hold through commits, handoff and processed-run recording; release with another fresh-SHA update. Preserve processed IDs. No process-local-only locking.

The hourly task remains enabled, using this lock and ledger. It may recover missed completion events but must not duplicate claimed or processed run IDs. Do not modify code while relevant verification is in flight. Commits use a development branch/PR; update main only after appropriate validation. Completion signals do not authorize merging unverified changes.

Initial functional estimate: 31%. Increase only with meaningful verified functional milestones; static inventories alone do not qualify.

Push delivery depends on ChatGPT notification settings and OS permission. No emails are sent by this automation.
