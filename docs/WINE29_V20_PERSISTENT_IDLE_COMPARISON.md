[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V20 — one-shot persistent wineserver comparison

**SIGNED BUILD VERIFIED — OWNER PHONE V20 EXECUTION COMPLETE.** Experimental `com.charoitx`, versionCode **143**, versionName **11.2-next.0.112**; [**successful GitHub Actions run 42536089299**](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299), exact APK source commit [`cfed669341a9045deeb332193f8293f2ff982f6a`](https://github.com/rgarn023/CharoitePortal/commit/cfed669341a9045deeb332193f8293f2ff982f6a), [**direct signed APK artifact 13638739137**](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299/artifacts/13638739137). Original persisted experimental signer matched; no Wine was executed on phone by CI. v0.112 supersedes verified v0.111.

**Owner phone result (November 8, 2026):** V20 direct `wineboot.exe -i` exited **0**, private persistent `wineserver -f -d -p` survived all five checkpoints (actual elapsed **0, 1000, 3001, 8001, 12001 ms**); no native child-exec errno marker or `c0000135` observed. The private server was stopped only at probe finalization, and V20 scratch/logs are retained permanently. No independent help, sc.exe, SCM or games. Immediately after Wineboot `system.reg`, `user.reg`, `userdef.reg` were reported absent, while *post-finalization* metadata showed **1,981 / 1,858 / 123 bytes**; likely timing-related but persistence cause and registry completeness remain unproven. **NEVER retry V20.** New separately consented V21 independent-help scope is [here](WINE29_V21_INDEPENDENT_HELP_PERSISTENT_SERVER.md).

V18's direct Wineboot -i exited 0. Wineboot and services.exe PE traces had no observed DLL failures. The native foreground wineserver exited 1 around 200 ms after initialization, but the cause is unknown. Wine's documented `-p` wineserver flag keeps a server persistent when clients exit. V18 used only `-f -d`. V19 completed V18's preserved read-only audit. **V20 changes only the private foreground server invocation to `-f -d -p`; it does not access V18.**

## Exact private phone-only scope

Only on explicit opt-in, create NEW `charoite-next-wine29-entry-v20` in experimental com.charoitx's no-backup private directory, fail closed if already present. Verify unchanged pinned 34 hybrid DLL, 111 PE/NLS, three native ELF and source-verified Wineboot/services/userenv/sc files; stage only V20-local copies. Create V20-local C: mapping, start one V20 foreground wineserver with `-f -d -p`; record socket/lock and bounded V20 server trace. Start exactly one source-verified Wineboot -i using existing V6 APK native loader and WINELOADERNOEXEC=1; Wine may launch internal services. Record bounded PE trace and process exits. On direct Wineboot success, observe server at nominal 0, 1, 3, 8, 12-second checkpoints and record **actual elapsed milliseconds**, not nominal survival time when wait returns early. After observation, terminate ONLY this V20 private server if still alive; retain all files/logs, no retries/cleanup.

**NO** independent Wineboot --help, sc.exe execution, SCM query, installers, games or network. NO Wine29 V1–V19, Wine28, stable Portal, user prefixes, saves or rootfs access. CI never executes phone Wine. Persistent survival would favor an idle-shutdown hypothesis but would not prove V18's cause; an early V20 exit would call for a separate preserved read-only audit, never a retry. Neither result proves independent Windows PE control/SCM/gaming.

## Historical System owner action — V20 already consumed, archived

Historical v0.112 only, no longer active: the original **System → V20 PERSISTENT SERVER IDLE** grouped instructions directly beside **Test Wine29 v20 persistent idle (one-shot)** and **Open current project handoff**. Tap Test → separately **Authorize ONE fresh v20 test** or **Cancel — do not execute**. Install verified APK IN PLACE over com.charoitx, never uninstall/clear app storage. Tap **Copy short report** and paste full first-line Handoff through **END OF SHORT V20 PERSISTENCE REPORT** in a new chat.

**Charoite 1.0 readiness: ~30% complete / ~70% remaining, unchanged.**

**This is an immutable historical test specification, not a request to execute V20 again. V21 is the only new source candidate.**
