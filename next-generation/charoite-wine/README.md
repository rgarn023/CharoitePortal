# Charoite Wine — source-controlled fork baseline

**Status (October 28/29, 2026): 22 same-source Wine ELF/PE bootstrap components plus all 76 pinned Wine NLS tables, including CP932, compiled and independently verified in one coherent experimental archive by GitHub Actions run 40806958409. The sampled import audit identifies 24 PE DLL names not yet bundled; this is NOT an installed or runnable Android Wine/Proton engine. FEX, Android display/graphics/input, complete PE/Unix dependency closure, isolated prefix startup and on-device execution remain outstanding.**

This is the beginning of **our modified Wine implementation** for Charoite Core Next. We are building an independently maintained **derivative** of Wine/Proton Wine, not claiming to have written Wine from scratch. The final runner will be paired with FEX (for compatible x86/x64 execution on ARM64), DXVK, VKD3D-Proton, Mesa/Turnip, a Wine prefix manager and Charoite's Android display/input subsystem.

## Latest actual-device milestone and Proton audit (October 29, 2026)

**Verified on Samsung Galaxy S26 Ultra:** Charoite Next v0.5 executed the
source-built, hash-verified Android AArch64 Charoite Wine loader and native
`ntdll` with exit code **0**, output **`wine-10.0`**.
The Charoite-maintained Android native loader path patch 0700 therefore passed
its first actual device test. This does **not** imply a functional Wine prefix,
Windows PE execution, games, Steam, Battle.net or anti-cheat support.

**Next v0.7 source (build and phone validation pending):** a new read-only,
same-bundle-hash-verified Android `wineserver --version` device probe is
packaged in Next only. It does not start a Wine server session or read existing
game/prefix data. The remaining runtime dependency audit, Android native
wineserver integration and isolated `wineboot` have not passed on device.

**What Proton functionality is incorporated?** Charoite Wine currently comes
from the pinned Proton-Wine fork plus 70 Android/ARM64EC prerequisites,
10 applied GE-Proton game-fixes and nine Charoite patch-series changes.
The pinned upstream GE script explicitly excludes its separate video rework.
DXVK, VKD3D-Proton, FEX, graphics drivers, multimedia, compatibility data and
the surrounding Proton environment are separately gated components, **not
proof of functional integrations merely because the Wine base is modified**.

See [PROTON_INTEGRATION_AUDIT.md](PROTON_INTEGRATION_AUDIT.md) for provenance,
missing components and the verified step-by-step Android implementation plan.
The comprehensive latest record remains
[docs/CURRENT_HANDOFF.md](../../docs/CURRENT_HANDOFF.md).

## Latest 22-component RPC/COM bootstrap — VERIFIED

[GitHub Actions run 40806958409](https://github.com/rgarn023/CharoitePortal/actions/runs/40806958409) **SUCCESS**, four jobs passed, code SHA `13a33686c3f93e0ac68b65fe7766d129ac0e6c99`. Artifact **Charoite-Wine-Coherent-Bootstrap-22-Experimental**, ID **12868478872**, adds source-built Windows ARM64X/ARM64EC `rpcrt4.dll`, `combase.dll`, `ole32.dll`, `comctl32.dll` to the previously source-verified 18-module archive and retains 76 Wine NLS tables. An independent verifier checks exact archive inventory, LLVM ARM64EC ABI evidence for the separately audited modules, file hashes, source reconstruction and startup/COM manifest digests, and verifies that no device/prefix/launch readiness is implied. CI also publishes standalone COM artifact ID **12868747669** and maintains 14-/18-component fallback archives.

After adding COM libraries, **24 Windows PE import names remain unbundled in the measured sample**: `bcrypt`, `cabinet`, `comdlg32`, `coml2`, `cryptnet`, `dnsapi`, `gdiplus`, `imm32`, `iphlpapi`, `mlang`, `mpr`, `msvcrt`, `newdev`, `oleacc`, `oleaut32`, `sechost`, `secur32`, `shcore`, `shdocvw`, `urlmon`, `uxtheme`, `wininet`, `winmm`, `wintrust`. The number may increase again as DLLs are added; this is **not complete Wine runtime closure**. There is still no fresh on-device Wineboot, modern ARM64EC/FEX launch or publisher-supported anti-cheat compatibility test. The installable Charoite Next v0.2 APK still contains **only seven experimental PE libraries as read-only diagnostic assets**; it does **not** incorporate or execute this 22-component source archive.

## Latest 18-component build

[Actions run 40803635407](https://github.com/rgarn023/CharoitePortal/actions/runs/40803635407) **SUCCESS** (code SHA `000fb2cb6c6bfe75f59967c4fd5913fe38a7ae2f`, four jobs green), artifact `Charoite-Wine-Coherent-Bootstrap-18-Experimental` ID **12867490929**. Adds source-built ARM64X/ARM64EC hybrid `win32u.dll`, `gdi32.dll`, `ucrtbase.dll`, `shell32.dll` to the previous 14 binaries, while retaining all 76 NLS tables including CP932. Independent ABI, SHA-256 and sampled-import gap verification passed. The prior 14-component bundle is still published separately.

The **23 Windows PE DLL imports not in this sampled bundle** are: `bcrypt`, `cabinet`, `combase`, `comctl32`, `comdlg32`, `cryptnet`, `dnsapi`, `gdiplus`, `imm32`, `iphlpapi`, `mlang`, `mpr`, `msvcrt`, `newdev`, `ole32`, `oleaut32`, `rpcrt4`, `sechost`, `shcore`, `shdocvw`, `urlmon`, `winmm`, `wintrust`. Four prior imports are now supplied, while some newly built DLLs revealed additional imports; this is **not** full dependency closure. The latest phone-installable APK remains [Charoite Next v0.2 diagnostics](https://github.com/rgarn023/CharoitePortal/actions/runs/40793135040), with its modern runtime still disabled. No source-built 18-component Wine runner is loaded or installed.

## Latest verified experimental bootstrap package

[GitHub Actions run 40801756245](https://github.com/rgarn023/CharoitePortal/actions/runs/40801756245) **SUCCESS** (code SHA `8e078e0dd484167ad9f4d42a1ae789bf35c1e506`, four jobs green). GitHub artifact `Charoite-Wine-Coherent-Bootstrap-NLS-Experimental`, ID `12866931158`, packages the same-built Android `wine` and `wineserver`, Unix `ntdll.so`, Windows ARM64EC `ntdll`, `kernelbase`, `kernel32`, seven API DLLs (`advapi32`, `user32`, `ws2_32`, `crypt32`, `setupapi`, `shlwapi`, `version`) and regular ARM64 `wineboot.exe`. Also includes all **76** Wine NLS tables from the exact pinned upstream `nls/Makefile.in`, including `c_932.nls`; every table is hash-checked and a missing/altered one fails verification. The archive is reproducible, source-attributed and **non-installable**, with `launch_ready=false` and `prefix_created=false`.

Independent `llvm-readobj`/ `llvm-readelf` inspection identified **24 PE imports not bundled** by this 14-component sample: `bcrypt`, `cabinet`, `combase`, `comdlg32`, `cryptnet`, `dnsapi`, `gdi32`, `imm32`, `iphlpapi`, `mlang`, `mpr`, `msvcrt`, `newdev`, `ole32`, `oleaut32`, `rpcrt4`, `sechost`, `shcore`, `shell32`, `ucrtbase`, `urlmon`, `win32u`, `winmm` and `wintrust`. An import inventory is not exhaustive dependency closure, and the archive has not been executed on Android.

The verified installable APK is still the **separate Next v0.2 diagnostic APK**, [run 40793135040](https://github.com/rgarn023/CharoitePortal/actions/runs/40793135040), package `com.charoitx`, artifact `12862243976`. It contains only seven new PE DLLs as read-only phone diagnostics and still uses the older Wine/Box64 runner. The new 14-component NLS archive is **CI output only**, not part of that APK. Do not replace installed prefixes, engines or saves.

## Source baseline

- Candidate upstream: [The412Banner/proton-wine](https://github.com/The412Banner/proton-wine), commit `c74acb09d51b447f5d5ac56c87608d3ec565a767`, Proton 10 GE ARM64EC lineage reported by WeHavePhones.
- **Patch 0001**: ARM64 syscall-stub relocatability, suspension and thread-exit grace, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/arm64-copyable-syscalls-grace-wine10.patch). It is *not* originally authored by Charoite.
- **Patch 0100**: the rebased additive syscall-stub/dispatcher and ARM64 thread-grace changes. This derivative includes only hunks not already applied by the pinned upstream Android/ARM64EC prerequisite set; source attributed to the Patch 0001 vendor work. It is Charoite's maintained integration/rebase, not a claim of original authorship of the underlying Wine fixes.
- **Patch 0600**: Charoite-authored type-safety correction to an imported Android clipboard Winsock integration. Upstream vendor code passed integer pointers to Win32 send/recv functions requiring char-byte buffers. This patch casts the six corresponding address arguments to const char* for send and char* for recv, without altering protocol bytes or clipboard storage. The 2026-10-28 ARM64EC user32 compile failed until this issue is addressed; source validation and new CI still required. Vendor Android clipboard patch remains separately attributed.
- **Patch 0500**: Charoite-authored Wine `winegcc` LLVM ARM64/ARM64EC linker correction. LLVM-MinGW `--no-default-config` reported a bare nonexistent `libgcc.a`, aborting both hybrid ARM64EC kernelbase/kernel32 DLL links and AArch64 Windows `wineboot.exe` linking. The patch skips that GCC archive for LLVM `CPU_ARM64` or `CPU_ARM64EC` PE targets **only** when `no_default_config` is set, preserving other compiler configurations. Both the ARM64EC kernel DLLs and regular ARM64 wineboot linker corrections were verified in successful CI builds.
- **Patch 0400**: Charoite-authored ARM64EC atomic correctness fix. Wine 10's fallback macros selected x86-64 inline `lock; xchg` instructions and x86 memory-ordering semantics when compiling hybrid ARM64EC code. This patch routes `InterlockedExchange` and pointer exchange through compiler atomic intrinsics and uses ARM acquire/release atomics for ARM64EC. Verified source application is separate from actual Android execution.
- **Patch 0300**: Charoite-authored ARM64EC Wine `__fastfail` fix. The cross compiler uses the hybrid ARM64EC target, which also defines x86-64 compatibility macros. The original conditional selected x86 `int 0x29` with an invalid `c` constraint during ARM64EC PE compilation; this patch chooses the native ARM64 `brk #0xf003` path for ARM64EC. This Wine 10 make graph uses the `aarch64-windows/ntdll.dll` final target and compiles ARM64EC-specific objects as dependencies. CI checks the resulting **PE machine ID 0xA641** and refuses a plain ARM64 PE, regardless of the output path.
- **Patch 0200**: Charoite-authored Android machine-ID fallback hardening. A native ARM64 build exposed that the upstream Android per-prefix fopen path could leave `FILE *f` uninitialized when `WINEPREFIX` is absent or the file is unreadable. The patch initializes the pointer and uses a deterministic Android-UID-derived machine ID if no prefix file is accessible, preventing undefined reads; native cross-build and on-device behavior must both be checked.
- **Patch 0002**: Android media-file Unix ownership / Windows SID behavior, attributed to [WeHavePhones's Wine patch](https://github.com/ashmerra/wehavephones/blob/main/patches/wine/server-android-file-owner-wine10.patch). It is *not* originally authored by Charoite.
- Wine and modifications remain subject to applicable Wine LGPL terms; this source is distributed alongside attribution to upstream and the source patches. Separate FEX, Mesa, DXVK and Proton license reviews are required for binaries.

**Patch 0700** (Android-only native loader): on Android ARM64, accept a probe-specific `CHAROITE_NTDLL_NATIVE_DIR` pointing to a verified APK native library directory and dlopen `libcharoite_wine_ntdll.so` when normal `ntdll.so` paths are absent. It does not install executable code or create a prefix; the native probe separately verifies both binary hashes. The fallback is off unless the explicit environment variable is supplied.

**Patch 0800** (Android-only, unverified source-build candidate): on Android AArch64 only, accept `CHAROITE_WINE26_DATA_DIR` as an explicit absolute private Wine data-directory override during native `ntdll` initialization; use `realpath` and fail on a missing directory or basic dot-segment traversal, and otherwise preserve the default installed Wine data-directory behavior. This targets the verified Galaxy v0.42 `locale.nls` / `l_intl.nls` failure after a fresh private prefix directory was created. It does not install an engine, execute games, or change earlier source artifacts. The phone probe must supply the path only after all 76 NLS files have passed SHA-256 verification in an entirely NEW, isolated sandbox.

**Patch order:** `patches/SERIES` applies 0100, 0002, 0200, 0300, 0400, 0500, 0600, 0700 and 0800 after the pinned Android/Bionic/FEX prerequisites and GE game fixes. Patch 0001 is kept as the original upstream reference only; reapplying all its suspension and SVE hunks duplicates the upstream patch list and fails. The validated prep script refuses an existing workspace and refuses fuzzy or partially applied Charoite patches.

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

## Verified Windows ARM64 wineboot bootstrap utility

[**GitHub Actions 40743283497 — SUCCESS**](https://github.com/rgarn023/CharoitePortal/actions/runs/40743283497) passed all four jobs and built Wine's `wineboot.exe` after the verified ARM64EC `kernelbase.dll` / `kernel32.dll` stage. The PE machine is **ordinary Windows ARM64 (0xAA64)** per Wine's actual Makefile target, rather than ARM64EC (0xA641). The independent ABI/manifest verifier passed. Artifact: `Charoite-Wine-ARM64-Wineboot-Experimental`, ID **12839039906**. The same run's ARM64EC kernel DLL artifact was **12840457429**, and coherent four-component base-slice artifact was **12839884074**.

**Not boot-tested**: The `wineboot.exe` module was compiled and checksum-validated, **not executed on Android**. No prefix, complete Wine runtime, FEX/graphics stack or Battle.net/Steam capability is proven. The Charoite-maintained source patch `0500-arm64ec-no-spurious-libgcc.patch` prevents Wine's Clang ARM64/ARM64EC link steps from appending an absent GCC `libgcc.a`; the proven patch must not be replaced with an overlapping linker experiment. Both installed apps and their existing games remain untouched.

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


## October 30, 2026 — 26-component security/service PE source-build candidate

The user's actual Galaxy S26 Ultra report for Next v0.38 confirms:
- Existing staged Windows modules **19/19 PE and 76/76 NLS SHA-verified**.
- Source-built ARM64 native Wine **`wine --version` exit 0, `wine-10.0`**.
- Source-built ARM64 native **`wineserver --version` exit 0, `Wine 10.0`**.
- No Wine session, prefix, Wineboot, FEX, graphics or Windows EXE yet.

The next independent source CI experiment targets four *measured* missing
ARM64EC Windows PE imports from the 22-component bundle:
`bcrypt.dll`, `secur32.dll`, `sechost.dll`, and `msvcrt.dll`.
`build-pe-services.sh` builds their exact `dlls/<name>/aarch64-windows/<name>.dll`
targets **from the same prepared and patched Wine source tree**; the
source and upstream patch attributions are preserved. The fail-closed
`verify-pe-services.py` checks every ARM64X/ARM64EC PE dual view,
size, SHA-256, exact ABI, audited import provenance, and NOT-READY flags.

If all modules compile and pass verification, the source workflow produces an
additional 26-component + 76-NLS **coherent archive** with version
`wine10-arm64ec-bootstrap.0.5`, dedicated source manifest hash,
and a freshly measured Windows import gap list. It retains the old validated
22-component fallback archive. Missing-import counts may change or grow after
new libraries expose more references. The new archive is **CI-only** until
proven and specifically integrated in a subsequent separately versioned
Next APK. The existing v0.38 app is unchanged and the built Wine engine
remains **not launch ready**.

No data is installed to a phone, no prefix is created, and no game/anti-cheat
behavior is claimed by this source-build experiment.


### ARM64EC bcrypt build correction (October 30)

First source CI extension [run 41116591592](https://github.com/rgarn023/CharoitePortal/actions/runs/41116591592)
**failed** in `bcrypt` compilation, not source validation or native `wine`.
The compiler error was `tomcrypt_macros.h:261/269: invalid input constraint 'c' in asm`:
LibTomCrypt chose an x86 rotate implementation under ARM64EC's x64 ABI
compatibility defines. The source build now passes
`CROSSCFLAGS="-O2 -g0 -DLTC_NO_ASM"` **only when cross-building bcrypt**,
enabling LibTomCrypt's supported portable rotate code. The pinned Wine source,
security API implementation, architecture checks, and binary hash verification
are unchanged. The correction needs a fresh GitHub source build to establish
actual 26-module success; no APK is changed by this experiment.

### Follow-up: generated ARM64EC wrapper fix

[Source CI run 41119319796](https://github.com/rgarn023/CharoitePortal/actions/runs/41119319796)
also failed on the same bcrypt inline asm: examination of the **actual emitted compiler
command** showed Wine's generated Makefile disregarded the `CROSSCFLAGS` override.
The source-build fix now changes ONLY the *temporary, generated ARM64EC compiler
wrapper* to add `-DLTC_NO_ASM` for `dlls/bcrypt/` compilation input paths,
and leaves every other compilation command unchanged. The wrapper is
checked against the expected exact source-build format before alteration;
the Wine source files and pinned source lineage remain untouched. All
independent Windows PE architecture, manifest and source SHA checks remain
mandatory. This correction is **unverified until the new CI run completes**.

### Third CI failure: shared LibTomCrypt assembly (October 30)

[Source run 41120261606](https://github.com/rgarn023/CharoitePortal/actions/runs/41120261606)
reached the added bcrypt module; its own `bcrypt_main.c` compiled with the
temporary ARM64EC wrapper, but compilation of shared
`libs/tomcrypt/src/ciphers/aes/aes.c` still selected incompatible x86
inline-assembly rotations. The source build now applies the supported
`-DLTC_NO_ASM` option to **all ARM64EC compiler invocations for the final
security/service module phase** (after assembly and independent verification
of the pre-existing 22-module baseline). It modifies only the ephemeral
compiler wrapper, not pinned source or installed apps. A new regression test
actually executes the wrapper rewrite against a safe mock compiler command,
checks its Bash syntax and confirms repeat rewriting is refused. The
corrected 26-component source build remains unverified pending CI.
