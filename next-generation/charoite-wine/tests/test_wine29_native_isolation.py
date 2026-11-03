"""Source-only isolation gate for a FUTURE Wine29 native cohort; no Wine run."""
import hashlib
import importlib.util
from pathlib import Path
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "verify-wine29-native-isolation.py"
spec = importlib.util.spec_from_file_location("wine29_native_gate", FILE)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def fixture():
    components = {}
    payloads = {}
    for name, rel in M.NATIVE_MEMBERS.items():
        elf = bytearray(64)
        elf[:6] = b"\x7fELF\x02\x01"
        struct.pack_into("<H", elf, 18, 183)
        for marker in M.REQUIRED_NATIVE_MARKERS[name]:
            elf.extend(marker + b"\x00")
        body = bytes(elf)
        payloads[name] = body
        components[name] = {
            "format": "ELF", "path": rel,
            "machine": "AArch64", "load_alignments": [16384],
            "needed": ["libc.so"], "size": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        }
    for n in range(24):
        components["pe%d" % n] = {"format": "PE"}
    manifest = {
        "version": M.NEXT_COHORT,
        "android_package": "com.charoitx",
        "source_commit": M.PINNED_SOURCE,
        "component_count": 27,
        "nls_count": 76,
        "components": components,
        "launch_ready": False,
        "installable": False,
        "prefix_created": False,
        "device_tested": False,
        "anti_cheat_supported": False,
    }
    delta = b"\n".join(M.REQUIRED_SOURCE_MARKERS)
    return manifest, payloads, delta


class Wine29NativeIsolation(unittest.TestCase):
    def test_gate_is_read_only_and_never_executed_or_installed(self):
        source = FILE.read_text(encoding="utf-8")
        self.assertIn("verify-bootstrap-bundle.py", source)
        self.assertIn("CHAROITE_WINE29_NATIVE_DIR", source)
        self.assertIn("CHAROITE_WINE29_PE_DIR", source)
        self.assertIn("CHAROITE_WINE29_DATA_DIR", source)
        self.assertIn("Wine29/Wine28 selector conflict", source)
        self.assertNotIn("subprocess.", source)
        self.assertNotIn("ProcessBuilder(", source)
        self.assertNotIn("os.system(", source)
        self.assertNotIn("rmtree(", source)
        self.assertNotIn(".unlink(", source)

    def test_only_future_rebuilt_generation_can_pass(self):
        manifest, payloads, delta = fixture()
        result = M.check(manifest, payloads, delta)
        self.assertTrue(result["source_native_cohort_verified"])
        self.assertFalse(result["apk_native_install_permitted"])
        self.assertFalse(result["wineboot_execution_permitted"])
        self.assertFalse(result["phone_runtime_verified"])
        manifest["version"] = M.OLD_COHORT
        with self.assertRaisesRegex(ValueError, "Separate Wine29 native"):
            M.check(manifest, payloads, delta)

    def test_missing_isolation_and_conflict_guard_are_fatal(self):
        manifest, payloads, delta = fixture()
        with self.assertRaisesRegex(ValueError, "conflict guard"):
            M.check(manifest, payloads, delta.replace(b"Wine29/Wine28 selector conflict", b""))
        with self.assertRaisesRegex(ValueError, "not compiled"):
            other = dict(payloads)
            original = other["wine"]
            other["wine"] = original.replace(b"CHAROITE_WINE29_NATIVE_DIR", b"DISABLED_WINE29_NATIVE_DIR")
            manifest["components"]["wine"]["sha256"] = M.sha256(other["wine"])
            manifest["components"]["wine"]["size"] = len(other["wine"])
            M.check(manifest, other, delta)

    def test_mixed_native_hashes_and_unsafe_abi_are_rejected(self):
        manifest, payloads, delta = fixture()
        bad = dict(payloads)
        bad["wineserver"] += b"mixed-other-cohort"
        with self.assertRaisesRegex(ValueError, "hash mismatch"):
            M.check(manifest, bad, delta)
        manifest, payloads, delta = fixture()
        manifest["components"]["ntdll_unix"]["load_alignments"] = [4096]
        with self.assertRaisesRegex(ValueError, "ABI"):
            M.check(manifest, payloads, delta)
        manifest, payloads, delta = fixture()
        native = bytearray(payloads["wineserver"])
        struct.pack_into("<H", native, 18, 62)  # x86-64, not AArch64
        payloads["wineserver"] = bytes(native)
        manifest["components"]["wineserver"]["sha256"] = M.sha256(payloads["wineserver"])
        with self.assertRaisesRegex(ValueError, "ABI"):
            M.check(manifest, payloads, delta)

    def test_source_identity_and_launch_claim_fail_closed(self):
        manifest, payloads, delta = fixture()
        manifest["launch_ready"] = True
        with self.assertRaisesRegex(ValueError, "readiness"):
            M.check(manifest, payloads, delta)
        manifest, payloads, delta = fixture()
        manifest["android_package"] = "com.charoite"
        with self.assertRaisesRegex(ValueError, "generation"):
            M.check(manifest, payloads, delta)


if __name__ == "__main__":
    unittest.main()
