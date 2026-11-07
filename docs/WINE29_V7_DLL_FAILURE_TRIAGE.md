# Wine29 v7 services.exe PID 0034 DLL failure — read-only follow-up

November 7, 2026. Next v0.87 source target, package com.charoitx.

## What the phone proved

In the prior v7 one-shot, Wineboot processes 0x0024 and 0x002c mapped NTDLL/kernel32/API-set and exited 0. The v0.86 preserved postmortem then determined that **PID 0x0034 mapped source-built ARM64 services.exe, ntdll.dll, kernel32.dll and API-set but exited 0xC0000135 (STATUS_DLL_NOT_FOUND)**. Two services.exe process-create requests were recorded and zero services builtin lookup failures. The exact missing DLL remains UNKNOWN. These results do not establish a functioning Service Control Manager, a complete prefix or running games.

## New v0.87 read-only diagnostic

The existing `CharoiteWine29V7ReadOnlyForensics.java` examines only the same two exact retained v7 logs (both 2 MiB cap, 60,000-line bound and 16,384-character per-line limit) and explicitly named v7 file metadata. Adds a PID 0x0034 focus: up to 10 module error/DLL-not-found/import failure EVENT TYPES and up to 12 most recent DLL import/load-order/load EVENT TYPES. Each event reports **at most six regex-sanitized DLL/EXE basenames**, not raw log lines or private paths. Merely appearing in the log does NOT prove that a DLL is missing. Server missing-name statuses are not evidence of a specific missing DLL.

No Wine, Wineboot, services.exe, wineserver, process, scratch creation, writes, registry contents, cleanup, retries, previous generations, stable Portal, user prefixes, games, saves or rootfs access. V7 execution remains archived and hidden. The only current System test is `Inspect Wine29 v7 DLL failure (read-only)`.

## Release gate and next step

**Verified signed v0.87:** [GitHub Actions 42413522887](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887) SUCCESS at commit `1cc689386f0dacd61e303e18627bcf6b9cc68791`; 138 stable and 190 Next tests PASS, Android Gradle SUCCESS, new bounded read-only PID 0034 gate PASS, v7 services.exe source hash/PE and prior v6 native/111 PE+NLS cohort checks PASS. AAPT `com.charoitx` versionCode 118/versionName 11.2-next.0.87; persisted Next signature certificate matches. [Download signed APK artifact 13590806127](https://github.com/rgarn023/CharoitePortal/actions/runs/42413522887/artifacts/13590806127) (ZIP SHA-256 `52b8bbddfaaf7aa3b4be67e948dabe05d91e359de691f3a22afde923fd2344c2`). When a verified signed APK exists, install **in place** over Next without uninstalling or clearing data. Run the read-only action once, copy the output. Only an explicit correlated failure identifies the next missing module; do not rerun v7 or assert Windows runtime readiness.

## Owner's v0.87 read-only findings (updated November 7)

The owner ran the requested diagnostic. Preserved PID 0x0034 reports `DLL_NOT_FOUND` with `userenv.dll` at line 1440 and a correlated module error naming `userenv.dll`/`services.exe` at 1441, plus a later `services.exe` module error at 1526. PID 0034 exits `0xC0000135`. Source-built `services.exe` mapped successfully; both Wineboot processes exited 0. The source-only V8 CI preflight [42418556136](https://github.com/rgarn023/CharoitePortal/actions/runs/42418556136) confirms the original source-verified sealed 34 providers omit `userenv.dll` while `services.exe` imports it. The previous request to rerun the v0.87 audit is completed and must not be repeated. Next work is an independent matching `userenv.dll` source candidate and its import graph; no v7 replay, new phone prefix or APK is authorized by the audit result.
