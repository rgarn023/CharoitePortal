#!/usr/bin/env python3
"""Replay an existing Wine GDI window surface when Android registers it.

Applied only to a fresh, pinned Wine29 source checkout in provider CI,
AFTER the surface lock/post error gate and the visible-HWND redraw patch.
This never synthesizes pixels: it flushes the actual Wine window bitmap.
The strict Windows dual-pixel test and Android frame evidence are unchanged.
"""
from pathlib import Path
import sys

HANDLER = """            if (NtUserIsWindowVisible( hwnd ))
            {
                TRACE( "Android surface ready, invalidating HWND %p for GDI paint\\n", hwnd );
                if (!NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW ))
                    WARN( "Could not redraw newly registered Android HWND %p\\n", hwnd );
            }"""

HANDLER_REPLAY = """            if (NtUserIsWindowVisible( hwnd ))
            {
                TRACE( "Android surface ready, invalidating HWND %p for GDI paint\\n", hwnd );
                if (!NtUserRedrawWindow( hwnd, NULL, 0, RDW_INVALIDATE | RDW_UPDATENOW ))
                    WARN( "Could not redraw newly registered Android HWND %p\\n", hwnd );
                replay_registered_android_surface( hwnd );
            }"""

DISPATCH = "LRESULT ANDROID_WindowMessage( HWND hwnd, UINT msg, WPARAM wp, LPARAM lp )"

HELPER = """/* A real Android TextureView may be registered after GDI has already
 * painted into Wine's off-screen DIB.  Repainting the HWND alone doesn't
 * submit the existing pixels to Android if the dirty bounds were cleared
 * before the first native buffer existed.  On the one native refresh event,
 * mark only the existing Android-backed bitmap dirty and flush it once.
 * Never fabricate framebuffer colors or bypass the two GetPixel checks. */
static void replay_registered_android_surface( HWND hwnd )
{
    struct window_surface *surface = window_surface_get( hwnd );
    RECT full;

    if (!surface)
    {
        WARN( "Wine29 native replay missing HWND surface %p\\n", hwnd );
        return;
    }
    if (surface->funcs != &android_surface_funcs)
    {
        TRACE( "Wine29 native replay HWND %p has no Android GDI surface\\n", hwnd );
        window_surface_release( surface );
        return;
    }

    full = surface->rect;
    OffsetRect( &full, -full.left, -full.top );
    if (!IsRectEmpty( &full ))
    {
        window_surface_lock( surface );
        surface->bounds = full;
        window_surface_unlock( surface );
        TRACE( "Wine29 native replay flushing HWND %p bounds %s\\n",
               hwnd, wine_dbgstr_rect( &full ) );
        window_surface_flush( surface );
    }
    window_surface_release( surface );
}

"""

POST_ANCHOR = """        status = surface->window->perform( surface->window, NATIVE_WINDOW_UNLOCK_AND_POST );
        if (status)
        {
            WARN( "Unable to post Android surface for %p status %d\\n",
                  window_surface->hwnd, status );
            return FALSE;
        }"""

POST_TRACED = POST_ANCHOR + """
        TRACE( "Wine29 native GDI buffer posted HWND %p dirty %s size %dx%d\\n",
               window_surface->hwnd, wine_dbgstr_rect( dirty ), buffer.width, buffer.height );"""

def patch_source(source: str) -> str:
    for name, anchor in (
        ("visible HWND refresh after native registration", HANDLER),
        ("WM_ANDROID_REFRESH dispatch", DISPATCH),
        ("real buffer lock/post failure gate", POST_ANCHOR),
    ):
        if source.count(anchor) != 1:
            raise ValueError(f"Pinned WineAndroid {name} mismatch")
    if "replay_registered_android_surface" in source or "Wine29 native GDI buffer posted" in source:
        raise ValueError("Native replay patch already applied")
    source = source.replace(DISPATCH, HELPER + DISPATCH)
    source = source.replace(HANDLER, HANDLER_REPLAY)
    source = source.replace(POST_ANCHOR, POST_TRACED)
    return source

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: patch_android_surface_replay.py PINNED_WINDOW_C", file=sys.stderr)
        return 2
    file = Path(argv[1])
    if not file.is_file() or file.is_symlink():
        print("Refusing missing or symlinked WineAndroid source", file=sys.stderr)
        return 2
    source = file.read_text(encoding="utf-8")
    file.write_text(patch_source(source), encoding="utf-8")
    print("WINE29_ANDROID_EXISTING_GDI_BUFFER_REPLAY=PATCHED (source-only)")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
