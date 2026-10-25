# TPDP handheld portrait layout — Charoite Core

Based on the user's October 25 sketch, Charoite Portal's TPDP
touch interface now resembles a dedicated handheld rather than two
separate clusters of keyboard shortcuts.

## Portrait arrangement

- Native TPDP game screen: centered in the *upper* part of the Wine
  desktop. Charoite moves the decorated frame without resizing its
  Direct3D9 client or changing the confirmed DXVK 1.10.3 + Turnip mode.
- Directly under the game: **Select** and **Start**, small center buttons.
- Next row: **L** to the left and **R** to the right.
- Bottom left: D-pad in a cross.
- Bottom right: **Y** top, **X** left, **A** right and **B** bottom.
  ABXY are circular, corresponding to conventional gamepad button labels.
- Top right: Hide Keys / Show Keys. Top left: More / Less, which toggles
  F11 fullscreen, Enter, Escape and P screenshot controls.

The buttons' placements and tap sizes respond to Android view size
changes, including portrait/landscape rotation. Multiple simultaneous
keys are supported for holding B-to-run while moving. All held keys
release when the overlay hides or loses window focus.

## Gamepad labels mapped to the original game keyboard

| On screen | Sent key |
|---|---|
| D-pad | Up/Down/Left/Right arrows |
| A | Z (confirm / interact) |
| B | X (cancel / run) |
| X | C |
| Y | S |
| L | A |
| R | D |
| Select | Left Shift |
| Start | Space |
| More: Fullscreen | F11 |
| More: Enter | Enter |
| More: Esc | Escape |
| More: Screenshot | P |

No original TPDP in-game key configuration is edited. This is a Core
screen overlay that supplies keyboard key presses to Winlator XServer.
DeX and external keyboard sessions continue using their hardware
inputs without this TPDP phone controller overlay. The native game
client remains unscaled to avoid disturbing known working graphics.

This layout is code-implemented and CI-tested, but must still be
visually verified on the physical Galaxy S26 Ultra, especially placement
relative to the Wine game frame and touch accessibility.
