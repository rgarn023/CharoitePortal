# Wine29 v6 phone results and bounded read-only completion audit

**Date:** November 7, 2026. **Package:** experimental Next `com.charoitx`.
**Phone report source:** user's executed **one-shot v6**, running signed `11.2-next.0.81` (code 112).
**New code:** v0.82 (code 113) preserves all old data and runs a read-only forensics function only when the user taps its System button.

## What v6 actually proved

The v6 phone report's 34-DLL header/delay/direct import preflight and 111 PE/NLS plus three APK-native ELF hashes all PASS. Native loader + matched NTDLL + wineserver selectors were independently source-verified. The v6 fresh-only private C: relative symlink was present before execution. A dedicated foreground wineserver showed its socket and lock. Direct ARM64 `wineboot.exe -i` completed in under 45 seconds with parent process exit code 0, without timeout or exceeding the 2-MiB PE log limit.

This time Wine's automatic child process **did start**: a native trace shows the main process `0024:NtCreateUserProcess C:\\windows\\system32\\wineboot.exe --init` followed by **`002c`** loading its own `wineboot.exe` PE, `ntdll.dll` PE and the `apisetschema.dll` API-set. In v5 the corresponding internal launch stopped with `run_wineboot failed to start wineboot 1`. In v6 that marker was **absent**, along with the new `CHAROITE_WINE29_V6_CHILD_EXECV_FAILURE` marker, and no `c0000135` was observed by the original summary test. This is a material advance of the isolated Wine29 child native reexec path.

The v6 report independently observes Wine-created `drive_c/windows`, `windows/system32`, `users`, `users/xuser/AppData`, and the private `system.reg`, `user.reg`, `userdef.reg` files. `drive_c` itself and `dosdevices/c:` were **precreated** by the test, so their mere presence is not Wine initialization proof. `drive_c/Program Files` was not present, which leaves prefix completeness unverified. The foreground wineserver was no longer alive after the direct PE process, but this is not independently proof of failure. A parent `wineboot -i` exit code 0 is not evidence of the child process' final completion status.

**Verdict: SUCCESSFUL CHILD STARTUP AND PE MAPPING; PREFIX INITIALIZATION PARTIAL / NOT YET VERIFIED.** No general Windows EXE/game, graphics/FEX/Proton compatibility, or new active engine is proven. Do **not** run v6 a second time, clear storage, or touch any prior scratch. The user already provided its one-shot report.

## Exact next step: a no-execution postmortem

`next-generation/CharoiteWine29V6ReadOnlyForensics.java` reads ONLY the two exact existing logs `v6-wine-direct-init.log` (2 MiB cap) and `v6-foreground-wineserver.log` (256 KiB cap) plus a small allowlist of **file type/presence only** under the one v6 scratch. It never reads registry contents. It detects internal --init creation requests, per-Wine-process identifiers and PE Wineboot/NTDLL/kernel32/API-set mappings, **observed process-exit trace status**, execv failure markers, loader/status failure markers, warnings and bounded server statistics. Sensitive lines and scratch paths are redacted; no logs or files are written, and no processes are started. No previous Wine29 v1-v5/Wine28, Portal, games, saves, user prefixes or rootfs are even opened.

In `next-generation/prepare_next.py`, the old Wine29 v6 execution UI is archived by `showArchivedWine29V6Execution = false`. The sole current System test button is **"Inspect Wine29 v6 child startup (read-only)"**. Source changes are additive; the already installed Next app retains its private data on an in-place signed update.

The new postmortem will help answer whether the child completed successfully or exited abnormally; it is **not an automated second execution** and **not** a claim that the Wine prefix is fully initialized. Only after reviewing that evidence should we consider a fresh v7 one-shot runtime smoke with separate user consent and its own scratch.

## Release gates

- Preserve `com.charoitx` and use persisted Charoite Next signing identity.
- Bump Next version to `11.2-next.0.82` / code 113; no stable Portal version change.
- Add bounded read-only test `next-generation/tests/test_wine29_v6_readonly_forensics_contract.py`, plus GitHub Actions gate `WINE29_V6_PRESERVED_READONLY_FORENSICS=PASS`.
- Verify full regression suites, APK signed hash, native v6 three-ELF SHA and old 111-file PE/NLS and native cohorts preserved, and publish signed v0.82 APK Actions artifact. **Do not invent artifact links or declare a build complete until GitHub confirms.**
