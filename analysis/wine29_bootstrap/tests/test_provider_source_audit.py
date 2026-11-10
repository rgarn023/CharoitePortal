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

    def test_rejects_unclassified_import_tokens_instead_of_omitting_them(self):
        for invalid in ("foo.dll", "$(UNKNOWN)/path", "$(BROKEN", "foo;bar",
                        "$(lowercase)", "-lfoo", "foo\\bar", "foo#comment"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                A.parse_makefile("winehid.sys",
                    "MODULE = winehid.sys\nIMPORTS = ntoskrnl " + invalid + "\n")

    def test_accepts_macro_as_whole_token_and_reports_it(self):
        parsed = A.parse_makefile("mscms.dll",
            "MODULE = mscms.dll\nIMPORTS = $(LCMS2_PE_LIBS) shlwapi advapi32\n")
        self.assertEqual(parsed["build_macros"], ["$(LCMS2_PE_LIBS)"])
        self.assertEqual(parsed["imports"], ["advapi32", "shlwapi"])

    def test_pinned_unix_companions_cannot_be_added_renamed_or_dropped(self):
        for provider, native in (
            ("winebth.sys", "winebth.so"),
            ("winebus.sys", "winebus.so"),
            ("wineusb.sys", "wineusb.so"),
        ):
            with self.subTest(provider=provider):
                parsed = A.parse_makefile(provider,
                    "MODULE = " + provider + "\nIMPORTS = ntoskrnl\n"
                    "UNIXLIB = " + native + "\n")
                self.assertEqual(parsed["unix_companion"], native)
                for invalid in ("", "other.so", native.upper(),
                                "../" + native, "lib" + native):
                    with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                        A.parse_makefile(provider,
                            "MODULE = " + provider + "\nIMPORTS = ntoskrnl\n"
                            "UNIXLIB = " + invalid + "\n")
        for provider in set(A.SOURCE_BLOBS) - {
            "winebth.sys", "winebus.sys", "wineusb.sys"
        }:
            with self.subTest(unexpected=provider), self.assertRaises(ValueError):
                A.parse_makefile(provider,
                    "MODULE = " + provider + "\nIMPORTS = ntoskrnl\n"
                    "UNIXLIB = unexpected.so\n")

    def test_parent_symlink_is_explicitly_rejected_before_makefile_read(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("directory.is_symlink()", source)
        self.assertIn("path.is_symlink()", source)
        self.assertLess(source.index("directory.is_symlink()"),
                        source.index("data = path.read_bytes()"))

    def test_copyqueue_handoff_requires_exact_distinct_list_and_safety_flags(self):
        valid = {
            "source_only": True, "wine_executed": False, "v28_reused": False,
            "resource_providers_not_in_sealed_pe": sorted(A.SOURCE_BLOBS),
        }
        self.assertEqual(A.validate_copyqueue_provider_list(valid),
                         set(A.SOURCE_BLOBS))
        import copy
        cases = []
        for replacement in (
            "mscms.dll", None, {}, [None] * 8,
            ["mscms.dll"] * 8,
            sorted(A.SOURCE_BLOBS)[:-1],
            sorted(A.SOURCE_BLOBS) + ["extra.dll"],
        ):
            bad = copy.deepcopy(valid)
            bad["resource_providers_not_in_sealed_pe"] = replacement
            cases.append(bad)
        for key, value in (("source_only", "true"),
                           ("wine_executed", True),
                           ("v28_reused", True)):
            bad = copy.deepcopy(valid)
            bad[key] = value
            cases.append(bad)
        for bad in cases + [[], None]:
            with self.subTest(bad=repr(bad)[:100]), self.assertRaises(ValueError):
                A.validate_copyqueue_provider_list(bad)

    def test_analyze_rejects_missing_extra_sources_and_malformed_pe_names(self):
        inputs = fixtures()
        names = {"x%02d.dll" % i for i in range(34)}
        for malformed in (
            dict(list(inputs.items())[:-1]),
            dict(inputs, **{"extra.dll": "MODULE = extra.dll"}),
        ):
            with self.assertRaises(ValueError):
                A.analyze(malformed, names, set(A.SOURCE_BLOBS))
        for invalid in ("../escape.dll", "KERNEL32.DLL", "bad.sys", "x.dll/path"):
            changed = set(names)
            changed.remove("x00.dll")
            changed.add(invalid)
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                A.analyze(inputs, changed, set(A.SOURCE_BLOBS))

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
