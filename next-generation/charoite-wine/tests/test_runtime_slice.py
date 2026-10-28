"""Contract tests for Charoite Wine experimental ABI-verified archive."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

WINE = Path(__file__).resolve().parents[1]


def load(filename, name):
    spec = importlib.util.spec_from_file_location(name, WINE / filename)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


packer = load("package-runtime-slice.py", "charoite_packer")
verifier = load("verify-runtime-slice.py", "charoite_verifier")


def fake_tool(*argv):
    if "--file-headers" in argv:
        return "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n"
    if "-h" in argv:
        return "ELF Header:\n  Machine: AArch64\n"
    if "-lW" in argv:
        return ("Program Headers:\n"
                "  LOAD 0x000000 0x000000 0x000000 0x001000 0x001000 R E 0x4000\n"
                "  LOAD 0x001000 0x001000 0x001000 0x001000 0x001000 RW  0x4000\n")
    if "-d" in argv:
        return "0x0000000000000001 (NEEDED) Shared library: [libc.so]\n"
    raise AssertionError(argv)


class SliceContract(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.source = root / "charoite-wine-prepared"
        self.source.mkdir()
        (self.source / "charoite-source-validation.txt").write_text("SOURCE VALIDATED")
        (self.source / "COPYING.LIB").write_text("GNU LGPL synthetic test notice")
        (self.source / "LICENSE").write_text("Synthetic Wine license notice")
        (self.source / "charoite-source-delta.patch").write_text(
            "diff --git a/server/token.c b/server/token.c\n"
            "--- a/server/token.c\n+++ b/server/token.c\n")
        self.build = self.source / "charoite-arm64ec-android"
        self.build.mkdir()
        for idx, (source, bundled, typ) in enumerate(packer.COMPONENTS.values()):
            dest = self.build / source
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(b"charoite-native-synthetic-unit-test-" + bytes([idx]) * 80)
        self.output = self.source / "charoite-runtime-slice"

    def tearDown(self):
        self.tmp.cleanup()

    def make_archive(self):
        with mock.patch.object(packer, "run", side_effect=fake_tool):
            return packer.package(self.build, self.output, "/fake/llvm-readelf",
                                  "/fake/llvm-readobj")

    def test_archive_keeps_engine_disabled(self):
        archive = self.make_archive()
        manifest = verifier.verify(archive)
        self.assertFalse(manifest["launch_ready"])
        self.assertFalse(manifest["installable"])
        self.assertEqual(set(manifest["components"]), set(packer.COMPONENTS))
        self.assertEqual(set(manifest["source_files"]), set(packer.SOURCE_FILES))
        self.assertEqual(manifest["source_reconstruction"]["upstream_commit"],
                         packer.SOURCE_SHA)
        self.assertEqual(manifest["components"]["ntdll_arm64ec"]["pe_machine"],
                         "0xA641")

    def test_refuses_overwrite(self):
        self.make_archive()
        with self.assertRaises(FileExistsError):
            self.make_archive()

    def test_rejects_bad_architecture(self):
        self.output.mkdir()
        with mock.patch.object(packer, "run", return_value="Machine: AArch64\n"):
            with self.assertRaises(ValueError):
                packer.build_manifest(self.build, "/fake/readelf", "/fake/readobj")

    def test_rejects_low_page_alignment(self):
        def low_alignment(*argv):
            if "-lW" in argv:
                return "  LOAD 0x00 0x00 0x00 0x10 0x10 R E 0x1000\n"
            return fake_tool(*argv)
        with mock.patch.object(packer, "run", side_effect=low_alignment):
            with self.assertRaisesRegex(ValueError, "alignment"):
                packer.build_manifest(self.build, "/fake/readelf", "/fake/readobj")

    def test_rejects_tampering_and_extra_paths(self):
        archive = self.make_archive()
        fake_archive = self.source / "bad.tar.gz"
        with tarfile.open(archive, "r:gz") as original:
            with tarfile.open(fake_archive, "w:gz") as target:
                for member in original.getmembers():
                    data = original.extractfile(member).read()
                    if member.name == "slice/lib/ntdll.so":
                        data = b"tampered" + data
                        member.size = len(data)
                    target.addfile(member, io.BytesIO(data))
        with self.assertRaisesRegex(ValueError, "Tampered"):
            verifier.verify(fake_archive)
        extra = self.source / "extra.tar.gz"
        with tarfile.open(archive, "r:gz") as original:
            with tarfile.open(extra, "w:gz") as target:
                for member in original.getmembers():
                    target.addfile(member, original.extractfile(member))
                unexpected = tarfile.TarInfo("slice/../../escape")
                unexpected.size = 3
                target.addfile(unexpected, io.BytesIO(b"bad"))
        with self.assertRaises(ValueError):
            verifier.verify(extra)

    def test_rejects_corrupted_source_delta(self):
        archive = self.make_archive()
        bad = self.source / "bad-source.tar.gz"
        with tarfile.open(archive, "r:gz") as original:
            with tarfile.open(bad, "w:gz") as target:
                for member in original.getmembers():
                    payload = original.extractfile(member).read()
                    if member.name == "source/charoite-source-delta.patch":
                        payload += b"corrupted patch"
                        member.size = len(payload)
                    target.addfile(member, io.BytesIO(payload))
        with self.assertRaisesRegex(ValueError, "Tampered Wine license/source"):
            verifier.verify(bad)


if __name__ == "__main__":
    unittest.main()
