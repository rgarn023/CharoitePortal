#!/usr/bin/env python3
"""Refresh Wine GDI paint only after a real Android native surface is registered.

WineAndroid's WM_ANDROID_REFRESH currently exposes an existing CPU window
surface, but that does not guarantee a first WM_PAINT if its native buffer
was missing when Wine initially drew. Re-invalidate the *real HWND* on this
one native-surface refresh message, preserving all Win32 rendering gates.
Applied only in a fresh, source-pinned provider CI build.
"""
from pathlib import Path
import sys

ANCHOR = """    case WM_ANDROID_REFRESH:
        if (wp)  /* opengl client window */
        {
            update_gl_drawable( hwnd );
        }
        else
        {
            NtUserExposeWindowSurface( hwnd, 0, NULL, 0 );
        }
        return 0;"""

REPLACEMENT = """    case WM_ANDROID_REFRESH:
        if (wp)  /* opengl client window */
        {
            update_gl_drawable( hwnd );
        }
        else
        {
            /* The Java TextureView can arrive *after* the first GDI paint.
             * Exposing old bits alone cannot create a new invalidation.
             * Request a real client paint once the native window has been
             * registered and the target HWND is actually visible.
             * No synthetic pixels, Android-side drawing, or repeated timer. */
            NtUserExposeWindowSurface( hwnd, 0, NULL, 0 );
            if (NtUserIsWindowVisible( hwnd ))
            {
                TRACE( "Android surface ready, invalidating HWND %p for GDI paint\\n", hwnd );
                if (!NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW ))
                    WARN( "Could not redraw newly registered Android HWND %p\\n", hwnd );
            }
        }
        return 0;"""


def patch_source(source: str) -> str:
    if source.count(ANCHOR) != 1:
        raise ValueError("Pinned WineAndroid WM_ANDROID_REFRESH handler not unique")
    if source.count("    case WM_ANDROID_REFRESH:") != 1:
        raise ValueError("Unexpected second Android refresh handler")
    if "NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW )" in source:
        raise ValueError("Native repaint already applied")
    return source.replace(ANCHOR, REPLACEMENT)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: patch_android_refresh_redraw.py PINNED_WINDOW_C", file=sys.stderr)
        return 2
    target = Path(argv[1])
    if not target.is_file() or target.is_symlink():
        print("Refusing missing or symlinked pinned source", file=sys.stderr)
        return 2
    source = target.read_text(encoding="utf-8")
    target.write_text(patch_source(source), encoding="utf-8")
    print("WINE29_ANDROID_SURFACE_REFRESH_GDI_REDRAW=PATCHED source-only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
