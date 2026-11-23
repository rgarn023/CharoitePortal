#!/usr/bin/env python3
"""Expose the actual Win32u driver target beneath a DPI-scaled surface.

Galaxy v21 registered an Android native window, yet replay rejected its
outer Win32u surface. Pinned Wine's dce.c may wrap a real Android driver
surface in a scaled_surface whose funcs differ from android_surface_funcs.
Only a real Android-backed target may pass: dummy and offscreen surfaces
are rejected. This patch never makes a synthetic Android frame or pixel.
Applies to fresh source in provider CI, never installed app data.
"""
from pathlib import Path
import sys

HEADER_ANCHOR = "W32KAPI struct window_surface *window_surface_get( HWND hwnd );"

DCE_ANCHOR = """W32KAPI struct window_surface *window_surface_get( HWND hwnd )
{
    struct window_surface *surface = NULL;
    WND *win = get_win_ptr( hwnd );

    if (win && win != WND_DESKTOP && win != WND_OTHER_PROCESS)
    {
        if ((surface = win->surface))
            window_surface_add_ref( surface );
        release_win_ptr( win );
    }
    return surface;
}"""

DCE_TARGET = DCE_ANCHOR + """

/* Return an independently referenced driver target, never an unowned
 * scaled_surface pointer. The caller must release the returned surface.
 * The original window_surface_get() remains unchanged for all consumers.
 * In particular, painting and flushing still use the scaling wrapper. */
W32KAPI struct window_surface *window_surface_get_driver( HWND hwnd )
{
    struct window_surface *surface = window_surface_get( hwnd );

    if (surface && surface->funcs == &scaled_surface_funcs)
    {
        struct window_surface *target = get_scaled_surface( surface )->target_surface;
        if (target) window_surface_add_ref( target );
        window_surface_release( surface );
        return target;
    }
    return surface;
}"""

REPLAY_ANCHOR = "static void replay_registered_android_surface( HWND hwnd )"

REPLAY_HELPER = """/* The HWND may own a Wine DPI-scaled DIB whose underlying target is
 * the real Android driver surface. Do not confuse the two callback tables.
 * This check does not flush a dummy/offscreen backend as proof of Android. */
static BOOL wine29_has_android_surface_target( HWND hwnd, struct window_surface *surface )
{
    struct window_surface *target = window_surface_get_driver( hwnd );
    BOOL valid = target && target->funcs == &android_surface_funcs;

    if (valid && target != surface)
        TRACE( "Wine29 v22 real Android driver behind Win32u scaled surface HWND %p\\n", hwnd );
    if (target) window_surface_release( target );
    return valid;
}

""" + REPLAY_ANCHOR

GUARD = "if (surface->funcs != &android_surface_funcs)"
GUARD_REPLACEMENT = "if (!wine29_has_android_surface_target( hwnd, surface ))"


def patch_sources(window: str, dce: str, header: str) -> tuple[str, str, str]:
    if header.count(HEADER_ANCHOR) != 1 or "window_surface_get_driver" in header:
        raise ValueError("Pinned public Wine GDI window-surface declaration mismatch")
    if dce.count(DCE_ANCHOR) != 1 or "window_surface_get_driver" in dce:
        raise ValueError("Pinned native Win32u driver-surface access mismatch")
    for native in ("struct scaled_surface", "scaled_surface_funcs",
                   "target_surface", "get_scaled_surface( struct window_surface"):
        if native not in dce:
            raise ValueError(f"Pinned Win32u DPI scaled target missing: {native}")
    if window.count(REPLAY_ANCHOR) != 1 or window.count(GUARD) != 2:
        raise ValueError("Expected exactly the v21 real surface and rearm checks")
    if "window_surface_get_driver" in window or "Wine29 v22" in window:
        raise ValueError("Scaled-target patch already installed")
    if "window_surface_flush( surface );" not in window:
        raise ValueError("Pinned real Wine surface flush is missing")
    return (
        window.replace(REPLAY_ANCHOR, REPLAY_HELPER).replace(GUARD, GUARD_REPLACEMENT),
        dce.replace(DCE_ANCHOR, DCE_TARGET),
        header.replace(HEADER_ANCHOR, HEADER_ANCHOR +
                       "\nW32KAPI struct window_surface *window_surface_get_driver( HWND hwnd );"),
    )


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print("Usage: patch_android_scaled_surface_target.py WINDOW_C DCE_C GDI_DRIVER_H",
              file=sys.stderr)
        return 2
    paths = [Path(x) for x in argv[1:]]
    if any(not p.is_file() or p.is_symlink() for p in paths):
        print("Refusing missing or symlinked pinned source file", file=sys.stderr)
        return 2
    originals = [p.read_text(encoding="utf-8") for p in paths]
    patched = patch_sources(*originals)
    for path, new in zip(paths, patched):
        path.write_text(new, encoding="utf-8")
    print("WINE29_V22_SCALED_ANDROID_DRIVER_SURFACE=PATCHED (source-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
