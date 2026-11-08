[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V18 — isolated foreground wineserver idle-lifecycle baseline

**Status: source candidate; not an installable/signed release until exact successful GitHub Actions and APK signing are verified.** No Wine, Windows PE, SCM or games run in CI. This is an OWNER-authorized phone execution experiment only.

## Reason for V18

The completed V17 preserved read-only evidence shows that direct Wineboot `-i` exited 0, Wineboot and services.exe mapped with zero observed PE/module errors and the independent Wineboot `--help` native process exited 127 with no output around 202 ms. The private foreground wineserver was alive immediately before the independent control but was absent after it. This does not identify the control failure's cause, whether the independent PE mapped, or whether server shutdown caused or followed the failure. V17 never attempted independent sc.exe, never queried SCM, and remains permanently consumed. A control/SCM retry on V17 is prohibited.

V18 changes **only the new scratch generation and the post-Wineboot observation phase**. It reuses the original source-verified Wine29 V6 native loader/NTDLL/server, sealed hybrid PE+NLS cohort, source-verified services, userenv and sc assets. The sc executable may be verified/staged as DATA alongside the other pinned files but is NEVER launched.

## V18 exact one-shot phone scope

1. New scratch `charoite-next-wine29-entry-v18` under experimental `com.charoitx` private no-backup data, created only on explicit on-device authorization; fail closed if it already exists. No retries, cleanup, deletion, resetting or repurposing V18.
2. Repeat original Wine29 34-DLL header/import preflight; verify sealed 111 staged PE/NLS entries, three APK-native ELF hashes and pinned source-built Wineboot, services.exe, userenv.dll and sc.exe source hashes. Create only private V18 prefix, C: mapping and scratch-local verified module copies.
3. Start one V18-private foreground wineserver with its own isolated environment and capture bounded `v18-foreground-wineserver.log`. When socket/lock handshake succeeds, invoke exactly one private Wineboot.exe `-i` with the V6 APK-native loader and `WINELOADERNOEXEC=1`, capturing `v18-wine-direct-init.log`. Wine may create internal Wineboot/services child processes during initialization.
4. If Wineboot exits within the 45-second and 2 MiB caps, record process exit, private server state, preseeded C: versus Windows-created folders, and registry file presence only (never parse contents). Then **do not invoke another native loader or Windows executable**. Observe server process liveness at 0, 1, 3, 8 and 12 seconds post-init; break early if it exits. Report each checkpoint actually observed, elapsed time, any observed server exit value and whether it was alive immediately before probe finalization.
5. Terminate only the V18 private server process if still running at controlled finalization; preserve all V18 files/logs. This termination must be distinguished from a server exit observed BEFORE finalization. No independent Wineboot `--help`, no sc.exe, no SCM query, no installers/games, no network, no past scratch access.

A server exit during idle observation can reflect wineserver's own lifecycle or an earlier client/internal change. Survival alone does not prove second-process execution, PE entry or SCM. No causal conclusions should be drawn.

## System and report

**System → CURRENT WINE29 ACTION — V18 SERVER IDLE LIFECYCLE** must show the scope and actions together:
**Test Wine29 v18 server lifecycle (one-shot)** and **Open current project handoff**.
The test tap opens a separate warning/confirmation, **Authorize ONE fresh v18 test** or **Cancel — do not execute**. No startup/background execution. After one-shot, tap **Copy short report**, paste from the first-line Handoff URL through **END OF SHORT V18 IDLE REPORT** into a new chat. V17 and previous test/inspection System actions are archived. Never uninstall or clear experimental app storage; stable Portal stays untouched.

Candidate `com.charoitx`, **versionCode 141, versionName 11.2-next.0.110**. CI must pass new V18 source isolation, UI consent, version/package, regression, Android Gradle build and original signer-continuity checks before owner installation. Existing latest verified signed v0.109 remains downloadable until V18 is separately confirmed.

**Charoite 1.0 readiness ~30% complete / ~70% remaining unchanged.** Idle server observations alone do not unlock independent PE entry, SCM or gameplay milestones.
