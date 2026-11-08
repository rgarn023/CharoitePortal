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


## Source candidate verified; Android integration in validation

**Source candidate PASS (November 7, 2026):** [Actions run 42426173638](https://github.com/rgarn023/CharoitePortal/actions/runs/42426173638) finished SUCCESS from exact source checkout `311a141fa255886020c5e2adab643db0e954a07a`. The true Windows ARM64 `programs/sc/aarch64-windows/sc.exe` built successfully; static COFF machine AA64 and pinned-provider import inventory PASS. **Zero unbundled ordinary or delayed imports.** Non-APK [source artifact 13595845868](https://github.com/rgarn023/CharoitePortal/actions/runs/42426173638/artifacts/13595845868), ZIP **10,088 B**, digest `sha256:f8ac4ddbdca513a07ee15b29101b78203d07cd9094e65357e50b9709887e6c54`, retention until 2027-01-06.

**Historical Android v0.91 integration candidate (subsequently verified below):** `next-generation/stage_wine29_v9_sc.py` verifies source-run, SHA, pinned manifest, true Windows ARM64 PE, exact importer closure, source-coherent v6 native/111 sealed/v7 services/v8 userenv ancestry, then adds NEW `assets/charoite-next/wine29-v9-sc/` payload only to the experimental Next APK in CI. `next-generation/CharoiteWine29V9ScmProbe.java` fail-closes source-verified v6/v7/v8/v9 assets BEFORE allocating new private `charoite-next-wine29-scm-v9` scratch. No reuse of old v8 scratch. It stages independent copies, starts only a new v9 wineserver and `wineboot -i` with distinct explicit in-app one-shot consent; after successful `-i`, it attempts `sc.exe query` **only if the same private v9 server remains alive**. Query bounded to 12 seconds / 512 KiB, raw logs never copied into chat; no automatic retry, no user games or stable package accesses. It cannot establish game or Windows 11 support by itself. Three new log names: `v9-foreground-wineserver.log`, `v9-wine-direct-init.log`, `v9-sc-query.log`. All evidence retained after one-shot; the prior v8 UI action is archived.

`next-generation/prepare_next.py` targets experimental `com.charoitx` versionCode **122** / versionName **11.2-next.0.91**. Exact release test suite and GitHub workflow are updated; first source test candidate failed only two stale/overstrict assertion strings, corrected at commit `ff13406b2c5e8ac8352fedbb4473a0728d04dccc`. [APK CI run 42435538563](https://github.com/rgarn023/CharoitePortal/actions/runs/42435538563) is the current verification attempt. **Historical release gate, now satisfied by the verified signed release below.** Until then, verified v0.90 remains the last signed upgrade.

**Consent boundary:** Preparing an APK with an explicitly consent-gated v9 test does not authorize running v9 on the phone. Nothing starts until the owner installs a verified APK and affirmatively presses the new test button. Automatic diagnostics remain separate opt-in. No direct on-device Wine process was executed from CI.

## Verified signed v0.91 Android release and consented next action

The final source release [Actions 42435538563](https://github.com/rgarn023/CharoitePortal/actions/runs/42435538563) completed **SUCCESS** using exact APK source commit `ff13406b2c5e8ac8352fedbb4473a0728d04dccc`. Stable 138 and Next 201 regression tests PASS, pinned-source v9 SCM client SHA-256/PE/module provenance checks PASS, Gradle assembled, package `com.charoitx` versionCode 122 / versionName `11.2-next.0.91`, and the persisted Next signing certificate `d6790e512d182a4642d9a558db2508a3e20e82b5f5aa54847fd6206e7d42a175` matched.

**[Direct signed Android APK artifact 13599217365](https://github.com/rgarn023/CharoitePortal/actions/runs/42435538563/artifacts/13599217365)** — ZIP 461,560,259 bytes, SHA-256 `7e11082036bf921083f672899d7c87cb36780040c9d8f53f9a4b2e73a72443f6`, expiry 2027-02-06T01:44:19Z. [Licenses and attribution 13599775642](https://github.com/rgarn023/CharoitePortal/actions/runs/42435538563/artifacts/13599775642). Earlier attempted v0.91 test-only CI run 42435461872 failed two incorrect assertions and produced no APK; the final release was successful.

**Next owner step:** install in place over the already-signed experimental `com.charoitx` (NO uninstall/clear). Under System the only current Wine29 test is `Test Wine29 v9 Service Manager query (one-shot)`, which presents a second, explicit authorization warning before creating the new private v9 scratch. The separate experimental package, prior v8 preserved data, stable `com.charoite`, games/saves/user prefixes and rootfs must not be read or modified. One tap can run real Wine/Wineboot/internal services plus a bounded SCM client query if the same v9 server remains alive. Preserve raw v9 logs and copy only the short report with END marker. If a used v9 scratch already exists, do not retry. **No on-device v9 test has occurred in CI, and a successful APK does not itself prove SCM readiness.**
