#!/usr/bin/env python3
"""One bounded attempt to create a real WineAndroid GDI surface after native registration.

Galaxy v20 showed hwnd 0x2003e registered with Android but
replay_registered_android_surface() found a non-Android (dummy) Win32u
surface.  Re-run normal Wine window positioning/surface allocation once,
without moving, resizing, changing Z order, fabricating pixels, or touching
a user's Wine prefix. Applied ONLY after the v20 source patch in isolated CI.
"""
from pathlib import Path
import sys

OLD = """    if (surface->funcs != &android_surface_funcs)
    {
        TRACE( "Wine29 native replay HWND %p has no Android GDI surface\\n", hwnd );
        window_surface_release( surface );
        return;
    }"""

NEW = """    if (surface->funcs != &android_surface_funcs)
    {
        /* Native Android TextureView arrived while Win32u still owned its
         * dummy top-level surface. Re-enter Win32u's normal SetWindowPos
         * surface-creation path once (no movement, resize, activation,
         * Z-order change or synthetic Android pixels). */
        TRACE( "Wine29 v21 rearming real Android GDI surface for HWND %p\\n", hwnd );
        window_surface_release( surface );
        if (!NtUserSetWindowPos( hwnd, NULL, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                                 SWP_NOACTIVATE | SWP_FRAMECHANGED ))
        {
            WARN( "Wine29 v21 cannot rearm HWND %p window surface\\n", hwnd );
            return;
        }

        surface = window_surface_get( hwnd );
        if (!surface)
        {
            WARN( "Wine29 v21 surface still absent after rearm HWND %p\\n", hwnd );
            return;
        }
        if (surface->funcs != &android_surface_funcs)
        {
            WARN( "Wine29 v21 HWND %p still lacks Android GDI surface after rearm\\n", hwnd );
            window_surface_release( surface );
            return;
        }
        TRACE( "Wine29 v21 real Android GDI surface attached HWND %p\\n", hwnd );
        /* A new real DIB needs a real Win32 paint before its bitmap is
         * replayed. Existing dual GetPixel checks remain authoritative. */
        if (!NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW ))
            WARN( "Wine29 v21 failed to redraw rearmed HWND %p\\n", hwnd );
    }"""

def patch_source(source: str) -> str:
    if source.count(OLD) != 1:
        raise ValueError("Pinned v20 WineAndroid dummy-surface anchor mismatch")
    if "Wine29 v21 real Android GDI surface attached" in source:
        raise ValueError("v21 rearm already installed")
    if source.count("replay_registered_android_surface( hwnd );") != 1:
        raise ValueError("Expected exactly one native-refresh replay invocation")
    if "window_surface_flush( surface );" not in source:
        raise ValueError("Missing original real-bitmap flush path")
    return source.replace(OLD, NEW)

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: patch_android_surface_rearm.py PINNED_WINDOW_C", file=sys.stderr)
        return 2
    target = Path(argv[1])
    if not target.is_file() or target.is_symlink():
        print("Refusing missing or symlinked pinned WineAndroid source", file=sys.stderr)
        return 2
    original = target.read_text(encoding="utf-8")
    patched = patch_source(original)
    target.write_text(patched, encoding="utf-8")
    print("WINE29_V21_REAL_GDI_SURFACE_REARM=PATCHED (source-only)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
