"""Contracts for an additional four source-built ARM64EC Windows startup APIs."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("charoite_pe_startup",ROOT/"verify-pe-startup.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
BUILD=(ROOT/"build-pe-startup.sh").read_text(encoding="utf-8")
DUAL=("Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n"
      "Format: COFF-ARM64EC\nMachine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")

def make_pe(coff=0xAA64):
    blob=bytearray(128)
    blob[:2]=b"MZ"
    struct.pack_into("<I",blob,0x3c,64)
    blob[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",blob,68,coff)
    return bytes(blob)

class StartupTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.root=Path(self.tmp.name)/"new";self.root.mkdir()
        self.base=Path(self.tmp.name)/"dependency-review.json"
        self.review={
            "schema_version":1,
            "purpose":"Exact imports in sampled compiled bootstrap; not full runtime dependency closure",
            "windows_imports_not_bundled":[f"{name}.dll" for name in mod.NAMES],
        }
        self.save_base()
        components={}
        for name in mod.NAMES:
            binary=make_pe()
            (self.root/f"{name}-arm64ec.dll").write_bytes(binary)
            (self.root/f"{name}-pe-header.txt").write_text(DUAL)
            (self.root/f"{name}-pe-imports.txt").write_text(
                "File: "+name+".dll\nFormat: COFF-ARM64X\nImport {\n Name: kernel32.dll\n}\n")
            components[name]={
                "file":f"{name}-arm64ec.dll",
                "size":len(binary),"sha256":hashlib.sha256(binary).hexdigest(),
                "pe_machine":"0xA641","raw_arm64x_carrier":"0xAA64",
            }
        self.manifest={
            "schema_version":1,"source_commit":mod.SOURCE,
            "android_package":"com.charoitx","status":"compiled-not-executed",
            "base_dependency_review_sha256":hashlib.sha256(self.base.read_bytes()).hexdigest(),
            "launch_ready":False,"installable":False,"prefix_created":False,
            "device_tested":False,"anti_cheat_supported":False,
            "components":components,
        }
        self.save()
    def save(self):
        (self.root/"pe-startup-manifest.json").write_text(json.dumps(self.manifest))
    def save_base(self):
        self.base.write_text(json.dumps(self.review))
    def tearDown(self): self.tmp.cleanup()
    def test_valid(self):
        self.assertEqual(len(mod.verify(self.root,self.base)["components"]),4)
    def test_tampered_dll(self):
        (self.root/"win32u-arm64ec.dll").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"hash"):mod.verify(self.root,self.base)
    def test_plain_x64_rejected(self):
        bad=make_pe(0x8664)
        (self.root/"gdi32-arm64ec.dll").write_bytes(bad)
        self.manifest["components"]["gdi32"]["sha256"]=hashlib.sha256(bad).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError,"ARM64X carrier"):mod.verify(self.root,self.base)
    def test_no_embedded_arm64ec_view(self):
        (self.root/"shell32-pe-header.txt").write_text("Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n")
        with self.assertRaisesRegex(ValueError,"dual view"):mod.verify(self.root,self.base)
    def test_refuses_unaudited_candidate(self):
        self.review["windows_imports_not_bundled"].remove("ucrtbase.dll")
        self.save_base()
        with self.assertRaisesRegex(ValueError,"earlier bootstrap"):mod.verify(self.root,self.base)
    def test_missing_import_inspection(self):
        (self.root/"shell32-pe-imports.txt").write_text("")
        with self.assertRaisesRegex(ValueError,"unsafe|Unsafe|empty"):mod.verify(self.root,self.base)
    def test_not_launch_ready(self):
        self.manifest["launch_ready"]=True;self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe"):mod.verify(self.root,self.base)
    def test_no_file_overwrite_or_install(self):
        self.assertIn("for name in win32u gdi32 ucrtbase shell32",BUILD)
        self.assertIn("Refusing to replace PE startup output",BUILD)
        self.assertIn("verify-pe-startup.py",BUILD)
        for bad in ("rm -rf","adb install","WINEPREFIX=","su -c","deleteRecursively"):
            self.assertNotIn(bad,BUILD)

if __name__=="__main__":unittest.main()
