"""Strict opt-in, no-prefix, native-only Wine29 .0.7 version proof contract."""
import re
from pathlib import Path
import unittest

NEXT=Path(__file__).resolve().parents[1]
GATE=(NEXT/"CharoiteWine29Native07VersionGate.java").read_text(encoding="utf-8")
AUDIT=(NEXT/"CharoiteWine29Native07Audit.java").read_text(encoding="utf-8")
PREP=(NEXT/"prepare_next.py").read_text(encoding="utf-8")
RUNTIME=(NEXT/"CharoiteNextRuntime.java").read_text(encoding="utf-8")
WORKFLOW=(NEXT.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")


class Wine29VersionGateContract(unittest.TestCase):
    def test_exact_source_and_new_apk_identity_only(self):
        for text in ("com.charoitx", "wine10-arm64ec-bootstrap.0.7",
                     "41749167248", "13284932342",
                     "libcharoite_wine29_loader.so",
                     "libcharoite_wine29_wineserver.so",
                     "libcharoite_wine29_ntdll.so",
                     "CharoiteWine29Native07Audit.run(context)",
                     "source_native_cohort_verified",
                     "native_elf_installed_as_apk_libs",
                     "source_run", "source_artifact",
                     "getApplicationInfo().nativeLibraryDir",
                     "source/"): # source/ in source-comment? replaced below
            if text == "source/":
                continue
            self.assertIn(text,GATE)
        self.assertIn("original_wine29_sha256",AUDIT)
        self.assertIn("wine29-source-matched.bundle",GATE)
        self.assertIn("JSONObject components = index.getJSONObject",GATE)

    def test_native_execution_requires_user_button_confirmation(self):
        self.assertIn("Test Wine29 0.7 native --version (no prefix)",PREP)
        self.assertIn("Confirm Wine29 version-only test?",PREP)
        self.assertIn("Run version-only test",PREP)
        self.assertIn("CharoiteWine29Native07VersionGate.run(this)",PREP)
        self.assertIn(".setNegativeButton(\"Cancel\", null)",PREP)
        self.assertIn("wine29Version.setEnabled(false);",PREP)
        self.assertNotIn("CharoiteWine29Native07VersionGate.run(this);", PREP.split("wine29Version.setOnClickListener")[0])
        self.assertIn("CharoiteWine29Native07VersionGate.java",PREP)

    def test_only_fixed_binary_argv_and_clean_environment(self):
        self.assertEqual(GATE.count('new ProcessBuilder(binary.getAbsolutePath(), "--version")'),1)
        self.assertIn("env.clear();",GATE)
        self.assertIn('env.put("CHAROITE_WINE29_NATIVE_DIR", apkNative)',GATE)
        self.assertIn('env.put("CHAROITE_WINE29_PE_DIR", apkNative)',GATE)
        self.assertIn('env.put("CHAROITE_WINE29_DATA_DIR", apkNative)',GATE)
        self.assertIn('Native version-only directory unexpectedly contains PE/NLS files',GATE)
        self.assertIn('PE/NLS runtime NOT staged',GATE)
        self.assertIn("waitFor(TIMEOUT_SECONDS, TimeUnit.SECONDS)",GATE)
        self.assertIn("process.destroyForcibly();",GATE)
        self.assertIn("new File(directory, filename)",GATE)
        self.assertIn("binary.length() != rec.getLong(\"size\")",GATE)
        self.assertIn('!sha(binary).equals(rec.getString("sha256"))',GATE)
        self.assertIn('exact.equals(output)',GATE)
        self.assertIn('"wine-10.0"',GATE)
        self.assertIn('"Wine 10.0"',GATE)
        for forbidden in ('env.put("WINEPREFIX"', 'env.put("HOME"',
                          'env.put("CHAROITE_WINE28_', "Runtime.getRuntime()",
                          "FileOutputStream(", "FileWriter(", "mkdir(", "mkdirs(",
                          "delete(", "renameTo(", "ProcessBuilder(\"sh\"",
                          'new ProcessBuilder("wineboot"', '"--help"'):
            self.assertNotIn(forbidden,GATE)
        self.assertIn('Wineboot, PE/Windows EXE, prefix, graphics, FEX, games: NOT ATTEMPTED',GATE)

    def test_source_requires_complete_triad_before_native_dlopen(self):
        source=(NEXT/"charoite-wine/prepare-wine29-native.py").read_text(encoding="utf-8")
        self.assertIn("if (!native29 || !pe29 || !data29 ||", source)
        self.assertIn("Wine29/Wine28 selector conflict or invalid native directory", source)
        start=GATE.index("private static String version(")
        end=GATE.index("public static String run(",start)
        version=GATE[start:end]
        self.assertIn("final String apkNative = nativeDir.getCanonicalPath();",version)
        self.assertIn('new File(nativeDir, "ntdll.dll").exists()', version)
        self.assertIn('new File(nativeDir, "apisetschema.dll").exists()', version)
        self.assertIn('new File(nativeDir, "nls").exists()', version)
        for selector in ("NATIVE","PE","DATA"):
            literal='env.put("CHAROITE_WINE29_'+selector+'_DIR", apkNative)'
            self.assertEqual(version.count(literal), 1)
            self.assertLess(version.index(literal),version.index("process = builder.start();"))
        self.assertEqual(version.count("process = builder.start();"),1)
        self.assertNotIn('env.put("WINEPREFIX"',version.split("process = builder.start();")[0].split("env.clear();")[1])
        self.assertNotIn("wineboot.exe",version)

    def test_fail_closed_if_immutable_audit_or_any_native_hash_fails(self):
        self.assertIn("if (!audit.contains(",GATE)
        self.assertIn("prerequisite Wine29 APK audit not passed",GATE)
        self.assertIn('verifyElf(directory, components, "ntdll_unix"',GATE)
        self.assertIn("Three APK-native Wine29 ELF hashes: REVERIFIED PASS",GATE)
        self.assertIn("nativeLibraryDir",GATE)
        self.assertIn("!binary.canExecute()",GATE)
        self.assertIn("MAX_ELF",GATE)
        self.assertIn("MAX_OUTPUT",GATE)
        self.assertIn("Unbounded Wine29 version output",GATE)
        self.assertIn("RESULT: BLOCKED",GATE)
        self.assertIn("NOT RUNNABLE",GATE)

    def test_apk_build_and_read_only_button_retained(self):
        self.assertIn("versionCode 128",PREP)
        self.assertIn("11.2-next.0.97",PREP)
        self.assertIn("Experimental Wine29 v10 PE-entry diagnostic; SCM not verified",RUNTIME)
        self.assertIn("versionCode='128'",WORKFLOW)
        self.assertIn("versionName='11.2-next.0.97'",WORKFLOW)
        self.assertIn("CharoiteWine29Native07VersionGate.java",WORKFLOW)
        self.assertIn('wine29Audit.setText("Verify Wine29 0.7 package (read-only)")',PREP)
        self.assertIn("WINE29_07_PHONE_WINE_EXECUTION=NOT_ATTEMPTED",WORKFLOW)


if __name__=="__main__":
    unittest.main()
