# Charoite Wine — source-controlled fork baseline

**Status (October 28, 2026): Wine 10.0 Android ARM64 loader + wineserver and the ARM64EC/Android `ntdll` pair now compile together into an ABI- and SHA-256-verified, source-attributed experimental slice. This is NOT yet a complete Android Windows compatibility runtime or an installable APK; FEX/graphics/prefix/device testing remains outstanding.**

This is the beginning of **our modified Wine implementation** for Charoite Core Next. We are building an independently maintained **derivative** of Wine/Proton Wine, not claiming to have written Wine from scratch. The final runner will be paired with FEX (for compatible x86/x64 execution on ARM64), DXVK, VKD3D-Proton, Mesa/Turnip, a Wine prefix manager and Charoite's Android display/input subsystem.

## Source baseline

- Candidate upstream: [The412Banner/proton-wine](https://github.com/The412Banner/proton-wine), commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`, Proton 10 GE ARM64EC lineage reported by WeHavePhones.
- **Patch 0001**: ARM64 syscall-stub relocatability, suspension and thread-exit grace, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/arm64-copyable-syscalls-grace-wine10.patch). It is *not* originally authored by Charoite.
- **Patch 0100**: the rebased additive syscall-stub/dispatcher and ARM64 thread-grace changes. This derivative includes only hunks not already applied by the pinned upstream Android/ARM64EC prerequisite set; source attributed to the Patch 0001 vendor work. It is Charoite's maintained integration/rebase, not a claim of original authorship of the underlying Wine fixes.
- **Patch 0500**: Charoite-authored Wine `winegcc` LLVM ARM64/ARM64EC linker correction. LLVM-MinGW `--no-default-config` reported a bare nonexistent `libgcc.a`, aborting both hybrid ARM64EC kernelbase/kernel32 DLL links and AArch64 Windows `wineboot.exe` linking. The patch skips that GCC archive for LLVM `CPU_ARM64` or `CPU_ARM64EC` PE targets **only** when `no_default_config` is set, preserving other compiler configurations. DLL links are CI verified; AArch64 wineboot linking must be checked in the next build.
- **Patch 0400**: Charoite-authored ARM64EC atomic correctness fix. Wine 10's fallback macros selected x86-64 inline `lock; xchg` instructions and x86 memory-ordering semantics when compiling hybrid ARM64EC code. This patch routes `InterlockedExchange` and pointer exchange through compiler atomic intrinsics and uses ARM acquire/release atomics for ARM64EC. Verified source application is separate from actual Android execution.
- **Patch 0300**: Charoite-authored ARM64EC Wine `__fastfail` fix. The cross compiler uses the hybrid ARM64EC target, which also defines x86-64 compatibility macros. The original conditional selected x86 `int 0x29` with an invalid `c` constraint during ARM64EC PE compilation; this patch chooses the native ARM64 `brk #0xf003` path for ARM64EC. This Wine 10 make graph uses the `aarch64-windows/ntdll.dll` final target and compiles ARM64EC-specific objects as dependencies. CI checks the resulting **PE machine ID 0xA641** and refuses a plain ARM64 PE, regardless of the output path.
- **Patch 0200**: Charoite-authored Android machine-ID fallback hardening. A native ARM64 build exposed that the upstream Android per-prefix fopen path could leave `FILE *f` uninitialized when `WINEPREFIX` is absent or the file is unreadable. The patch initializes the pointer and uses a deterministic Android-UID-derived machine ID if no prefix file is accessible, preventing undefined reads; native cross-build and on-device behavior must both be checked.
- **Patch 0002**: Android media-file Unix ownership / Windows SID behavior, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/server-android-file-owner-wine10.patch). It is *not* originally authored by Charoite.
- Wine and modifications remain subject to applicable Wine LGPL terms; this source is distributed alongside attribution to upstream and the source patches. Separate FEX, Mesa, DXVK and Proton license reviews are required for binaries.

**Patch order:** `patches/SERIES` applies 0100, 0002, 0200, 0300, 0400 and 0500 after the pinned Android/Bionic/FEX prerequisites and GE game fixes. Patch 0001 is kept as the original upstream reference only; reapplying all its suspension and SVE hunks duplicates the upstream patch list and fails. The validated prep script refuses an existing workspace and refuses fuzzy or partially applied Charoite patches.

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

## Verified Android-native checkpoint with Charoite safety patch

**GitHub Actions [40715586360](https://github.com/rgarn023/CharoitePortal/actions/runs/40715586360) passed all three jobs** at source commit `244cf07400b7f5603d4f153bee5b034eadfcb73b`. CI verified the 3-entry Charoite patch series, host Wine server compilation, and NDK r27d Android API 35 **AArch64 wineserver** cross-compilation. ELF `LOAD` alignment values: `[16384, 16384, 16384, 16384]`. The uninitialized `FILE *f` warning from the preceding run no longer appears (an unrelated unused-variable warning remains).

Experimental Android-native artifact: `Charoite-Wine-Android-ARM64-Experimental` ID **12828870997**, with checksums and ELF reports. This file is a component, **not a complete runner or APK**, and has **not been executed on the Galaxy S26 Ultra**. No FEX bridges, ARM64EC `ntdll.dll`/`ntdll.so`, DXVK/VKD3D or Steam/Battle.net integration exists yet in this experimental output.

## Verified Charoite Wine ARM64EC ntdll compilation

[**GitHub Actions run 40721844963 — SUCCESS**](https://github.com/rgarn023/CharoitePortal/actions/runs/40721844963), compiled code SHA `26c7a33c7cd6207123211c1c1af20df47c62e167`. **All four independent CI jobs passed**: source patch validation (5 active Charoite Wine patches after 70 Android/Bionic/FEX prerequisites and 10 GE fixes), Linux host wineserver, Android AArch64 wineserver, and newly built ARM64EC PE + Android Unix ntdll pair.

- **Windows PE:** `ntdll-arm64ec.dll` verified by LLVM `llvm-readobj` as `IMAGE_FILE_MACHINE_ARM64EC (0xA641)`, not ordinary ARM64.
- **Android Unix:** `ntdll-arm64-android.so` verified as AArch64 ELF with four `PT_LOAD` segments each aligned to **16,384 bytes**.
- **Pinned toolchains:** Android NDK `27.3.13750724` API 35; LLVM-MinGW UCRT 20261020 pinned SHA-256 `55064b60b991a1e1e8090b8c2f84e82b22cfe5903d12c159d65064cf5e8ae335`.
- **Binary artifact:** `Charoite-Wine-ARM64EC-NTDLL-Experimental`, GitHub artifact **12831021769** (contains the verified ntdll pair, ELF and PE inspection reports and checksums). Android wineserver artifact `Charoite-Wine-Android-ARM64-Experimental` **12829954961**; host report **12831640935**; source provenance **12830373158**.
- Charoite-specific corrections `0300` and `0400` prevent ARM64EC's hybrid `__x86_64__` macro from selecting x86 fast-fail and atomic assembly instructions; ARM64EC acquires correct compiler builtin atomic operations and memory-ordering semantics. The code changes are maintained as LGPL-compatible source patches, not as unauthorized originals.
- **No Android APK containing this modified Wine was built.** These are standalone native components. No device execution test, working Wine session, Battle.net/Steam operation or anti-cheat support is established by CI.

**Next milestone:** source/build the rest of the compatible Android ARM64EC Wine 10 runner, FEX x86/x64 bridge and dependent graphics components; create an **entirely new app-private runtime slot and Wine prefix** in `com.charoitx` with manifest checksums, reversible staging and no migrations; run basic Windows program and rendering smoke tests on Galaxy S26 Ultra before enabling an engine selector. Neither stable `com.charoite` nor existing `com.charoitx` installations should be overwritten.

## Verified coherent four-component Charoite Wine base slice

[**GitHub Actions run 40728026115 — SUCCESS**](https://github.com/rgarn023/CharoitePortal/actions/runs/40728026115), compiled source SHA `fae65c2491e1778cabd323dec507662feed82092`, **all four jobs successful** and **21 source/archive tests passed**.

The new `Charoite-Wine-ARM64EC-Base-Slice-Experimental` artifact **12834111695** is a *single-source, ABI-checked build* containing the **Android AArch64 `wine` loader, Android AArch64 `wineserver`, Android AArch64 Unix `ntdll.so` and Windows ARM64EC PE `ntdll.dll`**. They were compiled together from the same patched and toolchain-pinned Wine 10 tree. CI checked all ELF `PT_LOAD` alignments (minimum 16 KiB), ARM64EC machine `0xA641`, component SHA-256, member paths, and a second read-only archive verifier. It includes a deterministic JSON manifest with `launch_ready=false` / `installable=false`.

The archive also contains the original Wine `COPYING.LIB` / `LICENSE`, attributed vendor MIT notice, and `charoite-source-delta.patch` (the corresponding source differences from the pinned Wine upstream commit). Each source/license file also has a SHA-256 checked at package creation and verification. This improves source provenance but **does not substitute for reviewing future third-party FEX, GE, Vulkan and related licensing obligations**.

Other verified artifacts on the same run: `Charoite-Wine-ARM64EC-NTDLL-Experimental` ID **12833398102** (separate ntdll pair), `Charoite-Wine-Android-ARM64-Experimental` ID **12833862177**, source-validation ID **12833219346**, host report ID **12834051928**.

**Important limitations:** this four-component bundle is **not** a complete executable Wine/Proton environment. It lacks a full compatible Wine PE/Unix DLL/NLS tree, FEX CPU translation bridge, Windows prefix provisioning, Android graphics/display/input integrations, DXVK/VKD3D and a verified installation/rollback path. No actual Galaxy S26 Ultra process was launched and neither Battle.net nor Steam or anti-cheat support was tested. Existing stable `com.charoite` and side-by-side `com.charoitx` APKs and user data are unchanged.

**Next source/runtime work:** pin and validate a complete compatible Wine/Proton 10 ARM64EC layer and FEX components, preserve licenses and hashes, audit the manifest's listed Android DT_NEEDED dependencies, stage in a new Next-only runtime slot, create a fresh prefix, then run controlled Windows-program tests on device before enabling the modern engine.

## Verified ARM64EC kernelbase and kernel32 build

[**GitHub Actions run 40739844466 — SUCCESS**](https://github.com/rgarn023/CharoitePortal/actions/runs/40739844466), compiled source SHA `fc561a467c60a756ebd136f92091c0bb44a1a210`. All four CI jobs passed. After the coherent source-verified `wine` loader, `wineserver`, `ntdll.dll` and `ntdll.so` were built, the same configured Wine 10 tree successfully linked **Windows `kernelbase.dll` and `kernel32.dll`**, both confirmed as genuine **ARM64EC (machine 0xA641)**, not generic ARM64 PE.

The separate `Charoite-Wine-ARM64EC-Kernel-Experimental` artifact ID **12838573488** contains both DLLs, LLVM PE machine reports and SHA-256 manifest. `verify-kernel-bridge.py` checks files, SHA hashes, ABI and disabled state without installing anything. Source patch `0500-arm64ec-no-spurious-libgcc.patch` corrects Wine's `winegcc` wrapper so Clang ARM64EC `-nodefaultlibs` mode does not append a nonexistent `libgcc.a`; other targets remain unchanged.

Other current artifacts from the same run include the coherent source-provenance base slice **12837799898**, standalone ARM64EC ntdll pair **12838443793**, Android ARM64 wineserver **12838564522**, source provenance **12839490543** and host compilation report **12839820086**.

**Not bootable yet.** Kernel32/kernelbase are only two required Windows API DLLs. Missing components still include Wine's boot program, its transitive API DLLs/Unix interfaces, a full runtime and NLS tree, FEX, graphics/display/input, isolated Windows prefix and phone validation. Both installed Charoite apps and game data remain unchanged.

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
