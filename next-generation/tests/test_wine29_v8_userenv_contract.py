"""Wine29 v8 source-built userenv.dll one-shot must preserve all v7 runtime data."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
STAGE=(ROOT/"stage_wine29_v8_userenv.py").read_text()
JAVA=(ROOT/"CharoiteWine29V8UserenvProbe.java").read_text()
UI=(ROOT/"prepare_next.py").read_text()
WF=(ROOT.parent/".github/workflows/charoite-next.yml").read_text()

class Wine29V8SourceUserenvContract(unittest.TestCase):
    def test_pinned_source_verified_before_any_scratch(self):
        for token in (
            "42419386776", "523e66511a3504f0705eee508c0fc935999dca2f",
            "13593275372", "524ed4e41b418095c8cb546e31f0754522ce6c3b8501c643feea826c661fc887",
            'ROOT = "charoite-next/wine29-v8-userenv"',
            "userenv-arm64.dll.bin", "userenv-manifest.json",
            "COFF-ARM64X", "0xA64E", "0xAA64",
            "ordinary_imports_unbundled_after_candidate",
            "all_unbundled_after_candidate",
            "previous_sealed_111_unchanged", "prior_v7_services_unchanged",
            "WINE29_V8_SOURCE_VERIFIED_USERENV_APK_STAGE=PASS",
            "Refusing to overwrite another v8 APK candidate",
        ):
            with self.subTest(token=token): self.assertIn(token, STAGE)
        self.assertNotIn("ProcessBuilder", STAGE)
        self.assertNotIn("wineboot -i", STAGE)

    def test_verified_dll_and_prior_services_before_fresh_v8_creation(self):
        for token in (
            "charoite-next-wine29-userenv-v8", "verifyV6Native(context);",
            "verifyV7Services(context);", "verifyV8Userenv(context);",
            'userenvBuiltin=child(lib,"userenv.dll")',
            'serviceBuiltin=child(lib,"services.exe")',
            "V8 verified userenv.dll copied beside services/kernel32",
            "v8-wine-direct-init.log","v8-foreground-wineserver.log",
            "V8 one-shot scratch retained", "NO retry",
        ):
            with self.subTest(token=token): self.assertIn(token, JAVA)
        self.assertLess(JAVA.index("verifyV8Userenv(context);"),JAVA.index("scratch = child(privateBase, SCRATCH);"))
        for forbidden in (
            'charoite-next-wine29-services-v7', "clearApplicationUserData(",
            "getSharedPreferences(", ".delete(", "renameTo(", "Runtime.getRuntime("
        ):
            with self.subTest(forbidden=forbidden): self.assertNotIn(forbidden, JAVA)

    def test_current_one_shot_control_and_version(self):
        for token in (
            '"CharoiteWine29V8UserenvProbe.java"',
            'showArchivedWine29V7ReadOnly = false;',
            "Test Wine29 v8 userenv.dll services bootstrap (one-shot)",
            "Authorize ONE v8 test", "Cancel — do not execute",
            "CharoiteWine29V8UserenvProbe.run(this)",
            "nextCoreCard.addView(wine29V8Userenv);",
            "versionCode 139", "11.2-next.0.108",
        ):
            with self.subTest(token=token): self.assertIn(token, UI)

    def test_final_ci_provenance_and_apk(self):
        for token in (
            "stage_wine29_v8_userenv.py",
            "WINE29_V8_PINNED_USERENV_APK_DATA_STAGE=PASS",
            "WINE29_V8_PINNED_USERENV_CONSENT_AND_NEW_SCRATCH=PASS",
            "WINE29_V8_SIGNED_APK_SOURCE_BUILT_USERENV_SHA256=PASS",
            "WINE29_V8_V7_SERVICES_V6_NATIVE_111_SEALED_PRESERVED=PASS",
            "cp next-generation/CharoiteWine29V8UserenvProbe.java legal-bundle/CharoiteWine29V8UserenvProbe.java",
            "versionCode='139' versionName='11.2-next.0.108'",
        ):
            with self.subTest(token=token): self.assertIn(token, WF)

if __name__=="__main__": unittest.main()
