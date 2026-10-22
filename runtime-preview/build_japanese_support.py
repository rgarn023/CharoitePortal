#!/usr/bin/env python3
"""Create a licensed Japanese font + compiled glibc locale addon for Wine.

Do not commit/download proprietary Windows fonts. Pin an official SIL-OFL
Noto Sans CJK Japanese font at an immutable commit and verify its Git blob.
The compiled ja_JP.utf8 locale is built from the same rootfs locale sources.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

FONT_COMMIT = "f8d157532fbfaeda587e826d4cd5b21a49186f7c"
FONT_BLOB = "f56224957fb13a81b4c14bac34f2f058a017f9fb"
FONT_PATH = "Sans/OTF/Japanese/NotoSansCJKjp-Regular.otf"
LICENSE_PATH = "Sans/LICENSE"
REPO_BASE = f"https://raw.githubusercontent.com/notofonts/noto-cjk/{FONT_COMMIT}/"
FONT_NAME = "NotoSansCJKjp-Regular.otf"

def run(*args: str, **kwargs) -> None:
    subprocess.run(args, check=True, **kwargs)

def download(path: str) -> bytes:
    with urllib.request.urlopen(REPO_BASE + path, timeout=100) as response:
        return response.read()

def main(root: Path) -> None:
    assets = root / "app/src/main/assets"
    archive = assets / "rootfs.tzst"
    if not archive.is_file():
        raise SystemExit("Pinned Winlator rootfs.tzst is missing")
    font = download(FONT_PATH)
    object_bytes = b"blob " + str(len(font)).encode() + b"\0" + font
    if hashlib.sha1(object_bytes).hexdigest() != FONT_BLOB:
        raise ValueError("Noto font Git blob does not match pinned official revision")
    if not font.startswith(b"OTTO"):
        raise ValueError("Expected an OpenType Japanese font")
    license_content = download(LICENSE_PATH)
    if b"SIL OPEN FONT LICENSE Version 1.1" not in license_content:
        raise ValueError("Font license verification failed")
    license_dir = assets / "licenses"
    license_dir.mkdir(parents=True, exist_ok=True)
    (license_dir / "NotoSansCJK-OFL.txt").write_bytes(license_content)

    with tempfile.TemporaryDirectory(prefix="touhou-japanese-") as tmp:
        temp = Path(tmp)
        rootfs_sources = temp / "rootfs"
        rootfs_sources.mkdir()
        run("tar", "--use-compress-program=zstd", "-xf", str(archive),
            "-C", str(rootfs_sources), "./usr/share/i18n")
        i18n_path = rootfs_sources / "usr/share/i18n"
        if not (i18n_path / "locales/ja_JP").is_file():
            raise ValueError("Japanese locale definition missing in pinned rootfs")
        dest = temp / "addon"
        out_font = dest / "usr/share/fonts/opentype/noto" / FONT_NAME
        out_font.parent.mkdir(parents=True, exist_ok=True)
        out_font.write_bytes(font)
        locale_dir = dest / "usr/lib/locale/ja_JP.utf8"
        locale_dir.parent.mkdir(parents=True, exist_ok=True)
        env = os.environ.copy()
        env["I18NPATH"] = str(i18n_path)
        run("localedef", "-c", "--no-archive", "-i", "ja_JP", "-f", "UTF-8",
            str(locale_dir), env=env)
        for component in ["LC_CTYPE", "LC_COLLATE", "LC_TIME"]:
            if not (locale_dir / component).is_file():
                raise ValueError(f"Incomplete compiled Japanese locale: {component}")
        addon = assets / "japanese" / "japanese-support.tzst"
        addon.parent.mkdir(parents=True, exist_ok=True)
        run("tar", "--use-compress-program=zstd", "-cf", str(addon), "-C", str(dest), ".")
        print(f"Japanese support prepared: {len(font)} font bytes, "
              f"{addon.stat().st_size} addon bytes, SIL-OFL license included")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: build_japanese_support.py PINNED_WINLATOR_ROOT")
    main(Path(sys.argv[1]).resolve())
