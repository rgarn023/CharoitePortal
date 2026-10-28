"""Source-safety and tamper tests for ARM64EC audited API expansion."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
exp=load("charoite_pe_expansion","verify-pe-expansion.py")
foundation=load("charoite_pe_foundation_test","verify-pe-foundation.py")
SCRIPT=(ROOT/"build-pe-expansion.sh").read_text(encoding="utf-8")

def synthetic_pe(machine=0xAA64):
    raw=bytearray(128);raw[:2]=b"MZ"
    struct.pack_into("<I",raw,0x3c,64);raw[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",raw,68,machine)
    return bytes(raw)

HEADER=("Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n"
        "Format: COFF-ARM64EC\nMachine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")

class PEExpansionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        p=Path(self.tmp.name);self.root=p/"exp";self.base=p/"base"
        self.root.mkdir();self.base.mkdir()
        baseparts={}
        for name in foundation.NAMES:
            data=synthetic_pe()
            (self.base/f"{name}-arm64ec.dll").write_bytes(data)
            (self.base/f"{name}-pe-header.txt").write_text(HEADER,encoding="utf-8")
            baseparts[name]={"file":f"{name}-arm64ec.dll","size":len(data),
                             "sha256":hashlib.sha256(data).hexdigest(),"pe_machine":"0xA641"}
        self.base_manifest={
            "schema_version":1,"source_commit":exp.SOURCE,"android_package":"com.charoitx",
            "status":"compile-verified-not-executed","launch_ready":False,"installable":False,
            "prefix_created":False,"device_tested":False,"components":baseparts}
        self.write_base()
        parts={}
        for name in exp.NAMES:
            data=synthetic_pe()
            (self.root/f"{name}-arm64ec.dll").write_bytes(data)
            (self.root/f"{name}-pe-header.txt").write_text(HEADER,encoding="utf-8")
            parts[name]={"file":f"{name}-arm64ec.dll","pe_machine":"0xA641",
                         "raw_arm64x_carrier":"0xAA64","size":len(data),
                         "sha256":hashlib.sha256(data).hexdigest()}
        self.m={"schema_version":1,"source_commit":exp.SOURCE,"android_package":"com.charoitx",
                "status":"compiled-not-executed","launch_ready":False,"installable":False,
                "prefix_created":False,"device_tested":False,"anti_cheat_supported":False,
                "components":parts,"depends_on_foundation_manifest_sha256":hashlib.sha256(
                    (self.base/"pe-foundation-manifest.json").read_bytes()).hexdigest()}
        self.save()
    def write_base(self):
        (self.base/"pe-foundation-manifest.json").write_text(json.dumps(self.base_manifest))
    def save(self):
        (self.root/"pe-expansion-manifest.json").write_text(json.dumps(self.m))
    def tearDown(self):
        self.tmp.cleanup()
    def test_valid(self):
        self.assertEqual(len(exp.verify(self.root,self.base)["components"]),4)
    def test_hash_tamper(self):
        (self.root/"crypt32-arm64ec.dll").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"hash"):
            exp.verify(self.root,self.base)
    def test_wrong_machine(self):
        p=self.root/"setupapi-arm64ec.dll"
        data=synthetic_pe(0x8664);p.write_bytes(data)
        self.m["components"]["setupapi"]["sha256"]=hashlib.sha256(data).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError,"ARM64X carrier"):
            exp.verify(self.root,self.base)
    def test_missing_hybrid_view(self):
        (self.root/"version-pe-header.txt").write_text(
            "Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n")
        with self.assertRaisesRegex(ValueError,"dual-view"):
            exp.verify(self.root,self.base)
    def test_dependency_manifest_tamper(self):
        self.base_manifest["launch_ready"]=True;self.write_base()
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            exp.verify(self.root,self.base)
    def test_unsupported_ready_status(self):
        self.m["launch_ready"]=True;self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe"):
            exp.verify(self.root,self.base)
    def test_unexpected_file(self):
        (self.root/"extra").write_text("x")
        with self.assertRaisesRegex(ValueError,"Unexpected"):
            exp.verify(self.root,self.base)
    def test_script_is_non_destructive(self):
        self.assertEqual(set(exp.NAMES),{"crypt32","setupapi","shlwapi","version"})
        self.assertIn("for name in crypt32 setupapi shlwapi version",SCRIPT)
        self.assertIn("verify-pe-foundation.py",SCRIPT)
        self.assertIn("CHAROITE_PE_EXPANSION_AUDIT_INPUT_VERIFIED=PASS",SCRIPT)
        for invalid in ("rm -rf","adb install","WINEPREFIX=","su -c"):
            self.assertNotIn(invalid,SCRIPT)

if __name__=="__main__":unittest.main()
