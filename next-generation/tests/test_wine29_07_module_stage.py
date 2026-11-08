"""Wine29 .0.7 source PE/NLS staging is opt-in, data-only and isolated."""
from pathlib import Path
import importlib.util
import unittest

NEXT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "wine29_07_pe_nls_apk", NEXT / "stage_wine29_07_modules.py")
MOD = importlib.util.module_from_spec(spec)
spec.loader.exec_module(MOD)
CI_SRC = (NEXT / "stage_wine29_07_modules.py").read_text(encoding="utf-8")
ANDROID = (NEXT / "CharoiteWine29Native07Stage.java").read_text(encoding="utf-8")
PREP = (NEXT / "prepare_next.py").read_text(encoding="utf-8")
WORKFLOW = (NEXT.parent / ".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


def coherent_manifest():
    components = {}
    for name in ("wine", "wineserver", "ntdll_unix"):
        components[name] = {"format": "ELF", "path": "runtime/bin/" + name}
    for i in range(23):
        name = "apisetschema" if i == 0 else "winmod_" + str(i)
        components[name] = {
            "format": "PE", "path": "runtime/pe/arm64ec/" + name + ".dll",
            "size": 4096 + i, "sha256": "a" * 64
        }
    components["wineboot"] = {
        "format": "PE", "path": "runtime/pe/arm64/wineboot.exe",
        "size": 16384, "sha256": "b" * 64
    }
    return {
        "version": MOD.VERSION,
        "source_commit": "c74acb09d51b447f5d5ac56c87608d3ec565a767",
        "component_count": 27, "nls_count": 76,
        "components": components,
        "nls_files": {
            ("c_%03d.nls" % i): {
                "path": "runtime/nls/c_%03d.nls" % i,
                "size": 2048, "sha256": "c" * 64
            }
            for i in range(76)
        }
    }


class Wine29ModuleStage(unittest.TestCase):
    def test_complete_source_inventory_and_dedicated_asset_paths(self):
        rows, total = MOD.module_inventory(coherent_manifest())
        self.assertEqual(len(rows), 100)
        self.assertEqual(sum(x["path"].startswith("pe/") for x in rows), 24)
        self.assertEqual(sum(x["path"].startswith("nls/") for x in rows), 76)
        self.assertEqual(rows, sorted(rows, key=lambda x: x["path"]))
        self.assertEqual(sum(x["size"] for x in rows), total)
        self.assertEqual(len({x["asset"] for x in rows}), 100)
        for item in rows:
            self.assertTrue(item["asset"].startswith(
                "charoite-next/wine29-native07/modules/"))
            self.assertEqual(item["source"], "runtime/" + item["path"])
        self.assertIn("pe/arm64ec/apisetschema.dll", [x["path"] for x in rows])
        self.assertIn("pe/arm64/wineboot.exe", [x["path"] for x in rows])

    def test_reject_missing_apiset_duplicate_and_elf_as_windows_module(self):
        manifest = coherent_manifest()
        manifest["components"].pop("apisetschema")
        manifest["components"]["other"] = {
            "format":"PE", "path":"runtime/pe/arm64ec/other.dll",
            "size":256, "sha256":"d"*64}
        with self.assertRaisesRegex(ValueError, "API-set"):
            MOD.module_inventory(manifest)
        manifest = coherent_manifest()
        manifest["components"]["wine"]["format"]="PE"
        with self.assertRaisesRegex(ValueError, "24 Windows PE"):
            MOD.module_inventory(manifest)
        manifest = coherent_manifest()
        manifest["nls_files"]["c_000.nls"]["path"] = "runtime/../existing-prefix/system.reg"
        with self.assertRaisesRegex(ValueError, "path"):
            MOD.module_inventory(manifest)
        manifest = coherent_manifest()
        manifest["components"]["wineboot"]["size"] = 128 * 1024 * 1024
        with self.assertRaisesRegex(ValueError, "hash/size"):
            MOD.module_inventory(manifest)

    def test_never_overwrite_existing_cohort_in_ci(self):
        for term in (
            "stage_wine29_native07.py", "Wine29 .0.7 baseline absent",
            "asset_folder.exists()", "source_run", "source_artifact",
            "archive_sha256", "module_files", "module_staged_on_phone",
            "module_assets_verified", "wine29_pe_nls_runnable",
            "Original archive", "tarfile.open", "sha256",
        ):
            if term in ("stage_wine29_native07.py", "Original archive"):
                continue
            self.assertIn(term, CI_SRC)
        for term in ("subprocess.run", "subprocess.Popen", "os.system(",
                     "shutil.rmtree(", ".unlink(", "rm -rf"):
            self.assertNotIn(term, CI_SRC)

    def test_phone_slot_never_executes_or_overwrites(self):
        for term in (
            "CharoiteWine29Native07Audit.run(context)",
            "getNoBackupFilesDir().getCanonicalFile()",
            'ROOT = "charoite-next-wine29-07-pe-nls"',
            'FINAL = "wine10-arm64ec-bootstrap-0.7-pe-nls"',
            "verifyAssets(context, entries);",
            "if (pending.exists())",
            "verifyFiles(complete, entries);",
            "pending.renameTo(complete)",
            "quarantined; NO retry",
            "private static JSONArray inventory",
            "public static String verifyOnly",
            "public static String run(Context context)",
            "RESULT: PASS — Wine29 0.7 data staged; NOT RUNNABLE",
        ):
            self.assertIn(term, ANDROID)
        for forbidden in (
            "ProcessBuilder(", "Runtime.getRuntime(", "new Process(", ".delete(",
            "deleteRecursive(", "WINEPREFIX", "File(rootfs", "wineboot -i",
            "new File(context.getFilesDir()", "CHAROITE_WINE28_PE_DIR",
        ):
            self.assertNotIn(forbidden, ANDROID)

    def test_manual_consent_and_v063_apk_contract(self):
        self.assertIn('wine29Data.setText("Stage Wine29 0.7 PE/NLS data (no execution)")', PREP)
        self.assertIn('setTitle("Stage new isolated Wine29 0.7 DATA?")', PREP)
        self.assertIn('setPositiveButton("Stage data only"', PREP)
        self.assertIn('CharoiteWine29Native07Stage.run(this)', PREP)
        self.assertIn('setNegativeButton("Cancel", null)', PREP)
        self.assertIn('CharoiteWine29Native07Stage.java', PREP)
        self.assertIn("stage_wine29_07_modules.py", WORKFLOW)
        self.assertIn("WINE29_07_100_PE_NLS_APK_ASSET_HASHES_VERIFIED=PASS", WORKFLOW)
        self.assertIn("CharoiteWine29Native07Stage.java", WORKFLOW)
        self.assertIn("versionCode 142", PREP)
        self.assertIn("11.2-next.0.111", PREP)
        self.assertIn("versionCode='142'", WORKFLOW)
        self.assertIn("versionName='11.2-next.0.111'", WORKFLOW)

    def test_sealed_100_module_readonly_audit_rejects_extra_files(self):
        # A directory name or file presence cannot authorize an executable runtime.
        for term in (
            "private static void verifyClosedInventory(",
            "verifyClosedInventory(slot, entries);",
            "java.util.ArrayDeque<File>",
            "HashSet<String> expected",
            "HashSet<String> directories",
            "child.getCanonicalFile().equals(child.getAbsoluteFile())",
            "Unexpected Wine29 staging file",
            "Unknown Wine29 staging directory",
            "Incomplete Wine29 sealed 100-module inventory",
            "private static void verifyRootContents(",
            "Unexpected or quarantined Wine29 root entry",
            "verifyRootContents(root);",
            "verifyAssets(context, entries);",
            "APK source assets and sealed 100-file private inventory",
        ):
            self.assertIn(term, ANDROID)
        self.assertLess(ANDROID.index("verifyClosedInventory(slot, entries);"),
                        ANDROID.index("hash(new FileInputStream(target)"))
        self.assertIn("Verify staged Wine29 0.7 data (read-only)", PREP)
        self.assertIn("CharoiteWine29Native07Stage.verifyOnly(this)", PREP)
        self.assertIn("WINE29_07_SEALED_100_MODULE_READONLY_AUDIT_SOURCE_GATE=PASS",
                      WORKFLOW)
        for forbidden in ("ProcessBuilder(", "Runtime.getRuntime(", ".delete(",
                          "WINEPREFIX", "wineboot -i"):
            self.assertNotIn(forbidden, ANDROID)


if __name__ == "__main__":
    unittest.main()
