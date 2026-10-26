"""Charoite Portal clean-install application ID and ELF-path safety contracts."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
REWRITE = (ROOT / "rewrite_prefix.py").read_text()
OVERLAY = (ROOT / "overlay.py").read_text()
WORKFLOW = (ROOT.parent / ".github/workflows/runtime-preview.yml").read_text()

class CleanCharoitePackageContract(unittest.TestCase):
    def test_native_identifier_length(self):
        old = "com.winlator"
        new = "com.charoite"
        self.assertEqual(len(old), len(new))
        self.assertEqual(len(new), 12)
        self.assertIn('ORIGINAL = b"com.winlator"', REWRITE)
        self.assertIn('TARGET = b"com.charoite"', REWRITE)
        self.assertIn('assert len(ORIGINAL) == len(TARGET)', REWRITE)
        self.assertIn('link.replace("com.winlator", "com.charoite")', REWRITE)
        self.assertNotIn("com.touhoudr", REWRITE)

    def test_portal_package_provider_and_native_sources(self):
        self.assertIn('"applicationId \'com.charoite\'"', OVERLAY)
        self.assertIn('com.charoite.FileProvider', OVERLAY)
        self.assertIn('b"/data/data/com.charoite"', OVERLAY)
        self.assertNotIn("com.touhoudr", OVERLAY)
        # Historical JNI Java class namespace remains to preserve ABI.
        self.assertIn('JNI entrypoints retain the com.winlator Java package', OVERLAY)

    def test_signing_build_and_apk_identity(self):
        self.assertIn("package: name='com.charoite'", WORKFLOW)
        self.assertIn("b'/data/data/com.charoite/files/rootfs/lib/", WORKFLOW)
        self.assertIn("b'/data/data/com.touhoudr/' not in box64", WORKFLOW)
        self.assertIn('outdated in content:', WORKFLOW)

if __name__=="__main__":
    unittest.main()
