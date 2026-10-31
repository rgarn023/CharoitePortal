# Charoite Next — Opt-in automated phone diagnostics (first milestone)

Status: signed Next Android APK **v0.56 VERIFIED** (Actions 41162857377, 237 tests PASS, com.charoitx versionCode 87, signing unchanged). **Phone upload end-to-end VERIFIED:** sanitized [Issue #1](https://github.com/rgarn023/CharoitePortal/issues/1) was uploaded from the Galaxy; [Actions intake 41163400308](https://github.com/rgarn023/CharoitePortal/actions/runs/41163400308) validated/classified Wineboot child startup failure and posted a bot comment. v0.56 resolved AndroidKeyStore IV initialization and dialog contrast. Modern Wine28 remains unbootable. **Current decision: no separately billed OpenAI API usage.** Continue through chat-led GitHub development, free-of-OpenAI-API issue classification and normal CI. The former scheduled Codex workflow is now manual-only, doubly opt-in and not required.

## Purpose
Eliminate manual copying of Wine28 v9 forensic results into ChatGPT. The new System tab button, "Automatic phone diagnostics (GitHub opt-in)", prepares a strictly allowlisted, read-only report and, after explicit enrollment, sends it automatically to PUBLIC GitHub Issues in rgarn023/CharoitePortal.

## Troubleshooting the Enable button

- If v0.55 showed **Could not enable: InvalidAlgorithmParameterException**, this was a Charoite Android Keystore implementation bug, **not a bad token**. Update in place to **v0.56**; the app now lets Android Keystore generate its own GCM IV and displays the dialog on a readable dark background. **Do NOT regenerate the same token again** solely for this error, and never share its value in chat.
- In Next v0.54, **Could not enable: IllegalArgumentException** is the app's own over-restrictive token-format rejection; it happens BEFORE any upload. No need to uninstall/clear data or paste a credential into chat.
- Next **v0.55** makes this actionable: empty field, URL, classic `ghp_` token, non-fine-grained value and incomplete token show distinct safe messages. It accepts a complete `github_pat_` fine-grained token with an ordinary password-manager `Bearer ` or quote wrapper. GitHub API, not the app's local pattern, verifies the value and permission.
- Paste **the actual generated token value** (starts `github_pat_`) into the phone, NOT the token NAME, creation link, or Settings page. GitHub only shows the value when it is generated. If the value was not saved, regenerate a token and revoke the old one rather than trying to recover it.
- For GitHub HTTP 401, confirm token validity/expiration; 403 typically indicates inadequate repository access, permission or policy. The reporter stores these response status codes only, not credentials or response bodies. Check the reporter's "Last result" when reopening it.
- Never share any real token or a screenshot showing its value in chat, public GitHub issues, or logs.

## One-time device enrollment
1. Install the verified Charoite Core Next v0.56 APK over com.charoitx (GitHub Actions artifact https://github.com/rgarn023/CharoitePortal/actions/runs/41162857377/artifacts/13027808207). Do not uninstall or clear storage; leave com.charoite (stable Portal) alone.
2. Visit https://github.com/settings/personal-access-tokens/new while signed into the GitHub account authorized to create issues in rgarn023/CharoitePortal. Create a fine-grained token restricted to this one repository with the ONLY added repository permission "Issues: Read and write". Use a reasonable expiration. Do NOT give the token Contents, Actions, Administration or Workflows permission.
3. On the phone, in Charoite Next > System > "Automatic phone diagnostics (GitHub opt-in)", select Preview to inspect the precise data (JSON) that would become public.
4. Enter the fine-grained token DIRECTLY ON THE PHONE. Never paste it into ChatGPT, a GitHub issue, an APK or a commit. Tap Enable.
5. The app sends one sanitized issue immediately; Android JobScheduler also checks periodically when network access and power policy permit. It will not repost identical acknowledged report IDs.

## Technical guarantees and limits
- Public repository and public diagnostic issues stay PUBLIC. Phone uploads are explicit opt-in, OFF by default.
- The Android app sends only bounded counts/booleans from TWO read-only existing Wine28 v9 logs under the isolated com.charoitx no-backup private scratch. It does NOT transmit raw logs, filesystem paths, registry, game saves, unique device IDs, usernames, environment variables or Wine prefixes.
- It does NOT execute Wine/Wineboot/wineserver, create new scratch, retry one-shot v9, delete data, root the device, or modify stable Portal.
- The GitHub fine-grained token is entered only by the user and encrypted at rest with Android Keystore AES/GCM; no token or API secret is built into the APK or stored in source. The API destination is hardcoded to GitHub's HTTPS Issues endpoint for THIS repository, without redirect following.
- GitHub Actions on an issue opened by rgarn023 validates a strictly allowed report schema, checks its SHA-256 report ID and adds a deterministic issue comment classifying the failure. It is NOT autonomous AI programming.
- JobScheduler cannot guarantee exact background delivery times under Android Doze, battery settings or connectivity failures. An immediate upload attempt occurs on enrollment.
- If network response is lost after GitHub accepted a post, there is a small risk of a duplicate issue; normal acknowledged reports are deduplicated by hash.
- The first implementation reports ONLY preserved v9 bootstrap evidence. Future new safe diagnostic generations must be added explicitly without rereading v1-v8 scratch.

## Disable or revoke
Open the same System reporter settings, choose Disable / Close to remove the stored encrypted token and cancel scheduled reporting. To invalidate the credential globally, revoke the token in GitHub Settings > Developer settings > Personal access tokens. If app data is cleared or the keystore key is lost, re-enroll with a new token (never clear data solely to configure reporting).

## Remaining milestones — no paid AI API route
- **DONE / VERIFIED:** signed v0.56 APK, real phone upload (Issue #1), GitHub Actions validated intake (run 41163400308).
- **CURRENT DEVELOPMENT MODE:** continue Wine28 loader investigation and code fixes during active ChatGPT conversations through connected GitHub; run CI and publish signed GitHub Actions APK artifacts. No paid API secret or repo variable needed. Existing phone diagnostics/triage keep working.
- **COST CONTROL:** the experimental Codex workflow has NO recurring schedule. Manual paid operation requires three explicit owner choices (secret, enabling variable and dispatch consent); leave all unset. See [.github/automation/README.md](https://github.com/rgarn023/CharoitePortal/blob/main/.github/automation/README.md).
- Expand allowlisted reports to new explicitly approved isolated test generations; never rerun consumed v1–v9 scratch.
- Add verified APK update notices and user-safe installation. Full unattended app installation is NOT promised on Android.
- Gate eventual 1.0 against a tested compatibility matrix including Wine prefix bootstrap, Windows app launch, x86/x64 translation, graphics, audio, input, game installs and safe persistence.
