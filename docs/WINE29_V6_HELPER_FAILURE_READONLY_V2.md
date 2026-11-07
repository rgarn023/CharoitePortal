# Wine29 v6 — read-only postmortem v2 (helper exit and server line safety)

**Date:** November 7, 2026. **Package:** `com.charoitx`. **Proposed APK:** v0.83 / code 114. **Strict scope:** preexisting `charoite-next-wine29-child-loader-v6` scratch ONLY, NEVER re-run Wine29 v6.

## Confirmed results from signed v0.82 on-phone read-only report

1. Both Wineboot processes were observed independently: Wineboot parent `0024` and internal auto-`--init` child `002c` each mapped Wineboot/NTDLL/kernel32/API-set successfully and each ended with `exit_code 0`. These are real wins over v5's `run_wineboot failed to start wineboot 1`.
2. Separate process `0034` produced the first nonzero exit in the bounded log, `exit_code -1073741515`, exactly NTSTATUS `0xC0000135` (`STATUS_DLL_NOT_FOUND`). It is NOT yet known whether the failing executable is `services.exe`, `rundll32.exe`, or another Windows initialization helper; no specific missing DLL has been proven. Don't guess its identity or interpret Wineboot success as full prefix initialization.
3. Existing preseeded relative C: mapping remains correct, Wine-created Windows/users directory entries and three registry files exist. `Program Files` directory remains absent. Wine/PE/Graphics/games/Battle.net/Steam NOT tested as a functioning engine.
4. The v0.82 read-only audit ended `RESULT: BLOCKED — SecurityException` **AFTER** its PE-log analysis. Its next operation was `auditServer`, which enforces a 256 KiB total wineserver-log bound and additionally threw on any individual log line longer than 16 KiB. **Likely** explanation: an exceptionally long server protocol line. This is not proven without the exception message. No old evidence was modified by the failed read-only audit.

## Source fix (read-only v2)

`next-generation/CharoiteWine29V6ReadOnlyForensics.java` now:
- Runs an additional bounded **read-only** pass of ONLY the already preserved `v6-wine-direct-init.log` (2 MiB maximum) to identify ALL processes with nonzero trace exits, first mapped `.exe` basename, numeric exit and hex NTSTATUS, plus earliest bounded/redacted module-loader error. This explicitly targets the `0034` unknown failing process without presuming a DLL name.
- Keeps `v6-foreground-wineserver.log` total maximum **256 KiB**. Individual lines over 16 KiB are silently skipped and counted, rather than failing the whole audit. If the file exceeds the limit, its content is NOT READ and that condition is reported; other PE evidence is retained.
- Makes the server-audit exception stage/controlled reason visible and preserves earlier PE findings. No retries, Wine runs, prefix reads, registry contents, process creation, file creation, cleanup, permission edits or new scratch.
- The single current System test button is **"Inspect Wine29 v6 helper failure (read-only)"**. The old v6 one-shot execution is archived and hidden.
- In-place updating over the previous signed `com.charoitx` is mandatory to preserve logs, and stable Portal `com.charoite` is untouched.

## Next evidence target

First verify GitHub Actions passes 138 stable + all Next tests; versionCode 114, versionName 11.2-next.0.83; exact new v6 sealed native ELF hashes, same previous Next signing certificate and signed APK artifact. Use only verified Actions output for an APK link. On phone, perform ONLY the read-only v2 audit and paste the concise results. Investigate which executable process `0034` maps, the first relevant loader error, its exact `0xC0000135` status, and whether server log was truncated/overlong; don't start a new Wine process without future explicit authorization in a distinct scratch.
