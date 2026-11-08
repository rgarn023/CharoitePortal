# Wine29 V12 — preserved sc.exe exit-127 postmortem and V13 gate

## Owner's verified-by-report V12 observations (November 8, 2026)
The owner supplied the complete bounded phone report ending `END OF SHORT V12 ENTRY REPORT` from signed experimental Next v0.97 (package `com.charoitx`, versionCode 128). These are **owner-supplied device observations**, not direct access to raw private phone logs.

- Immutable source/asset preflight: 34 Wine29 hybrid DLLs, 111 staged PE/NLS entries, three native ELF, source-pinned services.exe, userenv.dll and ARM64 sc.exe **PASS** in entirely **new V12 private scratch**.
- Foreground wineserver socket/lock observed and alive following source-matched Wineboot `-i`. Wineboot process exited **0** with no 45-second deadline/log-overflow; Windows-created `windows/system32` and `users/xuser/AppData` were observed. C: drive folder and relative `dosdevices/c:` symlink were intentionally preseeded; not proof of Wine creating them. `Program Files` absent.
- Exactly one no-argument ARM64 `sc.exe` attempt: foreground server alive immediately **before and after**. `sc.exe` subprocess completed within 12 seconds, exit **127**, log **0 bytes**, no usage text, no log overflow. **PE mapping is not verified.** No SCM query or service operation ran. Absence of native execv errno/DLL missing markers in the short Wineboot report does not prove successful sc.exe execution.
- Three registry files present only **after server shutdown**: system.reg **1,981 B**; user.reg **1,858 B**; userdef.reg **123 B**, metadata-only. Their contents/integrity are untested. Pre-shutdown absence does not contradict their later presence.
- Wine28, Wine29 V1–V11, stable Portal, games, saves, user prefixes and rootfs not accessed per device report. **V12 already executed once; never repeat or clean it.**

## Read-only V12 postmortem in future signed v0.98
An archived V12 one-shot control must **not** be surfaced again. The only active Wine29 System control will be **Inspect Wine29 v12 sc.exe exit (read-only)**. The new `CharoiteWine29V12ReadOnlyForensics`:
- Inspects exactly THREE fixed local V12 logs: `v12-wine-direct-init.log`, `v12-sc-entry.log`, `v12-foreground-wineserver.log`; reads only named V12 metadata (scratch/local Windows directories, C: relative link via lstat/readlink, source-pinned PE file presence, post-shutdown registry file *lengths*).
- Bounds each log to 8 MiB, 100,000 lines, 16,384 characters/line, and 9,000 characters of sanitized user-facing output; reports PID/module **basenames** and counts of PE mappings, Wineboot/services/sc.exe requests, module errors, PE exits, wineserver lifecycle, and no-argument sc.exe log state. Empty `sc.exe` log cannot prove absence of a PE mapping.
- Never reads registry contents, enumerates arbitrary directories, follows C: symlink into external paths, starts Wine/Windows programs/processes, creates scratch, retries, writes, deletes, cleans, or accesses another Wine generation.
- Returns a report ending **`END OF SHORT V12 READ-ONLY REPORT`**. Raw logs remain on phone untouched. Do not execute a V13 process until this evidence is reviewed and a distinct one-shot fresh-prefix authorization is obtained.

## Status and preservation
v0.98 is initially a **source-only APK candidate**: package `com.charoitx`, versionCode 129, versionName `11.2-next.0.98`. Signing/build/CI must be verified first. Latest verified signed APK remains Next **v0.97**, Actions 42451472112, but its V12 execution is permanently consumed and must not run again. Install any later signed Next APK **in place** only, never uninstall, clear data or touch stable `com.charoite`. No SCM readiness or Windows-gaming capability is demonstrated by V12.
