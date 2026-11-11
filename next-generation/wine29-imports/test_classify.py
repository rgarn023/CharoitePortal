"""Safe PE32+ regular-versus-delay import parser tests, no binaries executed."""
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("wine29_import_classifier",ROOT/"classify.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture(regular="kernel32.dll", deferred="winspool.drv"):
    b=bytearray(0x800)
    b[:2]=b"MZ"
    struct.pack_into("<I",b,0x3c,0x80)
    b[0x80:0x84]=b"PE\x00\x00"
    struct.pack_into("<H",b,0x84,0xAA64)
    struct.pack_into("<H",b,0x86,1)
    struct.pack_into("<H",b,0x94,0xf0)
    optional=0x98
    struct.pack_into("<H",b,optional,0x20b)
    struct.pack_into("<Q",b,optional+24,0x180000000)
    struct.pack_into("<I",b,optional+108,16)
    # One .rdata section: file 0x200-0x5ff / RVA 0x1000-0x13ff
    section=optional+0xf0
    b[section:section+8]=b".rdata\x00\x00"
    struct.pack_into("<IIII",b,section+8,0x400,0x1000,0x400,0x200)
    if regular is not None:
        struct.pack_into("<II",b,optional+112+8,0x1000,40)
        struct.pack_into("<IIIII",b,0x200,0,0,0,0x1080,0)
        encoded=regular.encode()+b"\x00"
        b[0x280:0x280+len(encoded)]=encoded
    if deferred is not None:
        struct.pack_into("<II",b,optional+112+13*8,0x1100,64)
        struct.pack_into("<IIIIIIII",b,0x300,1,0x1180,0,0,0,0,0,0)
        encoded=deferred.encode()+b"\x00"
        b[0x380:0x380+len(encoded)]=encoded
    return bytes(b)


class PEImportClassificationContracts(unittest.TestCase):
    def test_regular_and_delay_imports_are_independent(self):
        self.assertEqual(mod.pe_imports(fixture()),(["kernel32.dll"],["winspool.drv"]))
        self.assertEqual(mod.pe_imports(fixture(None,"example.dll")),( [],["example.dll"]))
        self.assertEqual(mod.pe_imports(fixture("KERNEL32.DLL",None)),(["kernel32.dll"],[]))

    def test_kernel_driver_sys_imports_and_path_rejection(self):
        # Real pinned mouhid.sys imports hidparse.sys; it is not a DLL.
        self.assertEqual(mod.pe_imports(fixture("HIDPARSE.SYS", None)), (["hidparse.sys"], []))
        self.assertEqual(mod.pe_imports(fixture("ntoskrnl.exe", None)), (["ntoskrnl.exe"], []))
        for name in ("../hidparse.sys", "folder\\\\hidparse.sys", "hidparse.sys/other", "hidparse.so"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                mod.pe_imports(fixture(name, None))

    def test_fail_closed_on_missing_or_corrupt_pe_headers(self):
        bad=bytearray(fixture())
        bad[:2]=b"NO"
        with self.assertRaises(ValueError):mod.pe_imports(bytes(bad))
        bad=bytearray(fixture())
        struct.pack_into("<H",bad,0x84,0x8664)
        with self.assertRaises(ValueError):mod.pe_imports(bytes(bad))
        bad=bytearray(fixture())
        struct.pack_into("<I",bad,0x3c,0xfffffff0)
        with self.assertRaises(ValueError):mod.pe_imports(bytes(bad))

    def test_unterminated_or_unbacked_import_rejected(self):
        bad=bytearray(fixture())
        struct.pack_into("<II",bad,0x98+112+8,0x1000,20)
        with self.assertRaises(ValueError):mod.pe_imports(bytes(bad))
        bad=bytearray(fixture())
        struct.pack_into("<I",bad,0x200+12,0x80000000)
        with self.assertRaises(ValueError):mod.pe_imports(bytes(bad))

    def test_pinned_sources_and_runtime_safety_labels(self):
        source=(ROOT/"classify.py").read_text()
        for keyword in (
            "WINE29_ORIGINAL_GALAXY_REGULAR_IMPORTS_111_DESCRIPTORS_5_MISSING=PASS",
            "WINE29_31_DLL_REGULAR_PE_UNBUNDLED_ONLY_PROPSYS_AND_WININET=PASS",
            '"wineboot_executed": False', '"phone_installed": False',
            '"launch_ready": False', '"currency_boundary_rounding_unverified": True',
            "winspool.drv", "verify-bootstrap-bundle.py", "SOURCE_SHA",
            "not report.parent.is_dir()", "regular_unbundled_owners",
            "delay_unbundled_owners"
        ):
            self.assertIn(keyword,source)
        for token in ("wineboot -i", "WINEPREFIX=", "adb install", "rm -rf ",
                      "subprocess.run", "ProcessBuilder"):
            self.assertNotIn(token,source)
        self.assertEqual(set(mod.SIX_HASHES),{"coml2","imm32","oleacc","oleaut32","shcore","newdev"})
        self.assertEqual(set(mod.TWO_HASHES),{"urlmon","windowscodecs"})


if __name__=="__main__":
    unittest.main()
