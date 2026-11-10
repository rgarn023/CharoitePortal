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

    def test_import_plan_distinguishes_sealed_planned_and_external(self):
        # A planned .sys is not a verified built PE and must never be
        # counted as sealed just because its source Makefile is pinned.
        inputs = fixtures()
        inputs["winehid.sys"] = (
            "MODULE = winehid.sys\n"
            "IMPORTS = ntoskrnl winebus advapi32\n")
        sealed = {"x%02d.dll" % i for i in range(33)} | {"advapi32.dll"}
        result = A.analyze(inputs, sealed, set(A.SOURCE_BLOBS))
        row = next(p for p in result["providers"]
                   if p["module"] == "winehid.sys")
        self.assertEqual(row["imports_in_sealed_dlls"], ["advapi32"])
        self.assertEqual(row["imports_in_missing_provider_plan"],
                         [{"import": "winebus", "provider": "winebus.sys"}])
        self.assertEqual(row["imports_outside_sealed_and_provider_plan"],
                         ["ntoskrnl"])
        self.assertEqual(row["imports_not_in_sealed_dlls"],
                         ["ntoskrnl", "winebus"])
        self.assertTrue(result["provider_import_plan_only"])
        self.assertFalse(result["provider_pe_binaries_verified"])
        self.assertFalse(result["provider_native_companions_verified"])
        self.assertFalse(result["provider_import_closure_verified"])

    def test_dependency_first_order_is_stable_and_not_a_build_claim(self):
        inputs = fixtures()
        inputs["winehid.sys"] = (
            "MODULE = winehid.sys\nIMPORTS = winebus ntoskrnl\n")
        inputs["mouhid.sys"] = (
            "MODULE = mouhid.sys\nIMPORTS = winehid ntoskrnl\n")
        names = {"x%02d.dll" % i for i in range(34)}
        report = A.analyze(inputs, names, set(A.SOURCE_BLOBS))
        order = report["provider_source_build_order"]
        self.assertEqual(len(order), 8)
        self.assertEqual(set(order), set(A.SOURCE_BLOBS))
        self.assertLess(order.index("winebus.sys"), order.index("winehid.sys"))
        self.assertLess(order.index("winehid.sys"), order.index("mouhid.sys"))
        self.assertTrue(report["provider_source_build_order_only"])
        self.assertFalse(report["provider_pe_binaries_verified"])
        self.assertFalse(report["provider_import_closure_verified"])
        self.assertEqual(order, A.analyze(
            inputs, names, set(A.SOURCE_BLOBS))["provider_source_build_order"])

    def test_crossbuild_work_queue_exposes_unverified_external_native_and_macro_gates(self):
        inputs = fixtures()
        inputs["winehid.sys"] = (
            "MODULE = winehid.sys\\nIMPORTS = winebus ntoskrnl\\n")
        sealed = {"x%02d.dll" % i for i in range(34)}
        report = A.analyze(inputs, sealed, set(A.SOURCE_BLOBS))
        queue = report["provider_crossbuild_work_queue"]
        self.assertEqual([item["provider"] for item in queue],
                         report["provider_source_build_order"])
        self.assertTrue(report["provider_crossbuild_work_queue_only"])
        self.assertFalse(report["provider_pe_binaries_verified"])
        rows = {row["module"]: row for row in report["providers"]}
        for row in rows.values():
            self.assertFalse(row["crossbuild_verified"])
            self.assertIn("PINNED_ARM64_PE_BUILD_AND_IMPORT_TABLE",
                          row["crossbuild_verification_blockers"])
        self.assertIn("EXTERNAL_IMPORT_RESOLUTION",
                      rows["winehid.sys"]["crossbuild_verification_blockers"])
        self.assertIn("PLANNED_PROVIDER_PE_BUILD",
                      rows["winehid.sys"]["crossbuild_verification_blockers"])
        self.assertIn("ANDROID_BIONIC_UNIX_COMPANION",
                      rows["winebus.sys"]["crossbuild_verification_blockers"])
        self.assertIn("EXTERNAL_BUILD_MACRO_LINKAGE",
                      rows["mscms.dll"]["crossbuild_verification_blockers"])
        self.assertNotIn("ANDROID_BIONIC_UNIX_COMPANION",
                         rows["winehid.sys"]["crossbuild_verification_blockers"])
        self.assertLess(
            report["provider_source_build_order"].index("winebus.sys"),
            report["provider_source_build_order"].index("winehid.sys"))
        self.assertEqual(queue, A.analyze(
            inputs, sealed, set(A.SOURCE_BLOBS))["provider_crossbuild_work_queue"])

    def test_planned_provider_cycles_fail_closed_including_self_edge(self):
        names = {"x%02d.dll" % i for i in range(34)}
        inputs = fixtures()
        inputs["winehid.sys"] = "MODULE = winehid.sys\nIMPORTS = winebus\n"
        inputs["winebus.sys"] = (
            "MODULE = winebus.sys\nIMPORTS = winehid\nUNIXLIB = winebus.so\n")
        with self.assertRaisesRegex(ValueError, "Circular planned provider"):
            A.analyze(inputs, names, set(A.SOURCE_BLOBS))
        inputs = fixtures()
        inputs["winehid.sys"] = "MODULE = winehid.sys\nIMPORTS = winehid\n"
        with self.assertRaisesRegex(ValueError, "Invalid pinned provider"):
            A.analyze(inputs, names, set(A.SOURCE_BLOBS))

    def test_sealed_dll_takes_precedence_over_planned_stem(self):
        inputs = fixtures()
        inputs["winehid.sys"] = (
            "MODULE = winehid.sys\nIMPORTS = winebus\n")
        sealed = {"x%02d.dll" % i for i in range(33)} | {"winebus.dll"}
        row = next(p for p in A.analyze(inputs, sealed, set(A.SOURCE_BLOBS))["providers"]
                   if p["module"] == "winehid.sys")
        self.assertEqual(row["imports_in_sealed_dlls"], ["winebus"])
        self.assertEqual(row["imports_in_missing_provider_plan"], [])
        self.assertEqual(row["imports_outside_sealed_and_provider_plan"], [])

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
            "phone_accessed": False,
            "rpcss_registration_declared": True,
            "arm64_copy_sections": [
                "colorfiles", "etcfiles", "inffiles", "nlsfiles", "sortfiles"],
            "requested_nls_not_in_sealed": [],
            "requested_nls_count": 76,
            "sealed_nls_count": 76,
            "copyfile_rows": 88,
            "resource_provider_count": 8,
            "resource_providers_in_sealed_pe": [],
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

    def test_copyqueue_rejects_partial_or_contradictory_coverage(self):
        import copy
        valid = {
            "source_only": True, "wine_executed": False, "v28_reused": False,
            "phone_accessed": False, "rpcss_registration_declared": True,
            "arm64_copy_sections": [
                "colorfiles", "etcfiles", "inffiles", "nlsfiles", "sortfiles"],
            "requested_nls_not_in_sealed": [], "requested_nls_count": 76,
            "sealed_nls_count": 76, "copyfile_rows": 88,
            "resource_provider_count": 8,
            "resource_providers_in_sealed_pe": [],
            "resource_providers_not_in_sealed_pe": sorted(A.SOURCE_BLOBS),
        }
        self.assertEqual(A.validate_copyqueue_provider_list(valid),
                         set(A.SOURCE_BLOBS))
        invalid = (
            ("phone_accessed", True),
            ("rpcss_registration_declared", False),
            ("arm64_copy_sections", ["nlsfiles"]),
            ("requested_nls_not_in_sealed", ["missing.nls"]),
            ("requested_nls_count", True),
            ("requested_nls_count", 75),
            ("sealed_nls_count", 75),
            ("copyfile_rows", 0),
            ("resource_provider_count", 7),
            ("resource_providers_in_sealed_pe", ["mscms.dll"]),
            ("resource_providers_in_sealed_pe", ["foo.dll", "foo.dll"]),
            ("resource_providers_in_sealed_pe", "foo.dll"),
        )
        for field, value in invalid:
            bad = copy.deepcopy(valid)
            bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                A.validate_copyqueue_provider_list(bad)
        for field in ("phone_accessed", "rpcss_registration_declared",
                      "copyfile_rows", "resource_provider_count",
                      "requested_nls_count", "sealed_nls_count",
                      "resource_providers_in_sealed_pe"):
            bad = copy.deepcopy(valid)
            del bad[field]
            with self.subTest(missing=field), self.assertRaises(ValueError):
                A.validate_copyqueue_provider_list(bad)

    def test_copyqueue_json_rejects_duplicate_keys_even_if_last_value_is_safe(self):
        # The ordinary json.loads parser would silently retain the last
        # occurrence and report an apparently safe provenance flag.
        import json
        valid = {
            "source_only": True, "wine_executed": False, "v28_reused": False,
            "resource_providers_not_in_sealed_pe": sorted(A.SOURCE_BLOBS),
            "phone_accessed": False,
            "rpcss_registration_declared": True,
            "arm64_copy_sections": [
                "colorfiles", "etcfiles", "inffiles", "nlsfiles", "sortfiles"],
            "requested_nls_not_in_sealed": [],
            "requested_nls_count": 76,
            "sealed_nls_count": 76,
            "copyfile_rows": 88,
            "resource_provider_count": 8,
            "resource_providers_in_sealed_pe": [],
        }
        raw = json.dumps(valid)
        self.assertEqual(A.validate_copyqueue_provider_list(
            A.parse_copyqueue_json(raw)), set(A.SOURCE_BLOBS))
        for duplicate in (
            '"source_only": false,',
            '"wine_executed": true,',
            '"v28_reused": true,',
            '"resource_providers_not_in_sealed_pe": [],',
        ):
            with self.subTest(duplicate=duplicate), self.assertRaises(ValueError):
                A.parse_copyqueue_json("{" + duplicate + raw[1:])
        for invalid in ('{"source_only":NaN}', '{"source_only":Infinity}',
                        '[1,2,3]', 'null', '{"nested":{"a":1,"a":2}}'):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                A.parse_copyqueue_json(invalid)

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
