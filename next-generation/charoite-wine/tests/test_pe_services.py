"""Source-verified ARM64EC security/service DLL experiment, not an Android install."""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("pe_services",ROOT/"verify-pe-services.py")
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
BUILD=(ROOT/"build-pe-services.sh").read_text(encoding="utf-8")
WF=(ROOT.parent.parent/".github/workflows/charoite-wine-source.yml").read_text(encoding="utf-8")

def pe():
    b=bytearray(128)
    b[:2]=b"MZ"
    struct.pack_into("<I",b,0x3c,64)
    b[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",b,68,0xAA64)
    return bytes(b)

HEADERS=("Format: COFF-ARM64X\nMachine: IMAGE_FILE_MACHINE_ARM64X (0xA64E)\n"
         "Format: COFF-ARM64EC\nMachine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")

class ServicesTest(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.out=root/"services";self.out.mkdir()
        self.review=root/"review.json"
        self.audit={
            "schema_version":1,"purpose":v.PURPOSE,
            "windows_imports_not_bundled":[n+".dll" for n in v.NAMES]
        }
        self.save_review()
        entries={}
        for name in v.NAMES:
            b=pe()
            (self.out/f"{name}-arm64ec.dll").write_bytes(b)
            (self.out/f"{name}-pe-header.txt").write_text(HEADERS)
            (self.out/f"{name}-pe-imports.txt").write_text("File: "+name+".dll\nFormat: COFF-ARM64X\n")
            entries[name]={"file":name+"-arm64ec.dll","size":len(b),
                           "sha256":hashlib.sha256(b).hexdigest(),
                           "pe_machine":"0xA641","raw_arm64x_carrier":"0xAA64"}
        self.manifest={
            "schema_version":1,"source_commit":v.SOURCE,
            "android_package":"com.charoitx","status":"compiled-not-executed",
            "dependency_review_sha256":hashlib.sha256(self.review.read_bytes()).hexdigest(),
            "launch_ready":False,"installable":False,"prefix_created":False,
            "device_tested":False,"anti_cheat_supported":False,
            "components":entries
        }
        self.save()
    def tearDown(self):self.temp.cleanup()
    def save(self): (self.out/"pe-services-manifest.json").write_text(json.dumps(self.manifest))
    def save_review(self):self.review.write_text(json.dumps(self.audit))
    def test_verified_security_apis(self):
        self.assertEqual(len(v.verify(self.out,self.review)["components"]),4)
    def test_modified_binary_blocked(self):
        p=self.out/"bcrypt-arm64ec.dll"
        p.write_bytes(p.read_bytes()+b"tampered")
        with self.assertRaisesRegex(ValueError,"hash|SHA"):v.verify(self.out,self.review)
    def test_wrong_pe_machine_blocked(self):
        p=self.out/"msvcrt-arm64ec.dll"
        b=bytearray(p.read_bytes());struct.pack_into("<H",b,68,0x8664)
        p.write_bytes(bytes(b))
        self.manifest["components"]["msvcrt"]["sha256"]=hashlib.sha256(b).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError,"carrier"):v.verify(self.out,self.review)
    def test_forged_ready_or_missing_dependency_blocked(self):
        self.manifest["launch_ready"]=True;self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe|unsafe|Unverified"):v.verify(self.out,self.review)
        self.manifest["launch_ready"]=False;self.save()
        self.audit["windows_imports_not_bundled"].remove("secur32.dll");self.save_review()
        with self.assertRaisesRegex(ValueError,"review"):v.verify(self.out,self.review)
    def test_build_provenance_and_ci_output_only(self):
        for token in ('CROSSCFLAGS="-O2 -g0 -DLTC_NO_ASM"',
                      '"dlls/bcrypt/aarch64-windows/bcrypt.dll"',
                      "for name in secur32 sechost msvcrt",
                      "verify-pe-services.py",
                      "CHAROITE_SERVICES_AUDIT_22_INPUT_VERIFIED",
                      "charoite-source-validation.txt"):
            self.assertIn(token,BUILD)
        for forbidden in ("adb install","rm -rf","WINEPREFIX=","su -c"):
            self.assertNotIn(forbidden,BUILD)
        for token in ("build-pe-services.sh","verify-pe-services.py","--include-services",
                      "Charoite-Wine-Coherent-Bootstrap-26-Experimental",
                      "COMPONENTS=26","LAUNCH_READY=false"):
            self.assertIn(token,WF)
if __name__=="__main__":unittest.main()
