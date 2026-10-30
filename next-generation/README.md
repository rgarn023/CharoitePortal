# Charoite Core Next (experimental)

**First CI-verified, side-by-side Android development APK:** [GitHub Actions run 40649258138](https://github.com/rgarn023/CharoitePortal/actions/runs/40649258138)

- Artifact: `Charoite-Core-Next-Android-APK` (ID `12799426447`)
- App: **Charoite Next**, `com.charoitx` (separate from stable **Charoite Portal**, `com.charoite`)
- Runtime code commit: `aa89290a7e7a326ce495b6f3226f74adf8daf58a`
- CI: **138 existing and 6 Next isolation tests passed**, signed APK built; native loader paths and app label checked.
- IMPORTANT: **Next currently includes the stable Wine/Box64 engine**, not a working new Proton/FEX runner. Its System screen honestly shows modern engines as **NOT READY**. Do not claim Battle.net or Steam is working because this APK built.

## What we are developing

An original **Charoite integration and compatibility platform**, incorporating a **Charoite-maintained fork of Wine/Proton Wine**, ARM64EC, FEX or Box64 translation, DirectX→Vulkan via DXVK/VKD3D-Proton, Mesa/Turnip, Android display/input integration, per-game compatibility profiles and multi-engine selection.

A modified Wine implementation will be **derived from licensed upstream Wine/Proton Wine sources**. This is not a clean-room rewrite of all Windows APIs. See [Charoite Wine source baseline](charoite-wine/README.md). The original attributed Wine patches are retained with provenance, alongside Charoite-authored ARM64EC and Android corrections. The patched Wine **source and individual native components have now compiled successfully in standalone CI**; **the new Wine runtime has still not been installed in this APK**.

## Why a separate app?

The original `com.charoite` data, Wine C: drive, TPDP and other installed games are intentionally inaccessible to `com.charoitx` under Android app isolation. The two editions have separate app identities, signing keystores and private storage. Never uninstall or clear the stable app as part of a Next trial.

## Current Charoite Wine compilation milestone

[**GitHub Actions 40728026115**](https://github.com/rgarn023/CharoitePortal/actions/runs/40728026115) passed all four CI jobs, including **21 source/archive tests**. The experimental `Charoite-Wine-ARM64EC-Base-Slice-Experimental` artifact ID **12834111695** contains the **Android ARM64 `wine` launcher, Android ARM64 `wineserver`, ARM64EC PE `ntdll.dll`, and Android ARM64 `ntdll.so`**, built from the same patched Wine source and toolchain, with checked ABI, SHA-256, Wine LGPL notices and corresponding source delta.

**This is a development bundle, not an installable Wine runner or Android APK.** It is explicitly marked `launch_ready=false`. It does **not** replace the Next APK or original Portal, and it has not been run on the Galaxy S26 Ultra. A complete Wine/GE-Proton runtime, FEX, Vulkan graphics, dedicated prefix and device tests are still necessary for Battle.net and Steam. See [Charoite Wine details](charoite-wine/README.md) and [current GitHub handoff](../docs/CURRENT_HANDOFF.md).

## Latest experimental build and next compatibility milestone

**Next v0.35, signed Android APK:** [GitHub Actions run 41105956380](https://github.com/rgarn023/CharoitePortal/actions/runs/41105956380), [signed APK artifact 13000548951](https://github.com/rgarn023/CharoitePortal/actions/runs/41105956380/artifacts/13000548951). 41 Next and 138 stable tests passed, Android package `com.charoitx` code 66. Install over existing Next without clearing data. The v0.34 glow / inward-flowing crystal energy boot design remains unchanged.

**Next-only System → Audit modern Wine bootstrap prerequisites** reads a fail-closed, source-verified report derived from the pinned 22-component/76-NLS Wine bootstrap archive. Reports unbundled Windows imports, audited Android native dependencies and explicit missing FEX/graphics/prefix/device steps. **No Wineboot, new Windows prefix or game execution is attempted; modern runner still NOT READY.** Next milestone is resolving the reported bootstrap gaps, assembling an isolated versioned Wine+FEX runtime slot and testing on Galaxy without touching the stable Portal or the user's existing game environments.

## Device validation roadmap

1. Install Next **alongside** stable Portal; confirm both icons/apps and each edition's private data are independent.
2. Validate Next legacy engine and native graphics/input on Galaxy S26 Ultra. CI does not replace device testing.
3. Assemble an attributable source-built and hash-verified Charoite Wine ARM64EC runner, FEX bridges, Vulkan drivers and renderer DLLs.
4. Stage assets atomically in a NEW Next runtime directory, create a NEW dedicated Windows prefix, perform Windows program tests and rollback.
5. Test Battle.net launcher/login and Steam client separately, then game installs and DirectX 9/11/12 compatibility. Add game-specific profiles only after evidence.
6. Honor publisher support for anti-cheat. No bypasses, stealth, kernel-driver impersonation or universal game compatibility claims.

**Downloads:** Open the linked GitHub Actions run, expand **Artifacts**, and select `Charoite-Core-Next-Android-APK`. Unzip, then install the contained APK. Do not uninstall the existing Portal.

**Stable Portal:** [last verified stable APK run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611), package `com.charoite`. Unchanged.

## Next v0.36 — coherent bootstrap archive bundled in the APK

The experimental `com.charoitx` APK now contains the **complete, pinned,
independently verified 22-component Wine bootstrap archive with all 76 NLS tables**
as an inert asset. This is additional to the three individually packaged native
ELF `--version` probes. CI validates the original cross-build manifest and every
component hash before staging, then validates that the final signed APK contains
the exact archive bytes and source manifest digests.

In System, **Verify packaged modern Wine modules** verifies the APK archive
SHA-256 and size on-device, without extracting, executing, or modifying any
prefix. Report status truthfully: modules *packaged* does not mean a usable
Wine runtime. FEX, Android-native module layout, fresh prefix provisioning,
graphics, Wineboot and game compatibility are **not implemented/verified** by
this milestone. Stable `com.charoite` remains unchanged.

Next: inspect the v0.36 on-device module report and native wineserver
`--version`; then implement versioned, hash-gated, Next-only module staging
and fresh-prefix boot probes with rollback, never touching pre-existing data.


## Next v0.37 — consent-gated isolated PE/NLS staging

The S26 Ultra device confirmed the v0.36 complete Wine archive SHA-256 and
component inventory (22/22 components, 19 Windows PE, 3 native ELF, 76 NLS;
24 observed PE import gaps). No Wineboot was executed.

The v0.37 APK stages the 19 Windows PE and 76 NLS source-verified modules
as individual immutable .bin assets alongside the original complete archive.
A source-linked index pins each module's size and SHA-256. CI verifies all
95 modules inside the final signed APK.

System -> Stage isolated modern Wine PE/NLS modules is opt-in. It first
re-verifies the full APK archive and validates the exact file allowlist.
The staging area is in getNoBackupFilesDir()/charoite-next-isolated-wine/.
No existing runtime, rootfs, prefix, save or game is accessed or modified.
On success 95 hashes are checked again and the pending directory is renamed
to a versioned staged slot. If interrupted, pending data is left quarantined;
repeated requests verify staged data without overwriting it.

This is NOT a runnable Wine environment. Native ELF, FEX, graphics and
wineboot remain blocked and unverified. The approved energy boot is unchanged.

Next: resolve missing PE/ABI modules, create a separate native loader
layout, and attempt an isolated disposable-prefix Wineboot only after
the new staging and on-device prerequisites are verified.


## Next v0.38 — on-device native Wine bootstrap version gate

The S26 Ultra user reported `RESULT: PASS` for v0.37's **19/19 PE
plus 76/76 NLS** staged-data integrity, with no pre-existing Wine
prefix, save or rootfs access. This is independent of native Wine startup.

Next v0.38 adds **System → Test native Wine startup prerequisites**
with explicit confirmation. The gate first runs read-only SHA-256 checks
on the already-staged 95 PE/NLS files. If they are intact, it runs only
the **APK-owned, independently source-verified** native ARM64 `wine
--version`, then the pinned `wineserver --version`, in sequence.
The probes sanitize all inherited environment variables, set no
`WINEPREFIX` or `HOME`, time out, and cannot launch arbitrary code
paths. Failed staging/loader/server blocks later tests and yields a
copyable report. No staging writes, Windows PE execution, server session,
wineboot, FEX or GPU initialization occurs as part of this gate.

**Do not infer Wineboot readiness** from passing version probes. The
24 observed missing Windows PE imports, native Unix module layout,
FEX/ARM64EC bridge, display/graphics/input, first fresh prefix, and
real application launch remain separate milestones. Stable Portal and
approved boot animation are unaffected.

## Next v0.39 — verified full Wine26 archive, isolated PE/NLS data generation

**Source milestone verified:** [Charoite Wine source Actions run
41121328663](https://github.com/rgarn023/CharoitePortal/actions/runs/41121328663)
COMPLETED SUCCESS. The full coherent archive is artifact
`13009171257`, `Charoite-Wine-Coherent-Bootstrap-26-Experimental`.
The native source-built Wine10 loader and wineserver already passed
user device `--version` tests on the Galaxy S26 Ultra.

The new coherent archive contains **26 source-built components
(23 Windows PE, 3 native ELF)** and **76 Wine NLS** tables.
The source workflow independently verified all hashes, ARM64EC ABI,
the exact patched Wine source and per-PE import inventory. Observed PE
import gaps fell from **24 to 20**, but the import graph is not closed,
and Windows app execution is NOT READY.

**Important cohort isolation:** a rebuild of the same pinned Wine
source need not create binary-identical files. v0.39 deliberately
retains the full existing Wine22 APK archive, its native executable
probe libraries, the original 95-file staging slot and all on-device
data; it NEVER intermixes rebuilt Windows DLLs with previously verified
native Wine executables. The CI step `stage_wine26.py` verifies the
separately source-built 26-component archive, confirms original source
provenance matches the bundled Wine22 source, and bundles the full new
archive as an inert APK asset plus **99 individually SHA-256 verified
Windows module assets (23 PE + 76 NLS)**. It does not extract or install
the three native ELF files.

System → **Stage expanded Wine 26-module data** requires explicit
approval. It verifies the immutable complete new archive SHA-256,
checks all 99 per-module source paths/hashes and data sizes and copies
only the Windows PE/NLS files to a **new separate versioned staging
slot** under Next's private `getNoBackupFilesDir`. The old 0.4 slot
is never accessed, overwritten or deleted. Incomplete staging stays
quarantined; rechecks are read-only for already finalized slots.
No Windows PE execution, wineboot, new prefix, FEX, graphics or
anti-cheat support is implied.

The new user-actionable device test is this single opt-in staging
report. **Do not run Wineboot using these data files** until native
ELF/PE cohort compatibility and all required modules are independently
validated for the same generation in a future build. The stable
Charoite Portal and existing 7-second crystal energy boot are unchanged.

**CI fixture correction:** the first v0.39 build's fail-closed unit
allowlist correctly rejected a synthetic 26-component test fixture
that omitted the four named service DLLs. The fixture now includes
`bcrypt`, `msvcrt`, `sechost`, and `secur32`; the production
module allowlist and original Wine data are unchanged.


## Next v0.40 — Same-source Wine26 native loader and wineserver version-only probe

**Actual on-device evidence from user (Galaxy S26 Ultra):** v0.39
`CHAROITE NEXT — ISOLATED WINE26 PE/NLS STAGING` passed, with
**23/23 Windows PE** and **76/76 NLS** files hash-verified; complete
26-component source archive SHA-256 PASS; **20 observed unbundled PE
imports**, while the original Wine22 stage/loader, installed games,
saves, prefixes and rootfs were **not accessed**. No Wine26 native ELF
or Wineboot was executed. This is confirmed **data staging only**.

v0.40 adds a source-locked, separately APK-installed generation of
the **three native AArch64 ELF files** from the *same, independently
verified Wine26 26-component archive* (GitHub source run
[41121328663](https://github.com/rgarn023/CharoitePortal/actions/runs/41121328663),
artifact `13009171257`): loader, Unix ntdll and wineserver.
`stage_wine26_native.py` matches the verified full archive already
packaged as Wine26 inert data, checks all three SHA-256 hashes, Android
AArch64 ELF64 ET_DYN format, native dependencies and minimum 16KiB
load alignment, then packages them with **new names** under the
APK-owned native-library directory. It does **not** replace original
Wine22 native binaries or staging.

After explicit System → **Test matched Wine26 native startup** consent,
`CharoiteWine26NativeGate` runs the **read-only** 99-file Wine26
PE/NLS integrity check, verifies installed native loader, ntdll,
wineserver hashes against the same-source evidence, then executes
ONLY those exact APK-installed `wine --version` and
`wineserver --version`. Environment is sanitized, the timeout is
7 seconds per process, and exact Wine 10 version strings are required.
The prior successful Wine22 native probes remain separately available.

Wine26's native version gate **does not start a wineserver session,
wineboot, a Windows EXE, FEX, graphics, a Wine prefix, or games**.
**Do not infer launch readiness** if both native versions pass.
All 20 observed unbundled PE DLL import names and potential additional
native runtime dependencies remain work for later milestones.
Retain stable Charoite Portal, `com.charoitx` data and the user-approved
seven-second crystal boot art/audio.
