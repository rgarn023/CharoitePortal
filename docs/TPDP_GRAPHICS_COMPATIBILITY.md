# TPDP DirectX 9 black window with sound — Charoite Core workaround

Observed on Galaxy S26 Ultra: base Touhou Puppet Dance Performance 1.34
launches and reports approximately 60 FPS with audible sound, but its game
viewport is entirely black. The TPDP installer itself rendered Japanese
correctly after the Charoite Core v10 CP932/Shift-JIS correction. No
expansion is installed. Graphics compatibility is a distinct issue.

## Evidence and limitations

TPDP is a DirectX 9 game. A Winlator user independently reported that TPDP
stays black unless the DX wrapper is DXVK, with Turnip on Snapdragon GPUs
(https://ss1.xrea.com/poyogame.s322.xrea.com/play_tpdp/).

The upstream Winlator container default is DXVK with Turnip on supported
Adreno devices. Charoite's optional Compatibility Graphics uses
WineD3D/Vortek/VirGL instead. The saved graphics backend on the user's
actual container is not known from the screenshot. This is a targeted
hypothesis, not a verified fix until the game renders on the phone.

## Implemented in Core

A per-environment, per-TPDP-executable launch choice is available in System:

- DXVK + TURNIP (recommended first test; Touhou Realm default).
- WINED3D + VIRGL (reversible comparison).
- SAVED SETTINGS (no override).

Only gn_enbu.exe and enbu_ap.exe qualify. All other game and installer
launches retain the saved Wine container's graphics. Overrides occur in
XServerDisplayActivity before the Winlator driver / DirectX wrapper selection.
Nothing is written to the Wine container; no game assets or saves change.
When switching the runtime backend, only launch-local backend configurations
are cleared to avoid using incompatible previously saved wrapper options.

Diagnostics now include the resolved DirectX wrapper, selected Vulkan
graphics driver, and which TPDP override was requested — even when the
window appears but the screen remains black.

## Device acceptance test

1. Keep the existing installation and saved game. If progress exists,
   consider backing up save/gn_enbu.sav, without deleting anything.
2. Open Touhou Realm. Under System, select TPDP GRAPHICS: DXVK + TURNIP.
   Launch gn_enbu.exe, not setup.exe. Check for title graphics and menu.
3. If black persists, copy System -> View Last Launch Diagnostics,
   including GRAPHICS BACKEND. Compare WineD3D + VirGL and saved settings.
4. If all modes fail, investigate bundled DXVK d3d9 initialization,
   Wine/Adreno Vulkan driver support, texture and game-data loading, and
   graphics debug logs. Sound and title-bar FPS do not confirm actual
   presentation of pixels.

References:
https://thpp.supersanctuary.net/tpdp/manual/
https://ss1.xrea.com/poyogame.s322.xrea.com/play_tpdp/

Do not claim the black screen fixed without an on-device gameplay test.


## On-device follow-up: DXVK + Turnip also displays black

User confirmed that the TPDP 1.34 game window still shows a black
viewport even when launch diagnostics report DXVK + Turnip, with music
audible and the window title showing ~60 FPS. Consequently neither the
saved renderer nor DXVK+Turnip can be described as a verified fix.
Do not assume the presence of frame-rate text means the DirectX9
scene/textures are actually presenting. The existing reversible
WINED3D+VIRGL TPDP-only option is the next controlled comparison,
not a guaranteed solution. Collect a fresh graphics backend diagnostic
and screenshot for each test before introducing additional risky
Wine/driver changes.

## Dedicated on-screen TPDP keyboard

Charoite Portal now adds a TPDP-only XServer keyboard overlay to
gn_enbu.exe and enbu_ap.exe launches. An on-screen D-pad sends the game's
original Up/Down/Left/Right keys; Z confirms, X cancels and runs while
held, S opens menu, C opens the pose/display function, A and D switch
menu pages, and Space, Left Shift, Enter and Esc are also available.
Buttons use true X key-down on press and key-up on release/cancellation
and release all held keys when focus changes. HIDE KEYS / SHOW KEYS
toggles overlay visibility without changing any user input profile
or saved game data. Other game binaries and setup.exe do not receive
this overlay; physical keyboards and Winlator input profiles still work.

Source: TPDP official controls manual
https://thpp.supersanctuary.net/tpdp/manual/
