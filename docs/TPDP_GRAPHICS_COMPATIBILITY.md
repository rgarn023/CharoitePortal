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


## Device follow-up: DXVK + Turnip still black

In the user's second base-game test, \`gn_enbu.exe\` again displayed an all-black
client area while the title bar reported ~59.8 FPS and sound played. Launch
diagnostics confirmed \`DirectX wrapper: dxvk\`, \`Vulkan driver: turnip\`,
\`TPDP override: DXVK + TURNIP\`. **Therefore DXVK + Turnip is not a
confirmed workaround for this device/runtime.** The next reversible comparison
is System > TPDP Graphics > WINED3D + VIRGL. This changes only the next
TPDP launch, not the game files or existing Wine container graphics.

If WineD3D also remains black, investigate TPDP's Direct3D9 surface
initialization, graphics API diagnostics and the game's installed data before
claiming a fix. Audio and FPS in the window title are not evidence that the
game's image is being presented.

## Touch control layout (implemented, device verification pending)

TPDP's official manual documents arrow keys for movement and Z (confirm),
X (cancel/run), C (pose), S (sort), A/D (page L/R), and Space (Start).
Charoite's TPDP-specific Android touch overlay now appears on phone runs of
\`gn_enbu.exe\` or \`enbu_ap.exe\`. Separate, held touch buttons are sent through
the existing upstream XServer keyboard key-event handling, so holding X and a
direction can produce running rather than mouse emulation. It is hidden in
DeX desktop-window mode to preserve access to a physical keyboard/controller.

This is an input feature, not proof that the graphics surface is repaired.
No game file, Wine container or installed expansion is modified.

Official TPDP controls reference:
https://thpp.supersanctuary.net/tpdp/manual/
