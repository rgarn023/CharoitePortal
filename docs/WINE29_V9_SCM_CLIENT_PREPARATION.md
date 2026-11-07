# Wine29 v9 — SCM client source-only preparation and future isolated gate

Date: November 7, 2026. Current experimental Android package: `com.charoitx`; last **verified signed phone APK is v0.90**. This document is a development plan, not an authorization for any v9 device execution.

## Grounded v8 state

The owner ran the v0.90 preserved v8 audit **read-only**, reporting two Wineboot PIDs (0x0024, 0x002c) with observed exit 0, services.exe mapped in PID 0x0034, userenv.dll mapped in the same service PID, zero observed DLL-not-found/module errors and no captured services PID exit. All three registry files are now nonempty (system.reg 1,981 bytes, user.reg 1,858, userdef.reg 123); contents were never opened. C: relative symlink is intact, but it and drive_c were precreated. A single server shutdown marker was recorded. This supports **resolution of the specific v7 userenv load failure**, NOT persistent service-manager readiness, valid registry content, fully initialized Windows prefix or application/game support.

**Do not rerun v8 or delete/modify its logs, registries, scratch or earlier generations.** Stable Charoite Portal remains `com.charoite`, and Next remains isolated as `com.charoitx`.

## Source-side next gate (no phone changes)

The pinned exact Wine source is `The412Banner/proton-wine` commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`. At that commit, `programs/sc/Makefile.in` declares `MODULE = sc.exe` and `IMPORTS = advapi32`. A new, independent **GitHub Actions source-candidate workflow** will:

1. Fetch the already pinned sealed 34-DLL/76-NLS data archive from run 41947164001 and verify the exact established SHA-256 before using it as an import-provider inventory.
2. Prepare this identical pinned Wine source using the repository's existing checksummed patch chain and v6 loader patch on an ephemeral CI runner, and cross-build `programs/sc/aarch64-windows/sc.exe` using pinned Android NDK/LLVM-MinGW.
3. Validate the source-built PE signature and ARM64 machine, inventory ordinary/delay imports, explicitly report gaps against the 34 sealed providers, and publish only a manifest + PE candidate. **Any import gaps remain BLOCKERS for an eventual phone test until their source-coherent providers are verified.**
4. Never execute Wine, Wineboot, wineserver, services.exe, sc.exe or any Windows program in CI; never create or touch Android prefixes. No APK produced by this candidate workflow.

## Separate future on-phone gate — NOT AUTHORIZED YET

A future v9 APK would require a verified source candidate, closure of ALL PE imports, SHA-256-verified v6 native cohort, v7 services.exe, v8 userenv.dll and existing sealed PE/NLS, a NEW PRIVATE scratch (e.g. `charoite-next-wine29-scm-v9`), fail-closed uniqueness checks, and a separate explicit in-app opt-in. Its bounded one-shot experiment would initialize only the **new v9 prefix**, then attempt a minimal SCM status query through `sc.exe`, collecting exit status, Windows error/status, and short redacted request/response clues. It must not query existing user or game prefixes, run games, install software, touch stable Portal, clear data, retry historical generations or automatically retry v9. A successful service query would establish only basic SCM reachability, **not Windows 11/games/graphics/Steam/Battle.net readiness**.

Until a verified candidate and a separate user action, v9 device execution remains **NOT ATTEMPTED / NOT AUTHORIZED**. Current System UI remains v0.90's single v8 read-only auditor.

## Release and preservation policy

No Android APK/version bump comes from source-candidate CI alone. Latest verified Android update remains [signed v0.90 Actions run 42424819789](https://github.com/rgarn023/CharoitePortal/actions/runs/42424819789), [artifact 13595038107](https://github.com/rgarn023/CharoitePortal/actions/runs/42424819789/artifacts/13595038107). Never uninstall or clear `com.charoitx`; preserve all v8 evidence.
