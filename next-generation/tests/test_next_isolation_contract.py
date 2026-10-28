"""Static safety and identity tests for the side-by-side Charoite Core Next APK."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
NEXT = ROOT / "next-generation"
STABLE = ROOT / "runtime-preview"


class NextEditionContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prepare = (NEXT / "prepare_next.py").read_text()
        cls.rewriter = (NEXT / "rewrite_prefix_next.py").read_text()
        cls.engine = (NEXT / "CharoiteNextRuntime.java").read_text()
        cls.workflow = (ROOT / ".github/workflows/charoite-next.yml").read_text()
        cls.stable_workflow = (ROOT / ".github/workflows/runtime-preview.yml").read_text()
        cls.references = json.loads((NEXT / "engine-reference.json").read_text())

    def test_stable_android_id_is_preserved(self):
        self.assertIn("applicationId 'com.charoite'", (STABLE / "overlay.py").read_text())
        self.assertIn("com.charoitx", self.prepare)
        self.assertNotIn("applicationId 'com.charoitx'", (STABLE / "overlay.py").read_text())
        self.assertIn("package: name='com.charoite'", self.stable_workflow)

    def test_new_identity_has_fixed_elf_safe_length(self):
        self.assertIn('module.TARGET = b"com.charoitx"', self.rewriter)
        self.assertIn("len(module.ORIGINAL) == len(module.TARGET) == 12", self.rewriter)
        self.assertIn("com.charoitx.FileProvider", self.prepare)
        self.assertIn("applicationId 'com.charoitx'", self.prepare)

    def test_new_edition_signed_by_separate_key(self):
        self.assertIn("charoite-next.keystore", self.workflow)
        self.assertIn("charoite-next-debug-signing-v1", self.workflow)
        self.assertIn("charoite-next.keystore", self.prepare)
        self.assertIn("~/.android/debug.keystore", self.stable_workflow)
        self.assertNotIn("charoite-next.keystore", self.stable_workflow)

    def test_next_binaries_and_artifacts_are_separate(self):
        self.assertIn("Charoite-Core-Next-Android-APK", self.workflow)
        self.assertIn("Charoite-Next-Android.apk", self.workflow)
        self.assertIn("python3 next-generation/rewrite_prefix_next.py upstream", self.workflow)
        self.assertIn("python3 next-generation/prepare_next.py upstream", self.workflow)
        self.assertIn("application-label:'Charoite Next'", self.workflow)
        self.assertIn("package: name='com.charoitx'", self.workflow)
        self.assertIn("Charoite-Portal-Android-APK", self.stable_workflow)

    def test_modern_runtime_fails_closed(self):
        self.assertIn('PROTON_ARM64EC_FEX = "proton-arm64ec-fex"', self.engine)
        self.assertIn("false, false", self.engine)
        self.assertIn("hash/ABI", self.engine)
        self.assertIn("public static boolean mayLaunch", self.engine)
        engines = {x["id"]: x for x in self.references["runtimes"]}
        self.assertFalse(engines["proton-arm64ec-fex"]["runnableInThisPrototype"])
        self.assertFalse(engines["wine-staging-box64"]["runnableInThisPrototype"])

    def test_no_anti_cheat_bypass_and_no_prefix_migration(self):
        self.assertIn("no evasion", self.references["compliance"]["antiCheat"])
        self.assertIn("Never patch or migrate existing", self.references["compliance"]["gameData"])
        for forbidden in ("deleteRecursively", "rm -rf", "antiCheatDisable",
                          "kernelBypass", "rootDevice", "cheatBypass"):
            self.assertNotIn(forbidden, self.prepare + self.engine)


if __name__ == "__main__":
    unittest.main()
