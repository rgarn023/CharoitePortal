"""Synthetic offline bounds tests for Wine29 PE import inspection; no PE execution."""
import importlib.util
from pathlib import Path
import struct
import unittest

MODULE = Path(__file__).resolve().parents[1] / "wine29-imports/classify.py"
spec = importlib.util.spec_from_file_location("wine29_import_bounds", MODULE)
parser = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parser)


def fixture(directory_size=40, name_rva=0x1080):
    raw = bytearray(1024)
    raw[:2] = b"MZ"
    struct.pack_into("<I", raw, 0x3c, 0x80)
    raw[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H", raw, 0x84, 0xAA64)
    struct.pack_into("<H", raw, 0x86, 1)
    struct.pack_into("<H", raw, 0x94, 240)
    opt = 0x98
    struct.pack_into("<H", raw, opt, 0x20b)
    struct.pack_into("<I", raw, opt + 108, 14)
    struct.pack_into("<II", raw, opt + 112 + 8, 0x1000, directory_size)
    section = opt + 240
    struct.pack_into("<IIII", raw, section + 8, 0x100, 0x1000, 0x100, 0x200)
    struct.pack_into("<I", raw, 0x200 + 12, name_rva)
    raw[0x280:0x28d] = b"ntoskrnl.exe\x00"
    return raw


class ImportSectionBounds(unittest.TestCase):
    def test_valid_import(self):
        ordinary, delayed = parser.pe_imports(bytes(fixture()))
        self.assertEqual(ordinary, ["ntoskrnl.exe"])
        self.assertEqual(delayed, [])

    def test_directory_cannot_cross_section_boundary(self):
        with self.assertRaisesRegex(ValueError, "range not backed"):
            parser.pe_imports(bytes(fixture(directory_size=0x120)))

    def test_name_cannot_terminate_in_next_section_or_padding(self):
        data = fixture(name_rva=0x10fe)
        data[0x2fe:0x300] = b"ab"
        data[0x300:0x304] = b".dll"
        with self.assertRaisesRegex(ValueError, "Unterminated"):
            parser.pe_imports(bytes(data))


if __name__ == "__main__":
    unittest.main()
