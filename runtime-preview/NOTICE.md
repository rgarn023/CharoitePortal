# Charoite Portal - runtime preview attribution

Charoite Portal is an experimental Android Windows-game environment manager with Touhou Realm as a bundled profile by Charoite Games, adapted from an LGPL-licensed Winlator Android runtime.
The Windows runtime preview pulls the source at Git commit `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`
from [brunodev85/winlator-app](https://github.com/brunodev85/winlator-app) during GitHub Actions builds
and overlays the application label, launcher activity, provider authority, and application ID.

Winlator is © its respective copyright holders and is published under **LGPL-2.1**.
The original LICENSE is included under `app/src/main/assets/licenses/Winlator-LGPL-2.1.txt`.
The derivative overlay script, entry activity, and Charoite Core source module are retained publicly in this repository.
The runtime depends on additional separately licensed projects including Wine,
Box64, Mesa, DXVK, and libadrenotools. Applicable third-party notices are respected.
No proprietary Touhou game executables, translation data, or expansions are distributed.

**Scope:** Charoite Portal presents a game-library, import, and system interface over a source-derived Wine/Box64/Winlator runtime. Initial extraction of the bundled engine and creation of a private Windows container happen automatically when necessary; already-prepared installations are reused. The app does not distribute Touhou game files, expansions, or translation patches. The underlying Wine runtime remains Winlator-derived and is attributed here.

To rebuild, use GitHub Actions > Touhou Wine Runtime Preview. This is a source-based
build; do not distribute it as though original Winlator developer endorsed this fork.

**Charoite Core:** A Charoite Games runtime-coordination source module packaged within the same Android application; it is not an independently developed Wine/Box64 implementation and does not replace Android. It calls the pinned Winlator-derived engine and preserves the engine's copyright and license obligations.

Charoite Core v0.3 is an app-level environment manager, display/graphics/wallpaper policy and UI library, not a standalone OS or an independently written Wine, Box64 or GPU driver. Its environmental presets and original wallpapers do not include proprietary games. The new clean-install APK uses the Charoite-specific Android package ID com.charoite. It does not access or migrate the historical com.touhoudr private app data, which is removed when that older app is uninstalled. This fixed-length ID is necessary to preserve the pinned native Wine/Box64 ELF absolute-path layout.
