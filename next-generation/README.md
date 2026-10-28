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

## Device validation roadmap

1. Install Next **alongside** stable Portal; confirm both icons/apps and each edition's private data are independent.
2. Validate Next legacy engine and native graphics/input on Galaxy S26 Ultra. CI does not replace device testing.
3. Assemble an attributable source-built and hash-verified Charoite Wine ARM64EC runner, FEX bridges, Vulkan drivers and renderer DLLs.
4. Stage assets atomically in a NEW Next runtime directory, create a NEW dedicated Windows prefix, perform Windows program tests and rollback.
5. Test Battle.net launcher/login and Steam client separately, then game installs and DirectX 9/11/12 compatibility. Add game-specific profiles only after evidence.
6. Honor publisher support for anti-cheat. No bypasses, stealth, kernel-driver impersonation or universal game compatibility claims.

**Downloads:** Open the linked GitHub Actions run, expand **Artifacts**, and select `Charoite-Core-Next-Android-APK`. Unzip, then install the contained APK. Do not uninstall the existing Portal.

**Stable Portal:** [last verified stable APK run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611), package `com.charoite`. Unchanged.
