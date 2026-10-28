"""Source isolation and anti-tamper contract for Charoite Wineboot artifact."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
SCRIPT = (BASE / "build-wineboot.sh").read_text()
spec = importlib.util.spec_from_file_location("charoite_boot_verifier", BASE / "verify-wineboot.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class WinebootContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        data = b"synthetic-wineboot-not-executable"
        (self.root / "wineboot-arm64.exe").write_bytes(data)
        (self.root / "wineboot-pe-header.txt").write_text(
            "Machine: IMAGE_FILE_MACHINE_ARM64 (0xAA64)\n")
        self.manifest = {
            "schema_version": 1, "android_package": "com.charoitx",
            "source_commit": "c74acb09d51b447f5d5ac56c87608d3ec565a767",
            "pe_machine": "0xAA64", "status": "compiled-not-executed",
            "prefix_created": False, "installable": False,
            "launch_ready": False, "file": "wineboot-arm64.exe",
            "size": len(data), "sha256": hashlib.sha256(data).hexdigest(),
        }
        self.save()

    def save(self):
        (self.root / "wineboot-manifest.json").write_text(json.dumps(self.manifest))

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_pinned_source_and_existing_kernel_libraries(self):
        self.assertIn("charoite-source-validation.txt", SCRIPT)
        self.assertIn("dlls/kernelbase/aarch64-windows/kernelbase.dll", SCRIPT)
        self.assertIn("dlls/kernel32/aarch64-windows/kernel32.dll", SCRIPT)
        self.assertIn("programs/wineboot/aarch64-windows/wineboot.exe", SCRIPT)
        for value in ("rm -rf", "adb install", "com.charoite/files", "WINEPREFIX=", "su -c"):
            self.assertNotIn(value, SCRIPT)

    def test_verified_artifact(self):
        self.assertEqual(verifier.verify(self.root)["pe_machine"], "0xAA64")

    def test_corrupted_pe_rejected(self):
        (self.root / "wineboot-arm64.exe").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "tampered"):
            verifier.verify(self.root)

    def test_unverified_status_rejected(self):
        self.manifest["launch_ready"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            verifier.verify(self.root)

    def test_falsely_claiming_prefix_exists_rejected(self):
        self.manifest["prefix_created"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "Unsafe"):
            verifier.verify(self.root)


if __name__ == "__main__":
    unittest.main()
