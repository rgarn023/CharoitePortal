# Charoite Wine — source-controlled fork baseline

**Status (October 28, 2026): Wine 10.0 `wineserver` has now been cross-compiled for Android AArch64 at API 35 with 16 KiB ELF alignment, under the earlier patch series. A new Android machine-ID safety patch is undergoing CI validation. Full ARM64EC Wine DLLs, FEX and phone operation remain unverified.**

This is the beginning of **our modified Wine implementation** for Charoite Core Next. We are building an independently maintained **derivative** of Wine/Proton Wine, not claiming to have written Wine from scratch. The final runner will be paired with FEX (for compatible x86/x64 execution on ARM64), DXVK, VKD3D-Proton, Mesa/Turnip, a Wine prefix manager and Charoite's Android display/input subsystem.

## Source baseline

- Candidate upstream: [The412Banner/proton-wine](https://github.com/The412Banner/proton-wine), commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`, Proton 10 GE ARM64EC lineage reported by WeHavePhones.
- **Patch 0001**: ARM64 syscall-stub relocatability, suspension and thread-exit grace, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/arm64-copyable-syscalls-grace-wine10.patch). It is *not* originally authored by Charoite.
- **Patch 0100**: the rebased additive syscall-stub/dispatcher and ARM64 thread-grace changes. This derivative includes only hunks not already applied by the pinned upstream Android/ARM64EC prerequisite set; source attributed to the Patch 0001 vendor work. It is Charoite's maintained integration/rebase, not a claim of original authorship of the underlying Wine fixes.
- **Patch 0200**: Charoite-authored Android machine-ID fallback hardening. A native ARM64 build exposed that the upstream Android per-prefix fopen path could leave `FILE *f` uninitialized when `WINEPREFIX` is absent or the file is unreadable. The patch initializes the pointer and uses a deterministic Android-UID-derived machine ID if no prefix file is accessible, preventing undefined reads; native cross-build and on-device behavior must both be checked.
- **Patch 0002**: Android media-file Unix ownership / Windows SID behavior, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/server-android-file-owner-wine10.patch). It is *not* originally authored by Charoite.
- Wine and modifications remain subject to applicable Wine LGPL terms; this source is distributed alongside attribution to upstream and the source patches. Separate FEX, Mesa, DXVK and Proton license reviews are required for binaries.

**Patch order:** `patches/SERIES` applies 0100, 0002 and 0200 after the pinned Android/Bionic/FEX prerequisites and GE game fixes. Patch 0001 is kept as the original upstream reference only; reapplying all its suspension and SVE hunks duplicates the upstream patch list and fails. The validated prep script refuses an existing workspace and refuses fuzzy or partially applied Charoite patches.

These patches establish a reproducible starting point for **Charoite-maintained Wine patches**. They must be validated against the exact source state (including upstream GE and ARM64EC build prepatches) before building. No claim is made that merely applying these files produces a functioning Android Wine executable.

## First verified Charoite Wine build checkpoint

[GitHub Actions run 40709722718](https://github.com/rgarn023/CharoitePortal/actions/runs/40709722718) **SUCCESS** (source commit `c4292c9e78cb5c81607b6166d26031078e807a38`).

- The `prepare-source.sh` pipeline applied **70** pinned Android/Bionic/FEX prerequisite patches, **10** GE game-fix patches, then the **2** explicitly selected Charoite Wine patch-series entries, with no rejects or failed Git checks.
- The second job initialized the pinned DirectAudio submodule, ran Wine's `autogen.sh`, configured a minimal isolated host build and **compiled Wine 10.0 `server/wineserver`**, including patched `server/token.c`.
- Verified output: Linux **x86-64 ELF64** `wineserver`; `wineserver --version` returned **Wine 10.0**. This test only validates host-source compilation/linking; the Android-specific `__ANDROID__` runtime path, ARM64EC `ntdll`, FEX and GPU compatibility remain untested.
- Downloadable CI reports: `Charoite-Wine-Source-Validation` artifact **12824344954** and `Charoite-Wine-Host-Build-Validation` artifact **12825407581**. Reports deliberately do **not** include an installable Wine runtime.
- Original stable `com.charoite` APK remains on run `40641148611`; Next `com.charoitx` APK remains on run `40649258138`. Neither is replaced by this source build.

**Next native milestone:** reproducible pinned Android NDK/LLVM-MinGW ARM64EC cross-toolchain and host sysroot; compile `aarch64-windows/ntdll.dll`, `aarch64-unix/ntdll.so`, Android `wineserver` and supporting Wine pieces, verify 16-KiB-page alignment / ABI and hashes, then stage in a **new Charoite Next runtime slot and prefix only**. No game's anti-cheat or credentials are accessed by CI.

## First verified Android ARM64 build

[GitHub Actions run 40714449477](https://github.com/rgarn023/CharoitePortal/actions/runs/40714449477) **SUCCESS**, commit `f7476eab05b9705c1a2fcd7248442e2939f58490`, independent from the Portal APK. All three jobs passed: source patch series, native Linux host Wine server, and Android NDK r27d ARM64 cross-compile. The experimental `Charoite-Wine-Android-ARM64-Experimental` artifact ID **12827792939** contains the AArch64 server and inspection reports. ELF inspection reports four `LOAD` segments with 16 KiB alignment. **Not an installable Wine/Proton runtime.** The Android-native build also exposed the potential uninitialized Android machine-ID file pointer addressed by source patch 0200; a follow-up build must verify the fix.

## Engineering boundary

1. Prepare an isolated clone at the pinned upstream commit. Review and apply upstream GE and Android ARM64EC prerequisites **in the documented order**. Fail if conflicts occur; do not force a patch.
2. Apply Charoite's audited patch queue (the explicitly rebased vendor-derived active patch series) with reproducible integrity records.
3. Compile ARM64EC Windows `ntdll.dll`, Unix `ntdll.so`, `wineserver`, and necessary Wine libraries using a pinned cross toolchain and 16-KiB-page-compatible Android toolchain.
4. Run host smoke tests, ELF/PE ABI validation, and compare checksums and loader dependencies.
5. Use a **new app-private runner slot and new Windows prefix** in `com.charoitx`; never replace `com.charoite` files or in-place migrate games.
6. Only after device-proven Battle.net login and Steam client tests should the new runner become selectable. Modern DX12 or anti-cheat compatibility is **not** assumed from successful login.

### Security and user trust

No anti-cheat evasion, integrity-check tampering, hidden injection, kernel-driver spoofing or stealth processes. Honor publisher and anti-cheat platform support; some games will not run on Wine.

### Relationship to current APKs

- Stable app **Charoite Portal**: `com.charoite`, verified Actions run `40641148611`; preserved.
- Next app **Charoite Next**: `com.charoitx`, separate debug signing key and private data; current experimental APK initially contains the proven legacy Wine/Box64 engine plus an explicitly **not-ready** modern runner registry.
- **Charoite Wine binaries are not included yet.** Do not treat the future engine label as evidence of a completed Wine fork.
