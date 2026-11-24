#!/usr/bin/env python3
"""Permit one real native GDI allocation for a visible HWND stuck on dummy_surface.

Pinned Wine29 Win32u fixup_swp_flags() drops SWP_SHOWWINDOW whenever WS_VISIBLE
is already set. Consequently v23's visible-only rearm never reaches the
SWP_SHOWWINDOW-triggered native CreateWindowSurface path. Keep that flag
only when the caller requests the exact no-geometry/no-Z-order rearm pattern
AND the top-level HWND still has Win32u's actual dummy_surface.

This is not generic SHOWWINDOW behavior and never manufactures GDI pixels,
Android frames, a successful GetPixel reading, or a test exit status.
Runs solely on a fresh, source-pinned Wine provider checkout.
"""
from pathlib import Path
import sys

ANCHOR = """    if (win->dwStyle & WS_VISIBLE) winpos->flags &= ~SWP_SHOWWINDOW;
    else
    {
        winpos->flags &= ~SWP_HIDEWINDOW;"""

NEW = """    if (win->dwStyle & WS_VISIBLE)
    {
        /* v23's one-shot Android native rearm requests SWP_SHOWWINDOW
         * only to pass Win32u's real CreateWindowSurface gate. Wine
         * normally strips it on an already visible HWND; preserve it
         * ONLY when this exact no-move/no-size/no-Z-order/no-activate
         * request targets a top-level HWND still on the dummy surface.
         * No window style, geometry or activation is changed. */
        const UINT rearm = SWP_SHOWWINDOW | SWP_FRAMECHANGED |
                           SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                           SWP_NOACTIVATE;
        if ((winpos->flags & rearm) == rearm &&
            !(win->dwStyle & WS_CHILD) &&
            win->surface == &dummy_surface)
        {
            TRACE( "Wine29 v24 preserving SHOWWINDOW for dummy GDI HWND %p\\n",
                   winpos->hwnd );
        }
        else winpos->flags &= ~SWP_SHOWWINDOW;
    }
    else
    {
        winpos->flags &= ~SWP_HIDEWINDOW;"""

def patch_source(source: str) -> str:
    if source.count(ANCHOR) != 1:
        raise ValueError("Pinned visible-window SWP fixup anchor mismatch")
    for required in (
        "static BOOL fixup_swp_flags( WINDOWPOS *winpos",
        "surface = get_window_surface( winpos->hwnd, winpos->flags, FALSE,",
        "Wine29 v23 Win32u calling native CreateWindowSurface",
        "if (swp_flags & SWP_SHOWWINDOW) needs_surface = TRUE;",
    ):
        if required not in source:
            raise ValueError(f"Required pinned Wine29 native surface gate missing: {required}")
    if "Wine29 v24 preserving SHOWWINDOW" in source:
        raise ValueError("v24 fix already installed")
    return source.replace(ANCHOR, NEW)

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: patch_android_visible_dummy_swp_gate.py PINNED_WIN32U_WINDOW_C",
              file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file() or path.is_symlink():
        print("Refusing absent or symlinked source file", file=sys.stderr)
        return 2
    old = path.read_text(encoding="utf-8")
    new = patch_source(old)
    path.write_text(new, encoding="utf-8")
    print("WINE29_V24_VISIBLE_DUMMY_GDI_ALLOCATION=PATCHED source-only")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
