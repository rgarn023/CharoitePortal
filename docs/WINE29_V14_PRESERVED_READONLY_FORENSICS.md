# Wine29 V14 — preserved sc.exe exit-127 read-only postmortem

## Evidence received from owner (November 8, 2026)

The owner ran the signed Next v0.101 V14 one-shot on the Galaxy S26 Ultra, separately authorized in System, and supplied the complete short report ending `END OF SHORT V14 ENTRY REPORT`. This report is *device evidence*, not CI execution.

- Native/PE/NLS source and hash gates PASS: 34 hybrid DLLs, 111 PE/NLS, three APK ELFs, source-pinned ARM64 sc.exe and prerequisite services.exe/userenv.dll.
- One independent NEW V14 `charoite-next-wine29-entry-v14` scratch/prefix was used. Preseeded drive_c and C: relative symlink were correctly retained. Windows-created windows/system32 and users/xuser/AppData directories appeared; Program Files did not.
- Wineboot `-i` exited **0** within 45 seconds. The foreground wineserver remained alive immediately before and immediately after the subsequent sc.exe test. The three registry files appeared after shutdown with metadata sizes **1,981 / 1,858 / 123 bytes**; registry contents/completeness were not audited.
- A source-hash verified copy of sc.exe was placed **only in the new V14 private** `drive_c/windows/system32/sc.exe`. The native loader was invoked once with the **Windows** argument `C:\\windows\\system32\\sc.exe`; `WINELOADERNOEXEC` was **UNSET** for sc.exe (while retained for Wineboot).
- The separate sc.exe attempt completed in 12 seconds but returned **127** and wrote **0 stdout/stderr bytes**. No usage marker was found. PE mapping was **not confirmed**. No SCM query/service operation or game was attempted.
- Changing the previous Unix sc.exe argument to a Windows C: argument **did not resolve the exit-127 symptom**. This is not proof of the exit-127 cause, PE loader failure, missing DLL, or working SCM.

All V14 logs/scratch must now remain **permanently consumed**. Never rerun or delete V14. Never uninstall/clear experimental app storage; V1–V13, Wine28, stable Portal, user game saves/prefixes and rootfs must not be accessed.

## Next v0.102 audit: no execution, bounded evidence only

The sole current System Wine29 control is **Inspect Wine29 v14 sc.exe exit (read-only)**. The earlier V14 one-shot action remains in source for auditability but is permanently hidden by a false gate.

The inspector opens **only three fixed named V14 files** within the V14 private no-backup scratch, using the same bounded techniques as the completed V13 inspector:

1. `v14-wine-direct-init.log`: bounded log counters for Wineboot/services/helper events, mapped PE module names and per-PID exit codes. This Wineboot trace predates the separately launched sc.exe process, so an absence of sc.exe mappings in this log is **not evidence the later sc.exe failed to map**.
2. `v14-sc-entry.log`: bounded read-only examination of the *separate* sc.exe redirect output. An empty file gives no PE mapping evidence and must never be interpreted as a diagnosis.
3. `v14-foreground-wineserver.log`: bounded counts for server/process activity and sc.exe mentions. Server activity is not evidence of SCM readiness.

The inspector also checks only explicitly named V14 path metadata (not file contents), including the private Windows C: `sc.exe` copy, the original PE copies, folders and the sizes of system/user/userdef registry files. The C: link is inspected with `lstat/readlink` and **never traversed as a link**. Raw trace lines, private filesystem paths and registry contents are never copied into the report.

Limits: **8 MiB per log**, **100,000 lines**, **16,384 chars/line**, **9,000 chars total short report**. It performs **no process creation, Wine, Wineboot, sc.exe, services.exe or wineserver execution; no new scratch; no retries, cleanup, writes, or reads of older generations/Portal/games/rootfs**.

The report ends `END OF SHORT V14 READ-ONLY REPORT — raw traces remain on phone, unchanged.`.

## What would actually move us toward 1.0?

The existing exit-127/zero-output result suggests the **next functional experiment must target the native launcher and distinguish Android ProcessBuilder/ELF entry errors from Wine/PE errors**, rather than randomly adding Windows DLLs or retrying consumed generations. First, inspect preserved V14 evidence without modifying it. Any subsequent execution needs a separately authorized **NEW V15 isolated scratch** with a single testable hypothesis, independent logs for the sc.exe launcher and (if safely supported) native launch diagnostics; no game/SCM assumptions until PE entry is confirmed.

## Build integrity

This section is a **source candidate** until GitHub Actions verifies it and produces a signed APK. CI only compiles and runs regression/static safety checks; CI does not execute phone Wine, PE programs or games. Experimental package remains `com.charoitx` (distinct from stable `com.charoite`). Candidate APK identity: versionCode **133**, versionName **11.2-next.0.102**. Install in place using the original signing certificate; **never uninstall or clear storage**.
