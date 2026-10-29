"""Ensure COM/RPC ARM64EC development remains source-audited and non-destructive."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("pe_com_verifier",ROOT/"verify-pe-com.py")
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)
BUILD=(ROOT/"build-pe-com.sh").read_text(encoding="utf-8")

def pe_blob(machine=0xAA64):
    data=bytearray(128)
    data[:2]=b"MZ"
    struct.pack_into("<I",data,0x3c,64)
    data[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",data,68,machine)
    return bytes(data)

HEADERS=("Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n"
         "Format: COFF-ARM64EC\nMachine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")

class ComBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.bundle=root/"com"
        self.bundle.mkdir()
        self.audit=root/"dependency-review.json"
        self.review={
            "schema_version":1,
            "purpose":v.PURPOSE,
            "windows_imports_not_bundled":[n+".dll" for n in v.NAMES],
        }
        self.save_audit()
        components={}
        for name in v.NAMES:
            data=pe_blob()
            (self.bundle/f"{name}-arm64ec.dll").write_bytes(data)
            (self.bundle/f"{name}-pe-header.txt").write_text(HEADERS)
            (self.bundle/f"{name}-pe-imports.txt").write_text(
                "File: "+name+".dll\nFormat: COFF-ARM64X\n")
            components[name]={
                "file":f"{name}-arm64ec.dll",
                "size":len(data),
                "sha256":hashlib.sha256(data).hexdigest(),
                "pe_machine":"0xA641",
                "raw_arm64x_carrier":"0xAA64",
            }
        self.manifest={
            "schema_version":1,"source_commit":v.SOURCE,
            "android_package":"com.charoitx","status":"compiled-not-executed",
            "dependency_review_sha256":hashlib.sha256(self.audit.read_bytes()).hexdigest(),
            "launch_ready":False,"installable":False,
            "prefix_created":False,"device_tested":False,"anti_cheat_supported":False,
            "components":components,
        }
        self.save()
    def tearDown(self): self.temp.cleanup()
    def save(self):
        (self.bundle/"pe-com-manifest.json").write_text(json.dumps(self.manifest))
    def save_audit(self):
        self.audit.write_text(json.dumps(self.review))
    def test_valid(self):
        self.assertEqual(len(v.verify(self.bundle,self.audit)["components"]),4)
    def test_tampered_library(self):
        p=self.bundle/"ole32-arm64ec.dll"
        p.write_bytes(p.read_bytes()+b"x")
        with self.assertRaisesRegex(ValueError,"SHA"):
            v.verify(self.bundle,self.audit)
    def test_wrong_machine(self):
        bad=pe_blob(0x8664)
        (self.bundle/"rpcrt4-arm64ec.dll").write_bytes(bad)
        self.manifest["components"]["rpcrt4"]["sha256"]=hashlib.sha256(bad).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError,"carrier"):
            v.verify(self.bundle,self.audit)
    def test_arm64ec_view_missing(self):
        (self.bundle/"combase-pe-header.txt").write_text(
            "Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n")
        with self.assertRaisesRegex(ValueError,"dual view"):
            v.verify(self.bundle,self.audit)
    def test_forbidden_ready_flag(self):
        self.manifest["launch_ready"]=True
        self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            v.verify(self.bundle,self.audit)
    def test_unverified_missing_import_rejected(self):
        self.review["windows_imports_not_bundled"].remove("comctl32.dll")
        self.save_audit()
        with self.assertRaisesRegex(ValueError,"audit"):
            v.verify(self.bundle,self.audit)
    def test_missing_import_file(self):
        (self.bundle/"ole32-pe-imports.txt").unlink()
        with self.assertRaises((ValueError,FileNotFoundError)):
            v.verify(self.bundle,self.audit)
    def test_build_guards(self):
        for token in ("rpcrt4 combase ole32 comctl32","verify-pe-com.py",
                      "Refusing existing experimental COM output",
                      "charoite-source-validation.txt"):
            self.assertIn(token,BUILD)
        for token in ("adb install","rm -rf","WINEPREFIX=","su -c","clearAppData"):
            self.assertNotIn(token,BUILD)

if __name__=="__main__":unittest.main()
