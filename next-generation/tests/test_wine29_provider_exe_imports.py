"""Offline regression for kernel-mode PE import name validation.

Windows drivers can import ntoskrnl.exe; this does not imply binary closure.
No PE, Wine, Android or device process is executed.
"""
import importlib.util
from pathlib import Path
import unittest

PARSER = Path(__file__).resolve().parents[1] / "wine29-imports" / "classify.py"


class ProviderImportNameContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("wine29_pe_import_parser", PARSER)
        cls.parser = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.parser)

    def test_kernel_provider_imports_accept_exe_and_dll(self):
        for name in ("ntoskrnl.exe", "hidparse.sys.dll", "win32u.dll", "kernel32.dll"):
            with self.subTest(name=name):
                self.assertIsNotNone(self.parser.IDENTIFIER.fullmatch(name))

    def test_import_name_validation_remains_bounded(self):
        for name in ("../ntoskrnl.exe", "/ntoskrnl.exe", "ntoskrnl.exe/evil",
                     "ntoskrnl.exe\\evil", "ntoskrnl.exe\n", "ntoskrnl", "evil.so"):
            with self.subTest(name=name):
                self.assertIsNone(self.parser.IDENTIFIER.fullmatch(name))


if __name__ == "__main__":
    unittest.main()
