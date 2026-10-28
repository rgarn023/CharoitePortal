"""Contract tests for source-built Charoite ARM64EC foundation libraries."""
import hashlib,importlib.util,json,struct,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("pe_foundation",ROOT/"verify-pe-foundation.py")
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
BUILD=(ROOT/"build-pe-foundation.sh").read_text(encoding="utf-8")
def synthetic_pe(machine=0xA641):
    data=bytearray(128);data[:2]=b"MZ"
    struct.pack_into("<I",data,0x3c,64);data[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",data,68,machine)
    return bytes(data)
class FoundationContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        parts={}
        for name in mod.NAMES:
            d=synthetic_pe()
            (self.root/f"{name}-arm64ec.dll").write_bytes(d)
            (self.root/f"{name}-pe-header.txt").write_text("Machine: IMAGE_FILE_MACHINE_ARM64EC (0xA641)\n")
            parts[name]={"file":f"{name}-arm64ec.dll","pe_machine":"0xA641",
                         "sha256":hashlib.sha256(d).hexdigest(),"size":len(d)}
        self.manifest={"schema_version":1,"source_commit":mod.SOURCE,"android_package":"com.charoitx",
                       "status":"compile-verified-not-executed","launch_ready":False,"installable":False,
                       "prefix_created":False,"device_tested":False,"components":parts}
        self.save()
    def save(self):
        (self.root/"pe-foundation-manifest.json").write_text(json.dumps(self.manifest))
    def tearDown(self): self.tmp.cleanup()
    def test_valid(self): self.assertEqual(len(mod.verify(self.root)["components"]),3)
    def test_wrong_machine_rejected(self):
        p=self.root/"user32-arm64ec.dll";d=synthetic_pe(0xAA64);p.write_bytes(d)
        self.manifest["components"]["user32"]["sha256"]=hashlib.sha256(d).hexdigest()
        self.save()
        with self.assertRaisesRegex(ValueError,"not ARM64EC"):mod.verify(self.root)
    def test_tamper_rejected(self):
        (self.root/"ws2_32-arm64ec.dll").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError,"digest"):mod.verify(self.root)
    def test_ready_flag_rejected(self):
        self.manifest["launch_ready"]=True;self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe"):mod.verify(self.root)
    def test_extra_rejected(self):
        (self.root/"other.dll").write_bytes(b"x")
        with self.assertRaisesRegex(ValueError,"Unexpected"):mod.verify(self.root)
    def test_symlink_rejected(self):
        p=self.root/"advapi32-arm64ec.dll";p.unlink();p.symlink_to(self.root/"user32-arm64ec.dll")
        with self.assertRaisesRegex(ValueError,"unsafe"):mod.verify(self.root)
    def test_build_is_non_destructive(self):
        self.assertIn("CHAROITE_PE_FOUNDATION_AUDIT_INPUT_VERIFIED=PASS",BUILD)
        for name in mod.NAMES: self.assertIn(f"dlls/$name/aarch64-windows/$name.dll",BUILD)
        for bad in ("adb install","rm -rf","WINEPREFIX=","su -c"):
            self.assertNotIn(bad,BUILD)
        self.assertIn("Refusing to overwrite output",BUILD)
if __name__=="__main__":unittest.main()
