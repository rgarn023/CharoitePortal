# TPDP upper-screen enlargement (Charoite Core)

The user clarified that TPDP's Windows game content remains visually
too small **even when the window is maximized**. Moving the native
488x387 decorated frame to the top of the Wine desktop does not enlarge
its image. The existing Charoite Core layout only repositioned it.

## Implementation

- Keep the working DXVK 1.10.3 + Turnip compatibility profile and the
  native TPDP game rendering resolution unchanged.
- In TPDP phone sessions only, enable Winlator's existing
  `GLRenderer.setForceWindowsFullscreen(true)`.
- Its built-in `FullscreenTransformation` fits the undecorated game
  drawable to the Wine screen while retaining the original aspect ratio.
- October 25 device screenshot showed the full-width 720x540 result was
  **too large** and the title/frame was visually clipped.
- `CharoiteWindowPolicy.placeScaledGame` now reduces that fullscreen
  transformation to **86%** in portrait, yielding approximately **619x464**
  from the 480x360 game at a 720px-wide desktop (about 1.29x original).
  The picture is horizontally centered with approximately 50px side
  margins. Width and height are multiplied equally to avoid distortion.
- Both the actual game drawable and any decorated parent transformation
  use the same percentage, avoiding a full-size frame over a smaller image.
- `CharoiteWindowPolicy.placeScaledGame` (Core) relocates that enlarged
  compositor representation into the upper half of the portrait desktop,
  above Select / Start / shoulder buttons. Portrait positioning is
  responsive to the configured screen height; landscape retains normal
  centered presentation.
- The same built-in fullscreen transformation maps pointer input back
  to the real unscaled Windows coordinates in Winlator InputDeviceManager.
  D-pad and A/B/X/Y keys remain identical.
- DeX, installers and non-TPDP executables keep their original display.
  Existing app data, Wine prefixes, game folders, saves, audio configuration
  and renderer DLL settings are untouched.

This is **real enlargement of the displayed game content**, not larger
buttons and not only a different window position. The Android build
checks the integration; actual screen appearance must be verified on
the Galaxy device.

## Follow-up: game image appears outside its Windows frame

The device screenshot after 86% portrait scaling shows that TPDP's picture
and its Wine title/border do not line up consistently. The pinned Winlator
renderer computes a separate fullscreen transformation for the game client
and its decorated parent. Both were scaled to 86%, but the parent's 488x387
aspect ratio differs from the actual 480x360 game client. Independently
centering those transforms therefore offsets the picture and border.

The repair in Charoite Core `CharoiteWindowPolicy.alignWindowFrame`
derives the parent frame's position and dimensions directly from the
already-sized client transform. Both now use the *same* pixel scaling,
taking the original border offsets from their X11 root coordinates.
Scaled TPDP sessions no longer also move the original X11 parent geometry:
that earlier center-window policy was adding a second independent offset.

This only affects presentation of TPDP's phone game view. The proven
DXVK 1.10.3 + Turnip renderer, the 86%-width image, game data, audio,
controls and saves remain untouched. Confirm border alignment on phone;
GitHub CI can verify compilation but not Android device rendering.
