#!/usr/bin/env python3
"""Publish genuine Java desktop metrics even when Explorer has no visible tray."""
from pathlib import Path
import sys

ANCHOR = """    if (!hwnd || !NtUserIsWindowVisible( hwnd )) return;
    if (!NtUserGetWindowRect( hwnd, &rect, NtUserGetWinMonitorDpi( hwnd, MDT_RAW_DPI ) )) return;
    if (rect.top) monitor_rc_work.bottom = rect.top;
    else monitor_rc_work.top = rect.bottom;
    TRACE( "found tray %p %s work area %s\\n", hwnd,
           wine_dbgstr_rect( &rect ), wine_dbgstr_rect( &monitor_rc_work ));

    /* if we're notified from Java thread, update registry */
    if (*p_java_vm) NtUserCallNoParam( NtUserCallNoParam_DisplayModeChanged );"""

NEW = """    /* A shell tray is optional. Its absence must not suppress the
     * initial Java desktop display-mode publication. */
    if (hwnd && NtUserIsWindowVisible( hwnd ) &&
        NtUserGetWindowRect( hwnd, &rect, NtUserGetWinMonitorDpi( hwnd, MDT_RAW_DPI ) ))
    {
        if (rect.top) monitor_rc_work.bottom = rect.top;
        else monitor_rc_work.top = rect.bottom;
        TRACE( "found tray %p %s work area %s\\n", hwnd,
               wine_dbgstr_rect( &rect ), wine_dbgstr_rect( &monitor_rc_work ));
    }

    /* Only publish real positive dimensions supplied by the Java host.
     * Use the existing mode-change path; do not manufacture a monitor,
     * bypass GDI allocation, or alter the Windows pixel/frame gates. */
    if (*p_java_vm && width > 0 && height > 0)
    {
        TRACE( "Wine29 v25 publishing Android display mode %dx%d\\n", width, height );
        NtUserCallNoParam( NtUserCallNoParam_DisplayModeChanged );
    }"""

def patch_source(source: str) -> str:
    if source.count(ANCHOR) != 1 or "Wine29 v25 publishing" in source:
        raise ValueError("Pinned Android monitor-publication anchor mismatch")
    for required in ("void init_monitors( int width, int height )",
                     "virtual_screen_rect.right = width;",
                     "virtual_screen_rect.bottom = height;",
                     "monitor_rc_work = virtual_screen_rect;",
                     "UINT ANDROID_UpdateDisplayDevices("):
        if required not in source:
            raise ValueError(f"Missing pinned monitor path: {required}")
    return source.replace(ANCHOR, NEW)

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        return 2
    path = Path(argv[1])
    if not path.is_file() or path.is_symlink():
        return 2
    source = patch_source(path.read_text(encoding="utf-8"))
    path.write_text(source, encoding="utf-8")
    print("WINE29_V25_ANDROID_MONITOR_PUBLISH=PATCHED source-only")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
