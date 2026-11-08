# Wine29 V9 SCM exit-127 evidence and proposed V10 diagnostics

Date: November 7, 2026. Status: **source-side design only; no V10 on-device execution authorized, implemented, or claimed**.

## Preserved V9 owner evidence

The owner completed the single V9 execution attempt and then ran the signed Next v0.92 **strictly read-only** postmortem. Preserve `com.charoitx/no_backup/charoite-next-wine29-scm-v9` exactly. Do not rerun V9, delete logs, clean scratch, or open older v1–v8/Wine28/private user or game prefixes. Do not affect the stable `com.charoite` package.

- Preflight passed for 34 DLLs, 111 PE/NLS items and APK-native Wine loader/NTDLL/wineserver, plus source-built `services.exe`, `userenv.dll`, `sc.exe`.
- Direct ARM64 Wineboot `-i` returned 0; private Wine-created `windows`, `system32`, `users`, `users/xuser/AppData` observed. `drive_c` and `dosdevices/c:` were **preseeded**, not Wine-created evidence.
- After shutdown, `system.reg`, `user.reg`, `userdef.reg` exist with metadata sizes 1,981 / 1,858 / 123 bytes; contents **not read**, format/integrity/completeness unverified.
- Retained PE trace: 600,696 bytes / 3,936 lines. Wineboot PIDs `0x0024`, `0x002c`; services PID `0x0034`, `userenv.dll` mapped in that PID; no captured DLL_NOT_FOUND/module failure; six observed exit events, all zero. Services PE exit 0 is **not** an SCM health or persistence indicator.
- Retained foreground server trace: 486,481 bytes / 5,145 lines; 2 process requests/replies; no captured registry error or missing DLL marker.
- V9 owner one-shot report: `sc.exe query` was attempted; native subprocess returned **127**. The retained `v9-sc-query.log` is **0 bytes**. No confirmed `sc.exe` PE mapping, service query result, SCM status, or RPC response appears in the preserved evidence.

## Classification and limitation

The archived V9 `CharoiteWine29V9ScmProbe.java` constructs `ProcessBuilder(nativeLoader, verifiedScPe, "query")`, redirects combined stdout/stderr to `v9-sc-query.log`, and reports the subprocess exit code. Its successful `start()` plus observed exit indicates an Android-native subprocess was started. **It does not prove the Windows `sc.exe` PE initialized or reached the SCM**. A numerical exit 127 is not by itself a Wine error name, Win32 error, SCM failure response, missing program or missing DLL diagnosis. There is no shell in that ProcessBuilder invocation, so interpreting 127 as a shell's “command not found” is unjustified.

The strong next hypothesis is **a launcher / PE-entry boundary problem**, because the log is empty and no `sc.exe` PE mapping was captured. This is a hypothesis, not a confirmed root cause. No evidence currently proves SCM readiness or explains the missing `sc.exe` evidence. Do not treat “no DLL_NOT_FOUND” as “all Windows programs run.”

The archived V9 report's inherited V6-style generic `RESULT: FAIL` text does not classify V9. `Program Files` being absent is not conclusive for this bootstrap stage.

## Proposed V10 source preparation, not a V9 retry

1. **No device execution during source preparation.** Reinspect the existing V9 Java launch path, pinned source-built `sc.exe` / dependency manifests and Wine29 loader's exit/diagnostic behavior in code or CI only. Preserve immutable source-build hashes.
2. **New V10 scratch and explicit consent required for any eventual execution** (e.g. `charoite-next-wine29-scm-start-v10`). A single V10 launch may be implemented behind a distinct System action that clearly states that native Wine, Wineboot, internal Windows helpers and `sc.exe` may execute only against that newly created private prefix. Never start automatically on app boot, install or update. Refuse if the V10 scratch already exists.
3. **Capture launch-stage classifications without secrets or raw log excerpts:** Java `start()` success/failure class, child process exit/timeout, actual output-file byte count, foreground server liveness at start/end, and bounded `sc.exe` PE mapping/process creation/exit evidence. Keep bounded separate native-loader/PE telemetry; sanitize private paths, tokens, command arguments and environment values. Preserve raw logs locally in new V10 scratch only.
4. **Fail closed on observed V10 outcomes:** no PE mapping = “native/PE launch not demonstrated”; PE mapping with nonzero exit = “Windows program attempted, failed”; SCM/RPC failure = “client executed, service manager unavailable”; recognizable SCM service listing/query response = “basic SCM response observed.” Wineboot exit 0, registry file presence, successful Android ProcessBuilder start, or a numeric 127 alone do not satisfy the latter gate.
5. **Static tests and CI before APK:** ensure original 111 + three ELF + v7/v8/v9 assets byte-identical, source hashes and PE import closure still PASS; confirm V9/older scratch paths cannot be read, written, retried, or cleaned by V10; ensure archive of V9 execution control and absence of background launch. No game/Windows 11/graphics/Steam/Battle.net readiness claim.

Only after a verified signed V10 APK and *separate user opt-in* should a new V10 on-phone one-shot occur. No V10 code or APK has been produced by this design note. Latest verified install remains signed experimental Next **v0.92** from [Actions run 42441906008](https://github.com/rgarn023/CharoitePortal/actions/runs/42441906008), [APK artifact 13602310423](https://github.com/rgarn023/CharoitePortal/actions/runs/42441906008/artifacts/13602310423); install only in place, never uninstall or clear app data.
