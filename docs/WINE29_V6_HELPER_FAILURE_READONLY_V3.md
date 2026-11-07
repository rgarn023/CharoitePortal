# Wine29 v6 — read-only causal trace v3 (PID 0034 / retained wineserver evidence)

**Date:** November 7, 2026. **Experimental package:** `com.charoitx`. **Proposed:** v0.84, code 115. **State:** source submitted; APK and signature require separate verified Actions result.

## On-phone evidence requiring this audit

The owner's signed v0.83 report confirmed both Wineboot PE processes (0x0024 and internal 0x002c) mapped matching NTDLL, kernel32 and API set and exited 0. Process 0x0034 separately exited `-1073741515` / `0xC0000135` (`STATUS_DLL_NOT_FOUND`); no executable or missing DLL could be identified by the previous PE parser. Existing 485,294-byte, 3,113-line v6 PE log was safely read twice; the existing **410,477-byte wineserver log was NOT READ** because v0.83 had an explicit 256-KiB whole-file cap. This result does **not** prove a complete Wine prefix or functioning Windows apps.

## Scope of v3 — no execution, no state changes

Only the same two fixed, already-preserved logs inside `com.charoitx/no_backup/charoite-next-wine29-child-loader-v6` are read. PE log keeps original 2-MiB max and 16,384-character line limit. The server evidence limit explicitly increases from **256 KiB to 512 KiB**, enough to examine the known 410,477-byte source without truncation, while still rejecting unexpected larger files. Lines over 16,384 characters are skipped rather than copied into the report. No other generations or files are opened, no shell/PE/native processes launched, no filesystem writes, no retry or cleanup.

The report adds bounded/redacted *chronological clues* for process-creation requests, PID 0034 PE lines, status-text hits, and up to 16 relevant server-log lines. A mention of `0034` or temporal proximity **does not prove** the executable, parent PID, loader dependency, or causal association. If identification is impossible, it remains explicitly unknown. The full server log is **not** copied to clipboard or included in the report.

The old one-shot v6 execution button stays hidden. The only current System test is `Inspect Wine29 v6 helper causal trace (read-only)`. Do not uninstall, clear storage, rerun v6, or touch stable Portal, older Wine29 generations, games, rootfs, prefixes or saves. For future runtime execution require new authorization and an independent v7 scratch.

## Validation required

Next CI must verify 138 stable tests + all Next regression tests, versionName `11.2-next.0.84`, versionCode `115`, original v6 ELF and sealed PE/NLS hashes, unchanged `com.charoitx` signing certificate, and a completed signed Actions APK artifact. The phone read-only v3 report—not CI—is required before diagnosing `0034`. A successful APK build must not be interpreted as a successful Wine bootstrap.
