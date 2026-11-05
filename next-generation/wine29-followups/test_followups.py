"""Source-only Wine29 23+6+2 dependency graph and safety regression."""
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / "wine29-followups/verify-followups.py"
BUILDER = ROOT / "wine29-followups/build-followups.sh"
spec = importlib.util.spec_from_file_location("followup_contract", CHECKER)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class FollowupContracts(unittest.TestCase):
    def test_two_candidates_source_only(self):
        self.assertEqual(mod.EXTRA, ("urlmon", "windowscodecs"))
        self.assertEqual(len(mod.BASELINE_SHA), 64)
        self.assertEqual(mod.SOURCE, mod.sixlib.SOURCE_COMMIT)
        src = BUILDER.read_text()
        for token in ("urlmon windowscodecs", "make -j2", "--coff-imports",
                      "--file-headers", "verify-wine29-deps.py",
                      "WINE29_07_SOURCE_ONLY_2_TRANSITIVE_CANDIDATES=PASS"):
            self.assertIn(token, src)
        for token in ("wineboot -i", "WINEPREFIX=", "adb install", "rm -rf "):
            self.assertNotIn(token, src)

    def test_graph_keeps_remaining_imports_and_owner_edges(self):
        baseline = {"source_commit": mod.SOURCE,
                    "version": "wine10-arm64ec-bootstrap.0.7",
                    "components": {"wine": {"format": "ELF"},
                                   "wineserver": {"format": "ELF"},
                                   "ntdll_unix": {"format": "ELF"},
                                   "wineboot": {"format": "PE", "imports": ["newdev.dll"]}}}
        for i in range(23):
            baseline["components"][f"base_{i}"] = {"format": "PE", "imports": []}
        six = {name: {"imports": []} for name in mod.sixlib.MODULES}
        extra = {"urlmon": {"imports": ["wininet.dll"]},
                 "windowscodecs": {"imports": ["base_1.dll"]}}
        graph = mod.import_closure(baseline, six, extra)
        self.assertEqual(graph["provider_dll_count"], 31)
        self.assertEqual(graph["unresolved_import_names"], ["wininet.dll"])
        self.assertEqual(graph["unresolved_import_owners"]["wininet.dll"], ["urlmon.dll"])
        self.assertEqual(graph["new_two_imports"]["windowscodecs"], ["base_1.dll"])

    def test_source_guards_and_no_false_runtime_claim(self):
        src = CHECKER.read_text()
        for flag in ('"launch_ready": False', '"wineboot_executed": False',
                     '"device_tested": False', '"installed": False',
                     '"not_proof_of_loader_dependency_closure": True',
                     '"not_proof_of_currency_rounding_equivalence": True',
                     "bundlelib.verify(archive)", 'sixlib.run("verify"', "safe_file(report)",
                     "Unexpected file in new sealed two-DLL cohort"):
            self.assertIn(flag, src)
        for path in mod.FORBIDDEN:
            self.assertIn(path, BUILDER.read_text())
        with self.assertRaises(ValueError):
            mod.import_closure({}, {}, {})


if __name__ == "__main__":
    unittest.main()
