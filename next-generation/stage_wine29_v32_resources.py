"""Prepare the eight verified resource payloads as ordinary SetupAPI media."""
import hashlib
import json
import sys
from pathlib import Path
from zipfile import ZipFile

import pefile

ARCHIVES = (
    ("a311363f3dfa442742b817b8b5d74a3256a8d844a23f5c2ea09beb69826e082a", {
        "mscms.dll": "srgb color space profile.icm",
        "winebth.sys": "winebth.inf",
        "winebus.sys": "winebus.inf",
        "wineusb.sys": "wineusb.inf",
    }),
    ("3d666572de99fa0d0c0cf9c51ad4ef8318ce18dcdcd51e13e603db7db54915a8", {
        "hidclass.sys": "input.inf",
        "mouhid.sys": "mouhid.inf",
        "winehid.sys": "winehid.inf",
        "winexinput.sys": "winexinput.inf",
    }),
)
INF_SHA = "5c7a7041399370937bdaaec11bac8ab64b910d6a1877b6afb582ad1d6a2f894a"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def resource(binary):
    with pefile.PE(data=binary) as pe:
        if pe.FILE_HEADER.Machine != 0xAA64:
            raise ValueError("Expected ARM64 provider")
        entries = [
            leaf.data.struct
            for kind in pe.DIRECTORY_ENTRY_RESOURCE.entries
            if str(kind.name) == "WINE_DATA_FILE"
            for item in kind.directory.entries if item.id == 1
            for leaf in item.directory.entries if leaf.id == 0
        ]
        if len(entries) != 1 or not 0 < entries[0].Size <= 65536:
            raise ValueError("Expected one bounded neutral WINE_DATA_FILE resource 1")
        entry = entries[0]
        payload = pe.get_data(entry.OffsetToData, entry.Size)
        if len(payload) != entry.Size:
            raise ValueError("Truncated resource")
        return payload


def stage(archive_paths, inf_path, output):
    inf = inf_path.read_bytes()
    if digest(inf) != INF_SHA:
        raise ValueError("Unexpected wine.inf digest")
    payloads = {}
    for index, (path, (expected, providers)) in enumerate(zip(archive_paths, ARCHIVES, strict=True)):
        if digest(path.read_bytes()) != expected:
            raise ValueError(f"Unexpected provider archive digest: {path.name}")
        with ZipFile(path) as archive:
            for provider, target in providers.items():
                member = (provider + "-arm64-pe-candidate" if index == 0
                          else provider.removesuffix(".sys") + "-arm64.sys")
                payloads[target] = resource(archive.read(member))
                directory_id = 11 if provider.endswith(".dll") else 12
                row = f'{target},"@%{directory_id}%\\{provider},-1"'.encode()
                if inf.count(row) != 1:
                    raise ValueError(f"Unexpected INF row for {provider}")
                inf = inf.replace(row, f'{target},"{target}"'.encode(), 1)
    files = {**payloads, "charoite-v32.inf": inf}
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (output / name).write_bytes(data)
    (output / "manifest.json").write_text(
        json.dumps({name: digest(data) for name, data in files.items()}, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    first, second, inf, output = map(Path, sys.argv[1:])
    stage((first, second), inf, output)
