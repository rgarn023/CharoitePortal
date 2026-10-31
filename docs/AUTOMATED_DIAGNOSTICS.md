# Charoite Next — Opt-in automated phone diagnostics (first milestone)

Status: implemented in Next Android source v0.54; device behavior and signed APK are NOT yet verified until GitHub Actions and phone testing pass.

## Purpose
Eliminate manual copying of Wine28 v9 forensic results into ChatGPT. The new System tab button, "Automatic phone diagnostics (GitHub opt-in)", prepares a strictly allowlisted, read-only report and, after explicit enrollment, sends it automatically to PUBLIC GitHub Issues in rgarn023/CharoitePortal.

## One-time device enrollment
1. Install the verified Charoite Core Next v0.54 APK over com.charoitx when it is available. Do not uninstall or clear storage; leave com.charoite (stable Portal) alone.
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

## Remaining milestones for near hands-off 1.0 development
- Verify the signed APK and actual phone issue upload + GitHub Actions triage.
- Expand allowlisted reports to new approved isolated test generations (never rerun consumed scratch).
- Configure a persistent authorized AI development workflow that can review issues and propose code changes. Ordinary ChatGPT messages and CI do not provide a persistent AI developer.
- Add verified APK update notices and user-safe installation. Full unattended app installation is NOT promised on Android.
- Gate eventual 1.0 against a tested compatibility matrix including Wine prefix bootstrap, Windows app launch, x86/x64 translation, graphics, audio, input, game installs and safe persistence.
