"""Fail-closed tests for experimental Charoite Wine ARM64EC kernel modules."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (ROOT / "build-kernel-bridge.sh").read_text()
spec = importlib.util.spec_from_file_location("charoite_verify_kernel", ROOT / "verify-kernel-bridge.py")
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class KernelBridgeContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name)
        self.components = {}
        for name in ("kernelbase", "kernel32"):
            p = self.path / f"{name}-arm64ec.dll"
            p.write_bytes(b"unit-test-PE-not-real" + name.encode())
            (self.path / f"{name}-pe-header.txt").write_text(
                "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")
            import hashlib
            self.components[name] = {
                "file": p.name, "pe_machine": "0xA641", "size": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest()
            }
        self.manifest = {
            "schema_version": 1,
            "source_commit": verifier.SOURCE_SHA,
            "android_package": "com.charoitx",
            "machine": "IMAGE_FILE_MACHINE_ARM64EC",
            "pe_machine": "0xA641",
            "launch_ready": False, "installable": False,
            "base_slice_required": True,
            "components": self.components,
        }
        self.save()

    def save(self):
        (self.path / "kernel-bridge-manifest.json").write_text(json.dumps(self.manifest))

    def tearDown(self):
        self.tmp.cleanup()

    def test_same_source_build_and_no_installs(self):
        self.assertIn("charoite-source-validation.txt", SCRIPT)
        self.assertIn("dlls/ntdll/aarch64-windows/ntdll.dll", SCRIPT)
        self.assertIn("dlls/kernelbase/aarch64-windows/kernelbase.dll", SCRIPT)
        self.assertIn("dlls/kernel32/aarch64-windows/kernel32.dll", SCRIPT)
        for prohibited in ("adb install", "rm -rf", "com.charoite/files", "su -c"):
            self.assertNotIn(prohibited, SCRIPT)

    def test_verified_metadata(self):
        self.assertEqual(set(verifier.verify(self.path)["components"]),
                         {"kernelbase", "kernel32"})

    def test_corrupt_binary_is_rejected(self):
        (self.path / "kernelbase-arm64ec.dll").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError, "Hash/size"):
            verifier.verify(self.path)

    def test_normal_arm64_header_is_rejected(self):
        (self.path / "kernel32-pe-header.txt").write_text(
            "Machine: IMAGE_FILE_MACHINE_ARM64 (0xAA64)\n")
        with self.assertRaisesRegex(ValueError, "Wrong inspected PE"):
            verifier.verify(self.path)

    def test_cannot_enable_unverified_runtime(self):
        self.manifest["launch_ready"] = True
        self.save()
        with self.assertRaisesRegex(ValueError, "fail closed"):
            verifier.verify(self.path)

    def test_extra_files_rejected(self):
        (self.path / "extra.dll").write_bytes(b"payload")
        with self.assertRaisesRegex(ValueError, "Unexpected files"):
            verifier.verify(self.path)


if __name__ == "__main__":
    unittest.main()
