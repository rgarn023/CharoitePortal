#!/usr/bin/env python3
"""Fail closed on WineAndroid CPU surface lock/post failures.

Applies only to the pinned Wine29 source in a fresh provider CI checkout.
No Android, Wine process, installed prefix, game, or local runtime is accessed.
"""
from pathlib import Path
import sys


def patch_source(source: str) -> str:
    signature = (
        "static BOOL android_surface_flush( struct window_surface *window_surface, "
        "const RECT *rect, const RECT *dirty,"
    )
    declaration = "    ANativeWindow_Buffer buffer;\n    ARect rc;"
    lock = (
        "    if (!surface->window->perform( surface->window, NATIVE_WINDOW_LOCK, "
        "&buffer, &rc ))"
    )
    post = (
        "        surface->window->perform( surface->window, "
        "NATIVE_WINDOW_UNLOCK_AND_POST );"
    )
    failed = (
        '    else TRACE( "Unable to lock surface %p window %p buffer %p\\n",\n'
        "                surface, window_surface->hwnd, surface->window );"
    )
    for name, anchor in (
        ("flush signature", signature),
        ("flush locals", declaration),
        ("native lock", lock),
        ("native post", post),
        ("lock failure", failed),
    ):
        if source.count(anchor) != 1:
            raise ValueError(f"Unexpected pinned WineAndroid {name} (expected once)")

    source = source.replace(declaration, declaration + "\n    int status;")
    source = source.replace(
        lock,
        '    if (!surface->window)\n'
        '    {\n'
        '        WARN( "Missing native Android window for %p\\n", window_surface->hwnd );\n'
        '        return FALSE;\n'
        '    }\n'
        '    status = surface->window->perform( surface->window, NATIVE_WINDOW_LOCK, &buffer, &rc );\n'
        '    if (!status)',
    )
    source = source.replace(
        post,
        '        status = surface->window->perform( surface->window, NATIVE_WINDOW_UNLOCK_AND_POST );\n'
        '        if (status)\n'
        '        {\n'
        '            WARN( "Unable to post Android surface for %p status %d\\n",\n'
        '                  window_surface->hwnd, status );\n'
        '            return FALSE;\n'
        '        }',
    )
    source = source.replace(
        failed,
        '    else\n'
        '    {\n'
        '        WARN( "Unable to lock Android surface %p window %p buffer %p status %d\\n",\n'
        '              surface, window_surface->hwnd, surface->window, status );\n'
        '        return FALSE;\n'
        '    }',
    )
    return source


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: patch_android_surface_flush.py PINNED_WINDOW_C", file=sys.stderr)
        return 2
    path = Path(argv[1])
    if not path.is_file() or path.is_symlink():
        print("Refusing missing or symlinked WineAndroid source", file=sys.stderr)
        return 2
    original = path.read_text(encoding="utf-8")
    updated = patch_source(original)
    path.write_text(updated, encoding="utf-8")
    print("WINE29_ANDROID_SURFACE_FLUSH_ERROR_GATE=PATCHED (source-only)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
