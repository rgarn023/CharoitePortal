"""Source-built ARM64 services.exe v7 packaging & one-shot isolation contract.

'verifiedV7' is the explicit CI marker for this private-prefix cohort.
Historical v6 scratch and logs must remain untouched.
"""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
JAVA=(BASE/"CharoiteWine29V7ServicesProbe.java").read_text()
STAGE=(BASE/"stage_wine29_v7_services.py").read_text()
UI=(BASE/"prepare_next.py").read_text()
WF=(BASE.parent/".github/workflows/charoite-next.yml").read_text()

class V7SourceBuiltServicesContract(unittest.TestCase):
    def test_source_pinned_artifact_and_executable_verified_before_new_scratch(self):
        for text in (
            "f32a3563254b2ae6447d6cf2e6639be3e7e6d9d9",
            "42409561051", "13589325323", "fba183ee44a632c2e45608dace22ce71108129882e2854fd51bf077c04247a34",
            'ROOT = "charoite-next/wine29-v7-services"',
            'INDEX = ROOT + "/services-index.json"',
            "services-arm64.exe.bin", 'pe_machine', '0xAA64',
            "stage_wine29_v7_services.py",
            "previous_sealed_111_unchanged", "prior_v6_native_cohort_unchanged",
            "Refusing to overwrite v7 services APK asset",
            "WINE29_V7_SOURCE_BUILT_ARM64_SERVICES_APK_DATA=PASS"
        ):
            with self.subTest(text=text):
                self.assertIn(text, STAGE if text!="services-arm64.exe.bin" else STAGE+JAVA)

    def test_read_only_preflight_before_new_v7_scratch_and_no_history(self):
        for text in (
            'charoite-next-wine29-services-v7',
            'verifyV6Native(context);',
            'verifyV7Services(context);',
            'source_build_commit', 'source_artifact_digest',
            'serviceBuiltin=child(lib,"services.exe")',
            'V7 source-matched services.exe copied beside Wineboot/kernel32: SHA-256 PASS',
            'V7 one-shot scratch retained; NEVER rerun/delete v7',
            'v7-wine-direct-init.log','v7-foreground-wineserver.log',
            'source-built ARM64 services.exe APK SHA-256/PE header',
            'V7 services.exe is not Windows ARM64 PE AA64'
        ):
            with self.subTest(text=text):
                self.assertIn(text, JAVA)
        self.assertLess(JAVA.index('verifyV7Services(context);'), JAVA.index('scratch = child(privateBase, SCRATCH);'))
        self.assertNotIn('charoite-next-wine29-child-loader-v6', JAVA)
        for forbidden in ("Runtime.getRuntime()", 'clearApplicationUserData(', 'delete(', 'renameTo(', 'env.put("WINEBOOTSTRAPMODE"', 'getSharedPreferences('):
            self.assertNotIn(forbidden, JAVA)

    def test_manual_new_v7_confirmation_archives_old_v6_action(self):
        for text in (
            '"CharoiteWine29V7ServicesProbe.java"',
            'final boolean showArchivedWine29V6ReadOnly = false;',
            'Test Wine29 v7 services.exe bootstrap (one-shot)',
            'Authorize ONE v7 test',
            'Cancel — do not execute',
            'CharoiteWine29V7ServicesProbe.run(this)',
            'nextCoreCard.addView(wine29V7Services);',
            'versionCode 134','11.2-next.0.103',
        ):
            self.assertIn(text, UI)
        self.assertNotIn('CharoiteWine29V7ServicesProbe.run(this)',
                         UI.split("wine29V7Services.setOnClickListener",1)[0])
    def test_ci_apk_hash_gate_and_licenses(self):
        for text in (
            'stage_wine29_v7_services.py',
            'WINE29_V7_SOURCE_VERIFIED_SERVICES_APK_STAGE=PASS',
            'WINE29_V7_ONE_SHOT_SERVICES_CONSENT_AND_ISOLATION=PASS',
            'WINE29_V7_SIGNED_APK_SOURCE_BUILT_ARM64_SERVICES_SHA256=PASS',
            'WINE29_V7_PREVIOUS_V6_NATIVE_SEALED_111_UNCHANGED=PASS',
            "versionCode='134' versionName='11.2-next.0.103'",
            'cp next-generation/CharoiteWine29V7ServicesProbe.java legal-bundle/CharoiteWine29V7ServicesProbe.java'
        ):
            self.assertIn(text, WF)

if __name__ == "__main__":
    unittest.main()
