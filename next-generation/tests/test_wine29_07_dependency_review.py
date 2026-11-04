"""Source-only Wine29 .0.7 unbundled import ownership and old-data protections."""
import importlib.util
from pathlib import Path
import unittest

NEXT = Path(__file__).resolve().parents[1]
SCRIPT = NEXT / "wine29_07_dependency_review.py"
spec = importlib.util.spec_from_file_location("wine29_dependency_review", SCRIPT)
AUDIT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(AUDIT)
TEXT = SCRIPT.read_text(encoding="utf-8")
WORKFLOW = (NEXT.parent / ".github/workflows/wine29-07-dependency-review.yml")


def manifest_with_gap():
    dlls = (
        "ntdll kernelbase kernel32 advapi32 user32 ws2_32 crypt32 "
        "setupapi shlwapi version win32u gdi32 ucrtbase shell32 rpcrt4 "
        "combase ole32 comctl32 bcrypt secur32 sechost msvcrt apisetschema"
    ).split()
    assert len(dlls) == 23
    components = {}
    for name in ("wine", "wineserver", "ntdll_unix"):
        components[name] = {"format": "ELF", "path": "runtime/bin/" + name}
    for name in dlls:
        components[name] = {
            "format": "PE", "path": f"runtime/pe/arm64ec/{name}.dll",
            "imports": []
        }
    components["wineboot"] = {
        "format": "PE", "path": "runtime/pe/arm64/wineboot.exe", "imports": [
            "kernel32.dll", "ntdll.dll", "coml2.dll"
        ]
    }
    for name, unbundled in (
        ("ole32", "coml2.dll"),
        ("user32", "imm32.dll"),
        ("comctl32", "oleacc.dll"),
        ("combase", "oleaut32.dll"),
        ("shell32", "shcore.dll")
    ):
        components[name]["imports"] = [unbundled, "ntdll.dll"]
    all_imports = sorted({
        entry for item in components.values() for entry in item.get("imports", [])
    })
    gap = sorted(set(all_imports) - {n + ".dll" for n in dlls})
    manifest = {
        "version": AUDIT.VERSION, "source_commit": AUDIT.SOURCE,
        "component_count": 27, "nls_count": 76,
        "window_imports_unresolved_count": len(gap),
        "components": components
    }
    attestation = {
        "schema_version": 1,
        "bundled_windows_dlls": sorted(n + ".dll" for n in dlls),
        "observed_windows_imports": all_imports,
        "windows_imports_not_bundled": gap
    }
    return manifest, attestation


class Wine29SourceImportOwnership(unittest.TestCase):
    def test_source_gap_exactly_matches_actual_phone_names(self):
        manifest, evidence = manifest_with_gap()
        result = AUDIT.inspect(manifest, evidence)
        self.assertEqual(result["source_unbundled_imports"], list(AUDIT.PHONE_GAP))
        self.assertEqual(result["phone_reported_direct_unbundled_imports"],
                         list(AUDIT.PHONE_GAP))
        self.assertEqual(result["source_only_unbundled_imports"], [])
        self.assertEqual(result["pe_files"], 24)
        self.assertEqual(result["dll_files"], 23)
        self.assertEqual(result["nls_files"], 76)
        self.assertEqual(result["phone_direct_import_owners"]["coml2.dll"],
                         ["ole32.dll", "wineboot.exe"])
        self.assertFalse(result["wineboot_executed"])
        self.assertFalse(result["launch_ready"])

    def test_manifest_tampering_and_new_gap_fail_closed(self):
        manifest, evidence = manifest_with_gap()
        manifest["components"]["wineboot"]["path"] = "runtime/../prefix/drive_c"
        with self.assertRaisesRegex(ValueError, "path mismatch"):
            AUDIT.inspect(manifest, evidence)
        manifest, evidence = manifest_with_gap()
        manifest["components"]["ole32"]["imports"].append("unknown.dll")
        with self.assertRaisesRegex(ValueError, "review mismatch"):
            AUDIT.inspect(manifest, evidence)
        manifest, evidence = manifest_with_gap()
        evidence["observed_windows_imports"].append("unknown.dll")
        with self.assertRaisesRegex(ValueError, "review mismatch"):
            AUDIT.inspect(manifest, evidence)
        manifest, evidence = manifest_with_gap()
        manifest["components"]["ole32"]["imports"].append("coml2.dll")
        with self.assertRaisesRegex(ValueError, "metadata"):
            AUDIT.inspect(manifest, evidence)

    def test_phone_gap_must_not_be_silently_changed(self):
        manifest, evidence = manifest_with_gap()
        manifest["components"]["shell32"]["imports"] = ["ntdll.dll"]
        evidence["windows_imports_not_bundled"] = sorted(
            set(evidence["windows_imports_not_bundled"]) - {"shcore.dll"})
        evidence["observed_windows_imports"] = sorted(
            set(evidence["observed_windows_imports"]) - {"shcore.dll"})
        manifest["window_imports_unresolved_count"] = 4
        with self.assertRaisesRegex(ValueError, "Phone five direct imports missing"):
            AUDIT.inspect(manifest, evidence)

    def test_source_can_contain_additional_names_outside_phone_direct_imports(self):
        manifest, evidence = manifest_with_gap()
        manifest["components"]["user32"]["imports"].append("gdiplus.dll")
        evidence["observed_windows_imports"] = sorted(
            set(evidence["observed_windows_imports"]) | {"gdiplus.dll"})
        evidence["windows_imports_not_bundled"] = sorted(
            set(evidence["windows_imports_not_bundled"]) | {"gdiplus.dll"})
        manifest["window_imports_unresolved_count"] = 6
        result = AUDIT.inspect(manifest, evidence)
        self.assertEqual(result["source_only_unbundled_imports"], ["gdiplus.dll"])
        self.assertEqual(result["source_unbundled_import_owners"]["gdiplus.dll"],
                         ["user32.dll"])
        self.assertEqual(len(result["phone_reported_direct_unbundled_imports"]), 5)

    def test_no_pe_execution_or_android_mutation_and_ci_workflow(self):
        for forbidden in (
            "subprocess.", "ProcessBuilder(", "wineboot -i",
            "Runtime.getRuntime(", "shutil.rmtree(", "unlink(",
            "mkdir(", "mkdirs(", "os.system(",
        ):
            self.assertNotIn(forbidden, TEXT)
        for literal in (
            "verify-bootstrap-bundle.py", "module.verify(archive)",
            "source_archive_sha256", "WINE29_07_PINNED_SOURCE_IMPORT_OWNER_AUDIT=PASS",
            "PHONE_FIVE_IMPORTS_INCLUDED_IN_SOURCE_REVIEW=PASS", "WINDOWS_LAUNCH_READY=FALSE",
            "source_archive_sha256", "prefix_created",
        ):
            self.assertIn(literal, TEXT)
        self.assertTrue(WORKFLOW.name == "wine29-07-dependency-review.yml")


if __name__ == "__main__":
    unittest.main()
