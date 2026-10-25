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
  drawable to the Wine screen's available width **while maintaining its
  4:3 aspect ratio**. For a 720-wide portrait desktop, the original
  480x360 client is enlarged to about 720x540 (1.5x), not stretched.
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
