"""Strict no-Wine-execution 111-file sealed data-only archive tests."""
import importlib.util
from pathlib import Path
import tempfile
import tarfile
import unittest

HERE = Path(__file__).resolve().parent
SCRIPT = HERE / "package34.py"
spec = importlib.util.spec_from_file_location("wine29_package34", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class Wine29DataBundleContracts(unittest.TestCase):
    def test_static_guard_and_manifest_disclaimers(self):
        text = SCRIPT.read_text()
        self.assertEqual(module.GENERATION,
                         "wine10-arm64ec-dependencies.0.12-sealed-data-candidate")
        for label in ("gate.inspect(", "len(payload) != 111", "len(nls) != 76",
                      "len(names) != 34", '"native_elf_files_in_bundle": 0',
                      '"launch_ready": False', '"wineboot_executed": False',
                      'GzipFile(filename="",', 'mtime=0', '"xb"'):
            self.assertIn(label, text)
        for prohibited in ("subprocess.run(", "os.system(", "Popen(",
                           "adb install", "wineboot -i", "rm -rf"):
            self.assertNotIn(prohibited, text)

    def test_reject_existing_output_and_relative_path(self):
        with tempfile.TemporaryDirectory() as t:
            p = Path(t) / "archive.tar.gz"
            module.safe_output(p)
            p.write_bytes(b"old")
            with self.assertRaises(ValueError):
                module.safe_output(p)
            with self.assertRaises(ValueError):
                module.safe_output(Path("archive.tar.gz"))

    def test_reject_bad_members_and_duplicates(self):
        m = tarfile.TarInfo("data/one")
        m.size = 10
        m.mode = 0o444
        module.validate_members([m], {"data/one"})
        with self.assertRaises(ValueError):
            module.validate_members([m, m], {"data/one"})
        m.type = tarfile.SYMTYPE
        with self.assertRaises(ValueError):
            module.validate_members([m], {"data/one"})

    def test_deterministic_archive_and_tampering(self):
        with tempfile.TemporaryDirectory() as t:
            a, b = Path(t) / "one.tar.gz", Path(t) / "two.tar.gz"
            payload = {"data/pe/arm64ec/example.dll": b"fake-test-pe"}
            record = {"demo": False}
            module.write_archive(a, payload, record)
            module.write_archive(b, payload, record)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            self.assertEqual(module.verify_archive(a, payload, record),
                             module.verify_archive(b, payload, record))
            with self.assertRaises(ValueError):
                module.verify_archive(a, payload, {"demo": True})


if __name__ == "__main__":
    unittest.main()
