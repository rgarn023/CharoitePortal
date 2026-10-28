"""Non-destructive Charoite Wine bootstrap dependency inventory contracts."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"audit-runtime-deps.py"
spec=importlib.util.spec_from_file_location("charoite_dependencies", SCRIPT)
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class DependencyAuditTest(unittest.TestCase):
    def test_readobj_imports(self):
        data="Import {\n Name: ADVAPI32.dll\n Symbol: Foo\n}\nImport {\n Name: ntdll.dll\n}"
        self.assertEqual(module.pe_imports(data), ["advapi32.dll", "ntdll.dll"])

    def test_elf_needed(self):
        txt="0x1 (NEEDED) Shared library: [libc.so]\n0x1 (NEEDED) Shared library: [libm.so]"
        self.assertEqual(module.elf_needed(txt), ["libc.so", "libm.so"])

    def test_elf_alignment(self):
        self.assertEqual(module.load_alignments("LOAD 0x0 0x0 0x0 0x1000 0x1000 R E 0x4000"), [16384])
        with self.assertRaisesRegex(ValueError, "16 KiB"):
            module.load_alignments("LOAD 0x0 0x0 0x0 0x1000 0x1000 R E 0x1000")
        with self.assertRaisesRegex(ValueError, "16 KiB"):
            module.load_alignments("DYNAMIC 0x0")

    def test_wine_pe_machines_distinguished(self):
        module.pe_machine("Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)", "arm64ec")
        module.pe_machine("Machine: IMAGE_FILE_MACHINE_ARM64 (0xAA64)", "arm64")
        with self.assertRaisesRegex(ValueError, "Wrong Windows PE"):
            module.pe_machine("Machine: IMAGE_FILE_MACHINE_ARM64 (0xAA64)", "arm64ec")

    def test_expected_component_inventory(self):
        self.assertEqual(len(module.COMPONENTS), 7)
        self.assertEqual(module.COMPONENTS["wineboot_arm64"][1], "arm64")
        self.assertEqual(module.COMPONENTS["kernel32_arm64ec"][1], "arm64ec")
        source=SCRIPT.read_text()
        for forbidden in ("adb install", "WINEPREFIX=", "rm -rf", "su -c", "installable\": True"):
            self.assertNotIn(forbidden, source)
        for required in ("launch_ready\": False", "prefix_created\": False", "device_tested\": False"):
            self.assertIn(required, source)

    def test_no_overwrite_report(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)
            with self.assertRaisesRegex(ValueError, "must be new"):
                module.main(["audit-runtime-deps.py", str(path), "/tmp/readelf", "/tmp/readobj", str(path)])

if __name__=="__main__":
    unittest.main()
