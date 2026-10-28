# Charoite Wine — source-controlled fork baseline

**Status (October 28, 2026): source patch set only; not compiled, bundled, or phone-tested.**

This is the beginning of **our modified Wine implementation** for Charoite Core Next. We are building an independently maintained **derivative** of Wine/Proton Wine, not claiming to have written Wine from scratch. The final runner will be paired with FEX (for compatible x86/x64 execution on ARM64), DXVK, VKD3D-Proton, Mesa/Turnip, a Wine prefix manager and Charoite's Android display/input subsystem.

## Source baseline

- Candidate upstream: [The412Banner/proton-wine](https://github.com/The412Banner/proton-wine), commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`, Proton 10 GE ARM64EC lineage reported by WeHavePhones.
- **Patch 0001**: ARM64 syscall-stub relocatability, suspension and thread-exit grace, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/arm64-copyable-syscalls-grace-wine10.patch). It is *not* originally authored by Charoite.
- **Patch 0100**: the rebased additive syscall-stub/dispatcher and ARM64 thread-grace changes. This derivative includes only hunks not already applied by the pinned upstream Android/ARM64EC prerequisite set; source attributed to the Patch 0001 vendor work. It is Charoite's maintained integration/rebase, not a claim of original authorship of the underlying Wine fixes.
- **Patch 0002**: Android media-file Unix ownership / Windows SID behavior, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/server-android-file-owner-wine10.patch). It is *not* originally authored by Charoite.
- Wine and modifications remain subject to applicable Wine LGPL terms; this source is distributed alongside attribution to upstream and the source patches. Separate FEX, Mesa, DXVK and Proton license reviews are required for binaries.

**Patch order:** `patches/SERIES` applies 0100 and 0002 after the pinned Android/Bionic/FEX prerequisites and GE game fixes. Patch 0001 is kept as the original upstream reference only; reapplying all its suspension and SVE hunks duplicates the upstream patch list and fails. The validated prep script refuses an existing workspace and refuses fuzzy or partially applied Charoite patches.

These patches establish a reproducible starting point for **Charoite-maintained Wine patches**. They must be validated against the exact source state (including upstream GE and ARM64EC build prepatches) before building. No claim is made that merely applying these files produces a functioning Android Wine executable.

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
