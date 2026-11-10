"""No-execution source module dependency contracts for missing copy providers."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "analysis/wine29_bootstrap/audit_provider_sources.py"
SPEC = importlib.util.spec_from_file_location("charoite_provider_audit", SCRIPT)
A = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(A)

def fixtures():
    sources = {name: "MODULE = " + name + "\nIMPORTS = ntoskrnl\n"
               for name in A.SOURCE_BLOBS}
    sources["mscms.dll"] = ("MODULE = mscms.dll\n"
        "IMPORTS = $(LCMS2_PE_LIBS) shlwapi advapi32\n")
    for name in ("winebth.sys","winebus.sys","wineusb.sys"):
        sources[name] += "UNIXLIB = " + name.split(".")[0] + ".so\n"
    return sources

class ProviderAudit(unittest.TestCase):
    def test_matches_only_exact_pinned_eight_providers(self):
        self.assertEqual(len(A.SOURCE_BLOBS), 8)
        self.assertEqual(set(A.SOURCE_BLOBS), {
            "mscms.dll","hidclass.sys","mouhid.sys","winebth.sys",
            "winebus.sys","winehid.sys","wineusb.sys","winexinput.sys"})

    def test_categorizes_unix_side_and_external_toolchain_requirements(self):
        pe={"x%02d.dll" % i for i in range(34)}
        r=A.analyze(fixtures(),pe,set(A.SOURCE_BLOBS))
        self.assertEqual(r["provider_source_files_verified"],8)
        self.assertEqual(set(r["unix_companion_required_by"]),
                         {"winebth.sys","winebus.sys","wineusb.sys"})
        self.assertEqual(r["external_build_macro_modules"],["mscms.dll"])
        self.assertFalse(r["runtime_correction_verified"])
        self.assertFalse(r["phone_accessed"])
        self.assertTrue(r["source_only"])

    def test_fails_closed_on_wrong_module_name_and_new_providers(self):
        with self.assertRaises(ValueError):
            A.parse_makefile("winehid.sys","MODULE = rpcss.exe\nIMPORTS = ntdll\n")
        with self.assertRaises(ValueError):
            A.parse_makefile("winehid.sys","MODULE = winehid.sys\n"
                             "MODULE = winehid.sys\nIMPORTS = ntdll\n")
        with self.assertRaises(ValueError):
            A.parse_makefile("made-up.dll","MODULE = made-up.dll\nIMPORTS = ntdll\n")
        with self.assertRaises(ValueError):
            A.analyze(fixtures(),{"x%d.dll"%i for i in range(34)},{"mscms.dll"})

    def test_git_blob_identity_is_git_format(self):
        import hashlib
        self.assertEqual(A.git_blob_sha(b"hello\n"),
                         hashlib.sha1(b"blob 6\0hello\n").hexdigest())

    def test_workflow_never_builds_or_executes_phone_wine(self):
        y=(ROOT / ".github/workflows/wine29-v28-copyqueue-source-audit.yml").read_text()
        for req in ("audit_provider_sources.py", "The412Banner/proton-wine",
                    "c74acb09d51b447f5d5ac56c87608d3ec565a767",
                    "wine29-arm64-provider-source-audit.json"):
            self.assertIn(req,y)
        for banned in ("adb shell","wineboot -i","wineserver -p",
                       "assembleDebug","gh release create","OPENAI_API_KEY"):
            self.assertNotIn(banned,y)

if __name__ == "__main__":
    unittest.main()
