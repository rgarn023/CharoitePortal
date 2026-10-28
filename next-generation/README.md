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

[**GitHub Actions run 40721844963**](https://github.com/rgarn023/CharoitePortal/actions/runs/40721844963) successfully built source-validated Wine 10.0 components from our maintained patches. **All 4 CI jobs passed**, including an Android ARM64 `wineserver` with 16 KiB ELF alignment and a **Windows ARM64EC `ntdll.dll` (machine 0xA641)** paired with an **Android AArch64 `ntdll.so` (16 KiB aligned)**. Experimental binary artifacts: `Charoite-Wine-ARM64EC-NTDLL-Experimental` (ID **12831021769**) and `Charoite-Wine-Android-ARM64-Experimental` (ID **12829954961**).

**These are individual binaries, not a functioning full runner or a new APK.** They have not been added to the Charoite Next installation or tested on the Galaxy S26 Ultra. The Next APK still runs its isolated **legacy Wine/Box64** engine and explicitly marks the modern ARM64EC/FEX engine **NOT READY**. A complete Wine runtime, FEX, graphics dependencies, isolated prefix and device validation are still required before Battle.net/Steam testing. See [Charoite Wine source/build details](charoite-wine/README.md) and the [GitHub handoff](../docs/CURRENT_HANDOFF.md).

## Device validation roadmap

1. Install Next **alongside** stable Portal; confirm both icons/apps and each edition's private data are independent.
2. Validate Next legacy engine and native graphics/input on Galaxy S26 Ultra. CI does not replace device testing.
3. Assemble an attributable source-built and hash-verified Charoite Wine ARM64EC runner, FEX bridges, Vulkan drivers and renderer DLLs.
4. Stage assets atomically in a NEW Next runtime directory, create a NEW dedicated Windows prefix, perform Windows program tests and rollback.
5. Test Battle.net launcher/login and Steam client separately, then game installs and DirectX 9/11/12 compatibility. Add game-specific profiles only after evidence.
6. Honor publisher support for anti-cheat. No bypasses, stealth, kernel-driver impersonation or universal game compatibility claims.

**Downloads:** Open the linked GitHub Actions run, expand **Artifacts**, and select `Charoite-Core-Next-Android-APK`. Unzip, then install the contained APK. Do not uninstall the existing Portal.

**Stable Portal:** [last verified stable APK run 40641148611](https://github.com/rgarn023/CharoitePortal/actions/runs/40641148611), package `com.charoite`. Unchanged.
