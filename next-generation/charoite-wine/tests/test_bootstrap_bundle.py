"""Unit-test coherent Wine bootstrap archive fail-closed ABI and provenance."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import struct
import tarfile
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("charoite_bootstrap",ROOT/"verify-bootstrap-bundle.py")
ver=importlib.util.module_from_spec(spec)
spec.loader.exec_module(ver)
PACKAGER=(ROOT/"assemble-bootstrap-bundle.py").read_text(encoding="utf-8")
WORKFLOW=(ROOT.parent.parent/".github/workflows/charoite-wine-source.yml").read_text(encoding="utf-8")

def pe():
    data=bytearray(128)
    data[:2]=b"MZ"
    struct.pack_into("<I",data,0x3c,64)
    data[64:68]=b"PE\x00\x00"
    struct.pack_into("<H",data,68,0xAA64)
    return bytes(data)

def elf():
    data=bytearray(32)
    data[:6]=b"\x7fELF\x02\x01"
    struct.pack_into("<H",data,18,183)
    return bytes(data)

class BootstrapBundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/"sample.tar.gz"
        self.parts={}
        self.payloads={}
        for name,path in ver.EXPECTED.items():
            data=elf() if name in ver.ELF else pe()
            self.payloads[path]=data
            entry={"path":path,"size":len(data),"sha256":ver.digest(data),
                   "format":"ELF" if name in ver.ELF else "PE"}
            if name in ver.ELF:
                entry.update(machine="AArch64",load_alignments=[16384],
                             needed=["libc.so"],interpreter=None)
            else:
                entry.update(machine="0xAA64" if name=="wineboot" else "0xA641",
                             imports=["kernel32.dll","notbundled.dll"])
            self.parts[name]=entry
        sources={}
        for name in ver.SOURCES:
            data=(name+" license source content").encode()
            self.payloads["source/"+name]=data
            sources[name]={"path":"source/"+name,"size":len(data),"sha256":ver.digest(data)}
        self.nls={}
        nls_names=set(ver.NLS_REQUIRED)|{f"c_{30000+i}.nls" for i in range(71)}
        self.assertEqual(len(nls_names),76)
        for name in sorted(nls_names):
            contents=(name+" pinned Wine NLS bytes").encode()
            archive_path="runtime/nls/"+name
            self.payloads[archive_path]=contents
            self.nls[name]={"path":archive_path,"sha256":ver.digest(contents),"size":len(contents)}
        imported=["kernel32.dll","notbundled.dll"]
        self.report={"schema_version":1,
                     "bundled_windows_dlls":sorted(k+".dll" for k in ver.PE if k!="wineboot"),
                     "observed_windows_imports":imported,
                     "windows_imports_not_bundled":["notbundled.dll"],
                     "android_elf_needed":["libc.so"]}
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest={
            "schema_version":1,"version":"wine10-arm64ec-bootstrap.0.2",
            "source_commit":ver.BASE,"android_package":"com.charoitx",
            "status":"coherent-components-not-executed",
            "component_count":len(ver.EXPECTED),"components":self.parts,
            "source_files":sources,"nls_count":len(self.nls),"nls_files":self.nls,
            "dependency_review_sha256":ver.digest(
                self.payloads["dependency-review.json"]),
            "window_imports_unresolved_count":1,
            "launch_ready":False,"installable":False,"prefix_created":False,
            "device_tested":False,"anti_cheat_supported":False}
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self,duplicate=None):
        self.payloads["manifest.json"]=(json.dumps(self.manifest,sort_keys=True)+"\n").encode()
        with self.path.open("wb") as raw:
            with gzip.GzipFile(fileobj=raw,mode="wb",filename="",mtime=0) as compressed:
                with tarfile.open(fileobj=compressed,mode="w") as archive:
                    for name,content in sorted(self.payloads.items()):
                        member=tarfile.TarInfo(name)
                        member.size=len(content)
                        archive.addfile(member,io.BytesIO(content))
                    if duplicate:
                        d=self.payloads[duplicate]
                        info=tarfile.TarInfo(duplicate);info.size=len(d)
                        archive.addfile(info,io.BytesIO(d))
    def test_verified_inventory(self):
        m,r=ver.verify(self.path)
        self.assertEqual(m["component_count"],14)
        self.assertEqual(m["nls_count"],76)
        self.assertIn("c_932.nls",m["nls_files"])
        self.assertEqual(r["windows_imports_not_bundled"],["notbundled.dll"])
    def test_extended_18_component_bundle(self):
        for name,path in ver.EXTRA_PATHS.items():
            data=pe()
            self.payloads[path]=data
            self.parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                              "format":"PE","machine":"0xA641",
                              "imports":["kernel32.dll","notbundled.dll"]}
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.3"
        self.manifest["component_count"]=18
        self.manifest["startup_dependency_manifest_sha256"]="a"*64
        self.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE) if k!="wineboot")
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(
            self.payloads["dependency-review.json"])
        self.save()
        m,r=ver.verify(self.path)
        self.assertEqual(m["component_count"],18)
        self.assertEqual(m["nls_count"],76)
        self.assertEqual(r["windows_imports_not_bundled"],["notbundled.dll"])
        self.payloads[ver.EXTRA_PATHS["win32u"]]=pe()+b"damaged"
        self.save()
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            ver.verify(self.path)
    def test_extended_archive_rejects_missing_provenance(self):
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.3"
        self.save()
        with self.assertRaisesRegex(ValueError,"Wrong, repeated|Unsafe"):
            ver.verify(self.path)
    def test_22_component_bundle_and_com_tamper(self):
        for name,path in {**ver.EXTRA_PATHS,**ver.COM_PATHS}.items():
            data=pe()
            self.payloads[path]=data
            self.parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                              "format":"PE","machine":"0xA641",
                              "imports":["kernel32.dll","notbundled.dll"]}
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.4"
        self.manifest["component_count"]=22
        self.manifest["startup_dependency_manifest_sha256"]="a"*64
        self.manifest["com_dependency_manifest_sha256"]="b"*64
        self.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE,*ver.COM_PE) if k!="wineboot")
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(
            self.payloads["dependency-review.json"])
        self.save()
        manifest,review=ver.verify(self.path)
        self.assertEqual(manifest["component_count"],22)
        self.assertEqual(manifest["nls_count"],76)
        self.assertEqual(review["windows_imports_not_bundled"],["notbundled.dll"])
        self.payloads[ver.COM_PATHS["ole32"]]=pe()+b"unexpected"
        self.save()
        with self.assertRaisesRegex(ValueError,"SHA-256"):ver.verify(self.path)
    def test_22_bundle_rejects_unverified_com_provenance(self):
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.4"
        self.save()
        with self.assertRaisesRegex(ValueError,"Wrong, repeated|Unsafe"):ver.verify(self.path)
    def test_dll_tamper_rejected(self):
        self.payloads[ver.EXPECTED["user32"]]=pe()+b"changed"
        self.save()
        with self.assertRaisesRegex(ValueError,"SHA-256"):ver.verify(self.path)
    def test_nls_tamper_rejected(self):
        self.payloads["runtime/nls/c_932.nls"]=b"wrong Japanese CP932 table"
        self.save()
        with self.assertRaisesRegex(ValueError,"NLS file hash"):ver.verify(self.path)
    def test_missing_nls_rejected(self):
        self.payloads.pop("runtime/nls/c_1252.nls")
        self.save()
        with self.assertRaisesRegex(ValueError,"Missing or unexpected Wine NLS"):ver.verify(self.path)
    def test_forged_readiness_rejected(self):
        self.manifest["launch_ready"]=True
        self.save()
        with self.assertRaisesRegex(ValueError,"Unsafe"):ver.verify(self.path)
    def test_forged_dependency_closure_rejected(self):
        self.report["windows_imports_not_bundled"]=[]
        self.payloads["dependency-review.json"]=(json.dumps(self.report)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(
            self.payloads["dependency-review.json"])
        self.save()
        with self.assertRaisesRegex(ValueError,"Dependency closure"):ver.verify(self.path)
    def test_duplicate_members_rejected(self):
        self.save(duplicate=ver.EXPECTED["wine"])
        with self.assertRaisesRegex(ValueError,"repeated"):ver.verify(self.path)
    def test_wrong_elf_architecture_rejected(self):
        path=ver.EXPECTED["wine"]
        altered=bytearray(elf())
        struct.pack_into("<H",altered,18,62)
        self.payloads[path]=bytes(altered)
        self.parts["wine"]["sha256"]=ver.digest(bytes(altered))
        self.save()
        with self.assertRaisesRegex(ValueError,"AArch64"):ver.verify(self.path)
    def test_wrong_pe_machine_rejected(self):
        path=ver.EXPECTED["wineboot"]
        altered=bytearray(pe());struct.pack_into("<H",altered,68,0x8664)
        self.payloads[path]=bytes(altered)
        self.parts["wineboot"]["sha256"]=ver.digest(bytes(altered))
        self.save()
        with self.assertRaisesRegex(ValueError,"regular ARM64"):ver.verify(self.path)
    def test_no_installed_runtime_mutation(self):
        for name in ("verify-pe-foundation.py","verify-pe-expansion.py",
                     "verify-kernel-bridge.py","verify-wineboot.py",
                     "verify-runtime-slice.py"):
            self.assertIn(name,PACKAGER)
        for forbidden in ("rm -rf","adb install","WINEPREFIX=","su -c",
                          "deleteRecursively","/data/data/com.charoite/files"):
            self.assertNotIn(forbidden,PACKAGER)
        self.assertIn("Refusing existing or unsafe output",PACKAGER)
        self.assertIn("launch_ready",PACKAGER)
        self.assertIn("charoite-wine-bootstrap-bundle.tar.gz",PACKAGER)

if __name__=="__main__":unittest.main()
