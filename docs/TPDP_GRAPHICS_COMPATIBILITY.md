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

## October 24: TPDP Direct3D diagnostics and VirGL readback comparison

Wine graphics warnings/errors previously disappeared from the report when a
game window opened successfully. The next build retains a bounded subset of
Direct3D errors, shaders, surfaces and driver warnings in Launch Diagnostics.
Both the Vulkan and OpenGL drivers are reported.

When **WineD3D + VirGL** is chosen for TPDP, the launch-only environment now
sets `VIRGL_NO_READBACK=false` and `MESA_NO_ERROR=0`. Pinned upstream VirGL
otherwise disables framebuffer readback. This is an **unverified compatibility
experiment**, not evidence that the black screen is resolved, and may be slower.
Non-TPDP launches are unchanged.

Implementation clarification: upstream `extractDXWrapperFiles()` does replace
Winlator-managed Wine Direct3D DLLs and wrapper cache when switching graphics
modes. The saved graphics selection is unaffected and a later Saved Settings
launch can restore the corresponding wrapper, but the operation is not strictly
read-only to Wine's system DLLs. Game data and saves are not intentionally
changed, and existing prefixes are never reset/deleted.

Device validation: launch base `gn_enbu.exe` in WineD3D + VirGL mode, check
for graphics and touch keys, and copy the new TPDP DIRECT3D / GRAPHICS OUTPUT
section from Launch Diagnostics if the screen is still black.

## October 24: black screen persists in WineD3D/VirGL

The user confirmed both previously tested renderers produce a black TPDP
game viewport on Galaxy S26 Ultra. The latest option is **WineD3D + Zink**,
a reversible TPDP-only comparison translating Direct3D9 through WineD3D,
OpenGL/Zink and Turnip Vulkan. It is **not yet a verified fix**.

Launch Diagnostics now reports the selected executable's adjacent file/media
counts, whether a TPDP `dat` directory exists, and mapped Wine X-window names,
classes and sizes. Silent installer exits record an error. These are diagnostics,
not an invasive DLL/game-file repair.

### Complete expansion installer folders

Selecting `SELECT INSTALLER .EXE` copies only the .exe. Some expansion
installers depend on adjacent .cab/.bin files, folders or setup media that
would be lost by this import path. The new **IMPORT COMPLETE INSTALLER
FOLDER** copies the entire source folder into a new private import directory,
selects the setup.exe/installer executable and presents **RUN INSTALLER** on
the Setup tab. **Folder imports never auto-run the installer.** No existing
installation, Wine prefix or save directory is reset.

If the expansion installer still fails, inspect the new LAUNCH PACKAGE and
MAPPED WINDOWS diagnostics. The installer might also depend on registration
data from the original base-game installation; do not infer it installed
successfully from a process or window alone.

References:
https://gist.github.com/RobertTheSable/6c4d705623b4de8d8cb3c954eac4814f
https://thpp.supersanctuary.net/tpdp/manual/ynk/

## October 24: portrait TPDP window and silent game session

New Galaxy screenshot shows the native TPDP touch buttons are present but
the game window's original Direct3D client is black, and sound has
disappeared. Frame counter at approximately 60 FPS is not proof of audio or
GPU frame presentation.

For phone TPDP game executables only, center the game's main Wine X11
window inside the virtual desktop, leaving its existing Direct3D client
width and height unchanged. Keep portrait game higher than the touch
controls. Reapply when X11 changes geometry. Do not reposition installers,
DeX applications or unrelated Windows programs. This is a presentation
change, **not a graphics black-screen solution**.

Add selected audio-backend reporting and a separate bounded filter for
Wine DirectSound/MMDevAPI/Pulse/ALSA messages, without changing backend
selection, game assets, registry or saves.

For the next device reproduction, launch `gn_enbu.exe` and copy the full
Last Launch Diagnostics report after returning to Portal. A missing
`dat` directory, Wine D3D warnings, or audio initialization messages
would indicate different root causes. Do not declare the game playable
until visible graphics **and** audible game audio are confirmed.

### TPDP's native fullscreen test on Android

The base TPDP manual documents **F11** as the native window/fullscreen
toggle. Charoite's TPDP-only phone controls now include a **F11 Full**
key at the top-left, opposite Hide Keys, so a hardware keyboard is not
required. The game's own display-mode switch is reversible by pressing
F11 again. It can distinguish a window-mode presentation issue from a
persistently black Direct3D surface, but is not asserted to cure rendering
or silence.

## October 25 device report — sound recovered, graphics black, horizontal centering not applied

The game is audible again. The visible F11 control and FPS title do not
indicate successful Direct3D frame presentation. Preserve the audio driver.

The previous XServer centering assumed direct root-window parentage and a
known WM_CLASS/WM_NAME at map time; Wine can assign those properties later
and wrap the client in decorated parents. The next version retries after
property/geometry updates, centers the decoration frame, and updates child
texture coordinate caches without touching the Wine installation.

Additional TPDP-only read-only diagnostics:
- mapped Wine window root X/Y coordinates and selected frame placement;
- number of XServer content updates versus surface updates (not proof
  of nonblack pixels);
- count and size of files immediately within the installed dat folder;
- Wine DLL loading events via scoped trace+loaddll to detect failed
  or missing Direct3D-related DLLs.

No additional driver roulette or audio configuration changes. The cause
of the black frame is still unverified; inspect the report from the
next physical-device launch before choosing a repair.

## 2026-10-25 — Native WineD3D Vulkan compatibility experiment

Device report for **WINED3D + VIRGL**: game data folder exists (286,592,608
direct bytes), XServer receives drawable updates, ALSA audio works, and
WineD3D reports OpenGL context/pbuffer warnings. These observations do not
prove the error is specifically caused by OpenGL, but establish a useful
alternative to compare. Previous DXVK+Turnip and WineD3D+VirGL screens
remained black.

Added **WINED3D VULKAN + VORTEK**, TPDP games only, via the existing
Winlator WineD3D configuration mechanism (per launch). It uses Vortek as
the actual Vulkan driver and GLADIO for the unused OpenGL slot. 
`renderer=vulkan` is passed in `WINE_D3D_CONFIG`, avoiding WGL/GLX
pbuffer creation if the driver works. Other WineD3D configuration values
and the game's selected audio backend are preserved. The choice remains
reversible with **TPDP GRAPHICS** (five choices), and other Windows
programs and installers are unaffected.

Wine upstream documentation: WINE_D3D_CONFIG accepts `renderer=vulkan`
without editing registry files. Note that Vulkan support may differ by Wine
release and device driver: this is **not confirmed playable** on the Galaxy.

For diagnostic clarity, the report now retains first distinct renderer
warnings separately from the last 75 matching output lines. High-frequency
esync/RPC messages should not conceal early D3D setup failures.

Device check: select WINED3D VULKAN + VORTEK in System, launch installed
`gn_enbu.exe`, look for title graphics with sound, then copy the new
graphics report, especially `FIRST DISTINCT DIRECT3D / GPU EVENTS`.
Do not reimport or reinstall TPDP or clear the existing Wine prefix.

## 2026-10-25: startup video and native Vulkan shader limitation

17.4-second Samsung recording `157333.mp4` shows the Portal launcher,
brief black game window, then the actual TPDP Japanese copyright notice,
animated character and `演舞準備中` loading graphic for several seconds.
The game area subsequently goes black, followed by Portal returning.
This disproves a blanket "never renders any game content" interpretation
but does not alone establish whether the process crashed or exited normally.

The log confirms WineD3D's native Vulkan mode was selected and emitted
`shader_spirv_update_float_vertex_constants Not implemented` and
`shader_spirv_update_float_pixel_constants Not implemented`. The corresponding
Wine SPIR-V backend functions are unimplemented. This mode can show some
startup assets but is not a dependable verified TPDP gameplay mode.

Next mode **WINED3D + ZINK STABILITY** (game executables only) uses WineD3D
OpenGL shaders through Zink/Turnip, sets `renderer=gl`, `csmt=0`,
`strict_shader_math=0`, `ZINK_CONTEXT_THREADED=0` and `MESA_NO_ERROR=0`.
Its OpenGL API can use mature shader constant functionality rather than
Wine's incomplete native Vulkan shader updater. This may trade performance
for compatibility and remains experimental pending device confirmation.
All previous modes, the saved ALSA audio driver, Wine prefix and installed
games/saves remain preserved.

Diagnostics now capture a bounded set of SEH / winedbg / unimplemented
warnings and Wine/Box64 guest launcher termination code and elapsed runtime.
A launcher return code alone does not prove the actual Windows game process
crashed. Report what is seen and avoid certainty before validation.

Code reference: https://fossies.org/linux/wine/dlls/wined3d/shader_spirv.c
