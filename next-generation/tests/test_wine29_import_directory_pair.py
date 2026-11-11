"""Offline malformed PE directory regression; no Wine or executable runs."""
import importlib.util
from pathlib import Path
import struct
import unittest

PARSER = Path(__file__).resolve().parents[1] / "wine29-imports/classify.py"
spec = importlib.util.spec_from_file_location("wine29_import_parser", PARSER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def synthetic_pe():
    data = bytearray(1024)
    data[:2] = b"MZ"
    struct.pack_into("<I", data, 0x3c, 0x80)
    data[0x80:0x84] = b"PE\x00\x00"
    struct.pack_into("<H", data, 0x84, 0xAA64)
    struct.pack_into("<H", data, 0x86, 1)
    struct.pack_into("<H", data, 0x94, 240)
    opt = 0x98
    struct.pack_into("<H", data, opt, 0x20b)
    struct.pack_into("<I", data, opt + 108, 16)
    section = opt + 240
    struct.pack_into("<IIII", data, section + 8, 256, 0x1000, 256, 0x300)
    return data, opt


class ImportDirectoryBoundsTests(unittest.TestCase):
    def test_empty_directories_are_valid(self):
        data, _ = synthetic_pe()
        self.assertEqual(module.pe_imports(bytes(data)), ([], []))

    def test_import_directory_requires_both_rva_and_size(self):
        for index in (1, 13):
            for rva, size in ((0, 20), (0x1000, 0)):
                with self.subTest(index=index, rva=rva, size=size):
                    data, opt = synthetic_pe()
                    struct.pack_into("<II", data, opt + 112 + index * 8, rva, size)
                    with self.assertRaisesRegex(ValueError, "Inconsistent PE import directory"):
                        module.pe_imports(bytes(data))


if __name__ == "__main__":
    unittest.main()
