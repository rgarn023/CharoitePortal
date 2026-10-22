# Touhou Pocket Launcher - runtime preview attribution

Touhou Pocket Launcher is an experimental independent Android game launcher by Charoite Games.
The Windows runtime preview pulls the source at Git commit `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`
from [brunodev85/winlator-app](https://github.com/brunodev85/winlator-app) during GitHub Actions builds
and overlays the application label, launcher activity, provider authority, and application ID.

Winlator is © its respective copyright holders and is published under **LGPL-2.1**.
The original LICENSE is included under `app/src/main/assets/licenses/Winlator-LGPL-2.1.txt`.
The derivative overlay script and entry activity are retained publicly in this repository.
The runtime depends on additional separately licensed projects including Wine,
Box64, Mesa, DXVK, and libadrenotools. Applicable third-party notices are respected.
No proprietary Touhou game executables, translation data, or expansions are distributed.

**Scope:** An experimental fully integrated native Wine/Box64 runtime APK;
the separate native Kotlin launcher remains a file-import alpha. The runtime
preview opens a general-purpose Windows environment and does not auto-run TPDP or apply patches.

To rebuild, use GitHub Actions > Touhou Wine Runtime Preview. This is a source-based
build; do not distribute it as though original Winlator developer endorsed this fork.
