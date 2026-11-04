"""Wine29 compiled-native verification is fail-closed and does not start Wine."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT/"verify-wine29-native-compile.py"
spec = importlib.util.spec_from_file_location("wine29_compile", SCRIPT)
M = importlib.util.module_from_spec(spec)
spec.loader.exec_module(M)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def build_fixture(root: Path) -> tuple[Path, Path, Path]:
    source = root/"source"
    build = source/"charoite-arm64ec-android"
    build.mkdir(parents=True)
    patched_hashes = {}
    for rel in ("loader/main.c", "dlls/ntdll/unix/loader.c", "server/unicode.c"):
        dest=source/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        data=(rel+" Wine29 isolated source").encode()
        dest.write_bytes(data)
        patched_hashes[rel]={"before_sha256":"0"*64, "after_sha256":sha(data)}
    delta=b"isolated source delta for tests"
    (source/"charoite-wine29-native-source-delta.patch").write_bytes(delta)
    proof={"generation":M.GENERATION,"source_commit":M.SOURCE_COMMIT,
           "package":"com.charoitx","runtime_executable":False,
           "device_tested":False,"native_elf_installed":False,
           "legacy_wine28_cohort_modified":False,
           "delta_sha256":sha(delta),"patch_sources":patched_hashes}
    (source/"charoite-wine29-native-source-validation.json").write_text(json.dumps(proof))
    (source/"charoite-source-validation.txt").write_text("SOURCE VALIDATED")
    for name,(rel,markers) in M.BINARIES.items():
        data=bytearray(64); data[:6]=b"\x7fELF\x02\x01"
        struct.pack_into("<H",data,18,183)
        for marker in markers:data.extend(marker.encode()+b"\x00")
        target=build/rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    pe=build/M.WINDOWS_NTDLL
    pe.parent.mkdir(parents=True, exist_ok=True)
    pe.write_bytes(b"MZ"+bytes(64))
    readelf=root/"readelf"; readobj=root/"readobj"
    readelf.write_text("tool");readobj.write_text("tool")
    return source, readelf, readobj


def mock_command(_tool, *args):
    if args[0]=="-h":return "  Machine: AArch64\n"
    if args[0]=="-lW":return "  LOAD 0x0000 0x0000 0x0000 0x00010000 0x00010000 R E 0x4000\n"
    if args[0]=="-dW":return " 0x00000001 (NEEDED) Shared library: [libc.so]\n"
    if args[0]=="--file-headers":return "Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n"
    raise RuntimeError("Unexpected binary inspector invocation")


class Wine29NativeCompileContract(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.source,self.readelf,self.readobj=build_fixture(self.root)

    def tearDown(self):self.temp.cleanup()

    def run_check(self):
        with patch.object(M,"command",side_effect=mock_command):
            return M.verify_native(self.source/"charoite-arm64ec-android",
                                   self.readelf,self.readobj,self.source)

    def test_source_coherent_four_compiled_components(self):
        report=self.run_check()
        self.assertEqual(report["source_generation"], M.GENERATION)
        self.assertEqual(set(report["components"]),{"wine","wineserver","ntdll_unix","ntdll_windows"})
        self.assertFalse(report["new_27_component_archive_verified"])
        for field in ("launch_ready","native_elf_installed","device_tested",
                      "wineboot_executed","prefix_created","anti_cheat_supported"):
            self.assertFalse(report[field])

    def test_refuses_old_loader_and_cross_generation_native(self):
        wine=self.source/"charoite-arm64ec-android/loader/wine"
        wine.write_bytes(wine.read_bytes().replace(b"libcharoite_wine29_ntdll.so",
                                                  b"libcharoite_wine28_ntdll.so"))
        with self.assertRaisesRegex(ValueError,"source selector missing"):
            self.run_check()
        wine.write_bytes(b"\x7fELF\x02\x01"+bytes(50))
        with self.assertRaisesRegex(ValueError,"AArch64 ELF"):
            self.run_check()

    def test_refuses_modified_source_and_tampered_delta(self):
        path=self.source/"server/unicode.c"
        path.write_text("altered source")
        with self.assertRaisesRegex(ValueError,"Source changed"):
            self.run_check()
        path.write_text("server/unicode.c Wine29 isolated source")
        (self.source/"charoite-wine29-native-source-delta.patch").write_text("tampered")
        with self.assertRaisesRegex(ValueError,"provenance"):
            self.run_check()

    def test_invalid_elf_alignment_and_wrong_pe_architecture(self):
        def bad_align(_tool,*args):
            if args[0]=="-lW":return "  LOAD 0x0 0x0 0x0 0x10 0x10 R E 0x1000\n"
            return mock_command(_tool,*args)
        with patch.object(M,"command",side_effect=bad_align):
            with self.assertRaisesRegex(ValueError,"16 KiB"):
                M.verify_native(self.source/"charoite-arm64ec-android",self.readelf,
                                self.readobj,self.source)
        def bad_pe(_tool,*args):
            if args[0]=="--file-headers":return "Machine: IMAGE_FILE_MACHINE_AMD64 (0x8664)\n"
            return mock_command(_tool,*args)
        with patch.object(M,"command",side_effect=bad_pe):
            with self.assertRaisesRegex(ValueError,"ARM64EC"):
                M.verify_native(self.source/"charoite-arm64ec-android",self.readelf,
                                self.readobj,self.source)

    def test_pinned_llvm_inspector_symlink_is_allowed_only_within_bin_dir(self):
        toolchain = self.root/"verified-toolchain"
        toolchain.mkdir()
        target = toolchain/"llvm-readobj"
        target.write_text("#!/bin/sh\nprintf 'inspector-ok\n'\n")
        target.chmod(0o755)
        link = toolchain/"llvm-readelf"
        link.symlink_to(target)
        self.assertEqual(M.command(link), "inspector-ok\n")
        external = self.root/"unexpected-external-tool"
        external.write_text("#!/bin/sh\nprintf 'no\n'\n")
        external.chmod(0o755)
        escaped = toolchain/"untrusted"
        escaped.symlink_to(external)
        with self.assertRaisesRegex(ValueError, "escapes pinned toolchain"):
            M.command(escaped)
        missing = toolchain/"broken-inspector"
        missing.symlink_to(toolchain/"nonexistent-file")
        with self.assertRaisesRegex(ValueError, "Missing pinned inspection tool"):
            M.command(missing)

    def test_publish_no_overwrite_or_phone_execution(self):
        out=self.root/"sealed"
        with patch.object(M,"command",side_effect=mock_command):
            report=M.publish(self.source,self.readelf,self.readobj,out)
            self.assertTrue((out/"native-compile-report.json").is_file())
            self.assertFalse(report["launch_ready"])
            with self.assertRaisesRegex(ValueError,"existing or unsafe"):
                M.publish(self.source,self.readelf,self.readobj,out)
        code=SCRIPT.read_text()
        for forbidden in ("wineboot -i","adb install","subprocess.Popen","os.system(",
                          "rm -rf","unlink(","rmtree("):
            self.assertNotIn(forbidden,code)


if __name__=="__main__":unittest.main()
