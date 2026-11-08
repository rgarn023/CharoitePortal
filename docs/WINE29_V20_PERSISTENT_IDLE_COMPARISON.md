[**CURRENT PROJECT HANDOFF — OPEN FIRST**](https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md)

# Wine29 V20 — one-shot persistent wineserver comparison

**SIGNED BUILD VERIFIED — OWNER PHONE EXECUTION PENDING.** Experimental `com.charoitx`, versionCode **143**, versionName **11.2-next.0.112**; [**successful GitHub Actions run 42536089299**](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299), exact APK source commit [`cfed669341a9045deeb332193f8293f2ff982f6a`](https://github.com/rgarn023/CharoitePortal/commit/cfed669341a9045deeb332193f8293f2ff982f6a), [**direct signed APK artifact 13638739137**](https://github.com/rgarn023/CharoitePortal/actions/runs/42536089299/artifacts/13638739137). Original persisted experimental signer matched; no Wine was executed on phone by CI. v0.112 supersedes verified v0.111.

V18's direct Wineboot -i exited 0. Wineboot and services.exe PE traces had no observed DLL failures. The native foreground wineserver exited 1 around 200 ms after initialization, but the cause is unknown. Wine's documented `-p` wineserver flag keeps a server persistent when clients exit. V18 used only `-f -d`. V19 completed V18's preserved read-only audit. **V20 changes only the private foreground server invocation to `-f -d -p`; it does not access V18.**

## Exact private phone-only scope

Only on explicit opt-in, create NEW `charoite-next-wine29-entry-v20` in experimental com.charoitx's no-backup private directory, fail closed if already present. Verify unchanged pinned 34 hybrid DLL, 111 PE/NLS, three native ELF and source-verified Wineboot/services/userenv/sc files; stage only V20-local copies. Create V20-local C: mapping, start one V20 foreground wineserver with `-f -d -p`; record socket/lock and bounded V20 server trace. Start exactly one source-verified Wineboot -i using existing V6 APK native loader and WINELOADERNOEXEC=1; Wine may launch internal services. Record bounded PE trace and process exits. On direct Wineboot success, observe server at nominal 0, 1, 3, 8, 12-second checkpoints and record **actual elapsed milliseconds**, not nominal survival time when wait returns early. After observation, terminate ONLY this V20 private server if still alive; retain all files/logs, no retries/cleanup.

**NO** independent Wineboot --help, sc.exe execution, SCM query, installers, games or network. NO Wine29 V1–V19, Wine28, stable Portal, user prefixes, saves or rootfs access. CI never executes phone Wine. Persistent survival would favor an idle-shutdown hypothesis but would not prove V18's cause; an early V20 exit would call for a separate preserved read-only audit, never a retry. Neither result proves independent Windows PE control/SCM/gaming.

## System owner action — signed v0.112 verified; phone test required

In **System → CURRENT WINE29 ACTION — V20 PERSISTENT SERVER IDLE**, read instructions directly beside **Test Wine29 v20 persistent idle (one-shot)** and **Open current project handoff**. Tap Test → separately **Authorize ONE fresh v20 test** or **Cancel — do not execute**. Install verified APK IN PLACE over com.charoitx, never uninstall/clear app storage. Tap **Copy short report** and paste full first-line Handoff through **END OF SHORT V20 PERSISTENCE REPORT** in a new chat.

**Charoite 1.0 readiness: ~30% complete / ~70% remaining, unchanged.**
