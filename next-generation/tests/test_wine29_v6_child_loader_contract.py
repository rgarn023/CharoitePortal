"""Wine29 v6 must use an isolated, native-SHA-verified, opt-in one-shot path."""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
JAVA=(BASE/"CharoiteWine29V6ChildLoaderProbe.java").read_text(encoding="utf-8")
UI=(BASE/"prepare_next.py").read_text(encoding="utf-8")
STAGE=(BASE/"stage_wine29_v6_native.py").read_text(encoding="utf-8")
WF=(BASE.parent/".github/workflows/charoite-next.yml").read_text(encoding="utf-8")

class Wine29V6ChildLoaderContract(unittest.TestCase):
    def test_new_private_prefix_and_native_preflight_before_execution(self):
        for token in (
            'charoite-next-wine29-child-loader-v6', 'private static final String PACKAGE = "com.charoitx"',
            'CharoiteWine29Sealed012PePreflight.run(context)',
            'CharoiteWine29Sealed012Stage.verifyOnly(context)',
            'verifyV6Native(context);',
            'V6 APK-native loader/NTDLL/wineserver hashes: PASS',
            'index.getJSONObject("native_files")',
            'Os.lstat(file.getAbsolutePath())',
            'MessageDigest.getInstance("SHA-256")',
            'new ProcessBuilder(server.getAbsolutePath(),"-f","-d")',
            'bootBuiltin.getAbsolutePath(),"-i"',
            'env.put("CHAROITE_WINE29_V6_NATIVE_DIR", nativeDir.getCanonicalPath())',
            'env.put("CHAROITE_WINE29_V6_LOADER_EXEC", childLoader.getCanonicalPath())',
            'env.put("CHAROITE_WINE29_V6_PE_DIR", library.getCanonicalPath())',
            'env.put("CHAROITE_WINE29_V6_DATA_DIR", dataDir.getCanonicalPath())',
            'CHAROITE_WINE29_V6_CHILD_EXECV_FAILURE',
            'Os.symlink("../drive_c",link.getAbsolutePath())',
            'serverProc.destroyForcibly()', 'peProc.destroyForcibly()',
            'NEVER rerun/delete v6',
        ):
            with self.subTest(token=token):
                self.assertIn(token,JAVA)
        self.assertLess(JAVA.index('verifyV6Native(context);'),JAVA.index('scratch = child(privateBase, SCRATCH);'))
        for forbidden in (
            'charoite-next-wine29-c-drive-v5', 'charoite-next-wine29-direct-init-v4',
            'charoite-next-wine29-pe-dir-v3', 'charoite-next-wine29-bootstrap-v2',
            'env.put("WINEBOOTSTRAPMODE"', 'Runtime.getRuntime()', '.delete(',
        ):
            self.assertNotIn(forbidden,JAVA)

    def test_ui_requires_new_explicit_confirmation_and_archives_v5(self):
        for token in (
            '"CharoiteWine29V6ChildLoaderProbe.java"',
            'final boolean showArchivedWine29V5Execution = false;',
            'wine29V6Child.setText("Wine29 v6 native child-loader smoke (one-shot)")',
            'setNegativeButton("Cancel — do not execute", null)',
            'setPositiveButton("Authorize ONE new v6 test"',
            'CharoiteWine29V6ChildLoaderProbe.run(this)',
            'nextCoreCard.addView(wine29V6Child);',
            '11.2-next.0.92', 'versionCode 123',
        ):
            self.assertIn(token, UI)
        self.assertNotIn('CharoiteWine29V6ChildLoaderProbe.run(this)',
                         UI.split('wine29V6Child.setOnClickListener(v ->')[0])

    def test_apk_native_generation_is_pinned_non_overwriting(self):
        for token in (
            'SOURCE_REV = "c74acb09d51b447f5d5ac56c87608d3ec565a767"',
            'SOURCE_ARTIFACT_DIGEST', 'native-sha256.txt',
            'source-patch-evidence.json', 'modified_files',
            'libcharoite_wine29_v6_loader.so',
            'libcharoite_wine29_v6_ntdll.so',
            'libcharoite_wine29_v6_wineserver.so',
            'min(aligns) < 16384', 'sha256',
            'Refusing v6 native cohort overwrite',
            'Original Wine29 ELF was modified',
            '"launch_ready": False',
        ):
            self.assertIn(token, STAGE)

    def test_ci_has_separate_gate_and_license(self):
        for token in (
            'test_wine29_v6_child_loader_contract.py',
            'WINE29_V6_NATIVE_CHILD_LOADER_ONE_SHOT_CONSENT=PASS',
            'cp next-generation/CharoiteWine29V6ChildLoaderProbe.java legal-bundle/CharoiteWine29V6ChildLoaderProbe.java',
            "versionCode='123' versionName='11.2-next.0.92'",
        ):
            self.assertIn(token,WF)

if __name__=="__main__":
    unittest.main()
