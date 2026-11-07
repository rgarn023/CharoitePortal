"""CI-only verified Wine29 ELF literal-selector audit tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "audit_wine29_07_selectors.py"
spec = importlib.util.spec_from_file_location("selector_audit", SCRIPT)
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)


class SelectorAuditTests(unittest.TestCase):
    def make_inputs(self, root, selectors=None):
        root = Path(root)
        natives = root / "jniLibs"
        natives.mkdir(parents=True)
        selectors = selectors or {}
        items = {}
        for key, (source, filename) in AUDIT.EXPECTED.items():
            elf = bytearray(b"\x7fELF\x02\x01" + b"\x00" * 58)
            struct.pack_into("<H", elf, 18, 183)
            for marker in selectors.get(key, []):
                elf.extend(marker.encode("ascii") + b"\x00")
            data = bytes(elf)
            (natives / filename).write_bytes(data)
            items[key] = {
                "source": source, "filename": filename,
                "size": len(data), "machine": "AArch64",
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        index = root / "index.json"
        index.write_text(json.dumps({
            "schema_version": 1, "package": "com.charoitx",
            "source_run": AUDIT.EXPECTED_RUN,
            "wine_source_commit": AUDIT.EXPECTED_SOURCE,
            "bundle_version": "wine10-arm64ec-bootstrap.0.7",
            "native_elf_count": 3, "native_components": items,
        }), encoding="utf-8")
        return index, natives

    def test_exact_same_source_and_selector_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx, natives = self.make_inputs(tmp, {
                "wine": ["CHAROITE_WINE29_NATIVE_DIR"],
                "ntdll_unix": ["CHAROITE_WINE28_PE_DIR",
                               "CHAROITE_WINE29_PE_DIR"],
                "wineserver": ["CHAROITE_WINE29_DATA_DIR"],
            })
            report = AUDIT.inspect(idx, natives)
            self.assertEqual(report["native_elf_hashes_verified"], 3)
            self.assertEqual(report["wine_execution"], "NOT ATTEMPTED")
            self.assertEqual(
                report["preserved_v1_environment_selector_coverage"]["CHAROITE_WINE29_PE_DIR"],
                ["ntdll_unix"])
            self.assertTrue(report["native_elf"]["ntdll_unix"]
                            ["literal_markers"]["CHAROITE_WINE28_PE_DIR"])
            self.assertIn("INCONCLUSIVE", report["diagnosis"])

    def test_tamper_or_wrong_provenance_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            idx, natives = self.make_inputs(tmp)
            loader = natives / AUDIT.EXPECTED["wine"][1]
            loader.write_bytes(loader.read_bytes() + b"tamper")
            with self.assertRaisesRegex(ValueError, "size mismatch"):
                AUDIT.inspect(idx, natives)
            idx2, natives2 = self.make_inputs(Path(tmp) / "fresh")
            data = json.loads(idx2.read_text())
            data["wine_source_commit"] = "0" * 40
            idx2.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError, "provenance"):
                AUDIT.inspect(idx2, natives2)

    def test_no_process_execution_or_phone_data_reads(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("subprocess", "os.system", "os.popen", "/data/data/",
                          "/data/user/", "shutil.rmtree", "unlink("):
            self.assertNotIn(forbidden, text)
        workflow = (ROOT.parent / ".github/workflows/charoite-next.yml").read_text()
        self.assertIn("audit_wine29_07_selectors.py", workflow)
        self.assertIn("wine29-native-selector-audit.json", workflow)


if __name__ == "__main__":
    unittest.main()
