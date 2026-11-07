# Wine29 v7 services.exe PID 0034 DLL failure — read-only follow-up

November 7, 2026. Next v0.87 source target, package com.charoitx.

## What the phone proved

In the prior v7 one-shot, Wineboot processes 0x0024 and 0x002c mapped NTDLL/kernel32/API-set and exited 0. The v0.86 preserved postmortem then determined that **PID 0x0034 mapped source-built ARM64 services.exe, ntdll.dll, kernel32.dll and API-set but exited 0xC0000135 (STATUS_DLL_NOT_FOUND)**. Two services.exe process-create requests were recorded and zero services builtin lookup failures. The exact missing DLL remains UNKNOWN. These results do not establish a functioning Service Control Manager, a complete prefix or running games.

## New v0.87 read-only diagnostic

The existing `CharoiteWine29V7ReadOnlyForensics.java` examines only the same two exact retained v7 logs (both 2 MiB cap, 60,000-line bound and 16,384-character per-line limit) and explicitly named v7 file metadata. Adds a PID 0x0034 focus: up to 10 module error/DLL-not-found/import failure EVENT TYPES and up to 12 most recent DLL import/load-order/load EVENT TYPES. Each event reports **at most six regex-sanitized DLL/EXE basenames**, not raw log lines or private paths. Merely appearing in the log does NOT prove that a DLL is missing. Server missing-name statuses are not evidence of a specific missing DLL.

No Wine, Wineboot, services.exe, wineserver, process, scratch creation, writes, registry contents, cleanup, retries, previous generations, stable Portal, user prefixes, games, saves or rootfs access. V7 execution remains archived and hidden. The only current System test is `Inspect Wine29 v7 DLL failure (read-only)`.

## Release gate and next step

Target 11.2-next.0.87/versionCode 118, with existing persisted Next signing key, same immutable 111 PE/NLS and 3 native v6 ELF sources and verified ARM64 v7 services PE. Source must pass GitHub Actions Android Gradle and all regressions before an APK can be considered verified. When a verified signed APK exists, install **in place** over Next without uninstalling or clearing data. Run the read-only action once, copy the output. Only an explicit correlated failure identifies the next missing module; do not rerun v7 or assert Windows runtime readiness.
