# Touhou OS - runtime preview attribution

Touhou OS is an experimental Android Touhou game launcher by Charoite Games, adapted from an LGPL-licensed Winlator Android runtime.
The Windows runtime preview pulls the source at Git commit `8077f374ef2d54127b088de9e8cd7b4af14d9c8b`
from [brunodev85/winlator-app](https://github.com/brunodev85/winlator-app) during GitHub Actions builds
and overlays the application label, launcher activity, provider authority, and application ID.

Winlator is © its respective copyright holders and is published under **LGPL-2.1**.
The original LICENSE is included under `app/src/main/assets/licenses/Winlator-LGPL-2.1.txt`.
The derivative overlay script and entry activity are retained publicly in this repository.
The runtime depends on additional separately licensed projects including Wine,
Box64, Mesa, DXVK, and libadrenotools. Applicable third-party notices are respected.
No proprietary Touhou game executables, translation data, or expansions are distributed.

**Scope:** Touhou OS presents a game-library, import, and system interface over a source-derived Wine/Box64/Winlator runtime. Initial extraction of the bundled engine and creation of a private Windows container happen automatically when necessary; already-prepared installations are reused. The app does not distribute Touhou game files, expansions, or translation patches. The underlying Wine runtime remains Winlator-derived and is attributed here.

To rebuild, use GitHub Actions > Touhou Wine Runtime Preview. This is a source-based
build; do not distribute it as though original Winlator developer endorsed this fork.
