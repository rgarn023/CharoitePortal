#!/usr/bin/env python3
"""Force Wine's normal *visible* GDI allocation gate on Android refresh.

v22 Galaxy: Java SurfaceTexture/Android native window registered, but
the real Android GDI driver was still absent after the v21 frame-change
attempt and v22 scaled-target check. In pinned Win32u window.c,
SWP_SHOWWINDOW explicitly sets needs_surface=TRUE for a top-level
non-OpenGL window. Use this flag only for an HWND already visible,
without moving, resizing, Z-order/activation changes, or fake pixels.

Bounded diagnosis records whether Win32u attempts native surface creation,
and whether the WineAndroid driver is called. All paths preserve the strict
Win32 dual GetPixel and Android frame evidence gates.
"""
from pathlib import Path
import sys

REARM_ANCHOR = """        TRACE( "Wine29 v21 rearming real Android GDI surface for HWND %p\\n", hwnd );
        window_surface_release( surface );
        if (!NtUserSetWindowPos( hwnd, NULL, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                                 SWP_NOACTIVATE | SWP_FRAMECHANGED ))"""

REARM_NEW = """        /* Request native Win32u GDI allocation on a known-visible HWND.
         * Unlike FRAMECHANGED alone, SHOWWINDOW explicitly sets
         * needs_surface in get_window_surface(). This is safe only when
         * the HWND was already visible. The original one-shot path and
         * its real-driver validation remain authoritative. */
        if (!NtUserIsWindowVisible( hwnd ))
        {
            WARN( "Wine29 v23 refusing hidden HWND %p surface recreation\\n", hwnd );
            window_surface_release( surface );
            return;
        }
        TRACE( "Wine29 v23 requesting native GDI surface creation for visible HWND %p\\n", hwnd );
        TRACE( "Wine29 v21 rearming real Android GDI surface for HWND %p\\n", hwnd );
        window_surface_release( surface );
        if (!NtUserSetWindowPos( hwnd, NULL, 0, 0, 0, 0,
                                 SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER |
                                 SWP_NOACTIVATE | SWP_FRAMECHANGED | SWP_SHOWWINDOW ))"""

WIN32U_ANCHOR = """    if (is_opengl && !is_layered && !create_layered
        && !(!create_opaque && NtUserGetLayeredWindowAttributes( hwnd, NULL, NULL, &layered_flags ) && layered_flags & LWA_COLORKEY))
    {
        if (new_surface) window_surface_release( new_surface );
        new_surface = NULL;
    }
    else if (needs_surface)
        create_window_surface( hwnd, create_layered, surface_rect, raw_dpi_num, raw_dpi_den, &new_surface );"""

WIN32U_NEW = """    if (swp_flags & SWP_SHOWWINDOW)
        TRACE( "Wine29 v23 Win32u GDI allocation gate hwnd %p flags %#x style %#x child %u opengl %u needs_surface %u rect %s\\n",
               hwnd, swp_flags, style, is_child, is_opengl, needs_surface,
               wine_dbgstr_rect( surface_rect ) );
    if (is_opengl && !is_layered && !create_layered
        && !(!create_opaque && NtUserGetLayeredWindowAttributes( hwnd, NULL, NULL, &layered_flags ) && layered_flags & LWA_COLORKEY))
    {
        if (new_surface) window_surface_release( new_surface );
        new_surface = NULL;
    }
    else if (needs_surface)
    {
        if (swp_flags & SWP_SHOWWINDOW)
            TRACE( "Wine29 v23 Win32u calling native CreateWindowSurface HWND %p\\n", hwnd );
        create_window_surface( hwnd, create_layered, surface_rect, raw_dpi_num, raw_dpi_den, &new_surface );
    }"""

ANDROID_ANCHOR = """    TRACE( "hwnd %p, layered %u, surface_rect %s, surface %p\\n", hwnd, layered, wine_dbgstr_rect( surface_rect ), surface );

    if ((previous = *surface) && previous->funcs == &android_surface_funcs) return TRUE;
    if (!(data = get_win_data( hwnd ))) return TRUE; /* use default surface */
    if (previous) window_surface_release( previous );

    *surface = create_surface( data->hwnd, surface_rect );

    release_win_data( data );
    return TRUE;"""

ANDROID_NEW = """    TRACE( "hwnd %p, layered %u, surface_rect %s, surface %p\\n", hwnd, layered, wine_dbgstr_rect( surface_rect ), surface );
    TRACE( "Wine29 v23 native Android CreateWindowSurface request HWND %p rect %s\\n",
           hwnd, wine_dbgstr_rect( surface_rect ) );

    if ((previous = *surface) && previous->funcs == &android_surface_funcs)
    {
        TRACE( "Wine29 v23 reusing existing genuine Android GDI surface HWND %p\\n", hwnd );
        return TRUE;
    }
    if (!(data = get_win_data( hwnd )))
    {
        WARN( "Wine29 v23 Android window data missing for GDI HWND %p\\n", hwnd );
        return TRUE; /* retain original fail-closed default behavior */
    }
    if (previous) window_surface_release( previous );

    *surface = create_surface( data->hwnd, surface_rect );
    if (*surface)
        TRACE( "Wine29 v23 created real Android GDI surface HWND %p\\n", hwnd );
    else
        WARN( "Wine29 v23 Android GDI DIB allocation failed HWND %p\\n", hwnd );

    release_win_data( data );
    return TRUE;"""

def patch_sources(android: str, win32u: str) -> tuple[str, str]:
    for label, src, old in (
        ("visible-only native rearm", android, REARM_ANCHOR),
        ("native Android surface allocation", android, ANDROID_ANCHOR),
        ("Win32u GDI allocation gate", win32u, WIN32U_ANCHOR),
    ):
        if src.count(old) != 1:
            raise ValueError(f"Exact pinned Wine29 v23 anchor mismatch: {label}")
    if "Wine29 v23" in android or "Wine29 v23" in win32u:
        raise ValueError("v23 patch already applied")
    if "wine29_has_android_surface_target( hwnd, surface )" not in android:
        raise ValueError("Missing mandatory v22 real Android backend gate")
    if android.count("window_surface_flush( surface );") != 1:
        raise ValueError("Missing unique real GDI bitmap flush")
    new_android = android.replace(REARM_ANCHOR, REARM_NEW).replace(ANDROID_ANCHOR, ANDROID_NEW)
    new_win32u = win32u.replace(WIN32U_ANCHOR, WIN32U_NEW)
    return new_android, new_win32u


def main(args: list[str]) -> int:
    if len(args) != 3:
        print("Usage: patch_android_visible_surface_create.py WINDOW_C WIN32U_WINDOW_C", file=sys.stderr)
        return 2
    paths = [Path(x) for x in args[1:]]
    if any(not p.is_file() or p.is_symlink() for p in paths):
        print("Refusing missing or symlinked pinned Wine source files", file=sys.stderr)
        return 2
    updated = patch_sources(*(p.read_text(encoding="utf-8") for p in paths))
    for path, new_content in zip(paths, updated):
        path.write_text(new_content, encoding="utf-8")
    print("WINE29_V23_VISIBLE_SURFACE_CREATION=PATCHED (source-only)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
