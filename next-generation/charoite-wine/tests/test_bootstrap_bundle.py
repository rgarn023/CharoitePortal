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

def apiset_fixture():
    """Synthetic valid API-set namespace v6 PE32+ for archive tests."""
    data=bytearray(1024)
    data[:2]=b"MZ"
    struct.pack_into("<I",data,0x3c,0x80)
    data[0x80:0x84]=b"PE\x00\x00"
    struct.pack_into("<HH",data,0x84,0xAA64,1)
    struct.pack_into("<H",data,0x94,0xf0)
    struct.pack_into("<H",data,0x98,0x20b)
    off=0x80+24+0xf0
    data[off:off+8]=b".apiset\x00"
    struct.pack_into("<IIII",data,off+8,256,0x1000,256,512)
    struct.pack_into("<II",data,512,6,128)
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
    def test_26_component_services_provenance_and_tamper(self):
        for name,path in {**ver.EXTRA_PATHS,**ver.COM_PATHS,**ver.SERVICES_PATHS}.items():
            data=pe()
            self.payloads[path]=data
            self.parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                              "format":"PE","machine":"0xA641",
                              "imports":["kernel32.dll","notbundled.dll"]}
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.5"
        self.manifest["component_count"]=26
        self.manifest["startup_dependency_manifest_sha256"]="a"*64
        self.manifest["com_dependency_manifest_sha256"]="b"*64
        self.manifest["services_dependency_manifest_sha256"]="c"*64
        self.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE,*ver.COM_PE,*ver.SERVICES_PE) if k!="wineboot")
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(self.payloads["dependency-review.json"])
        self.save()
        m,r=ver.verify(self.path)
        self.assertEqual(m["component_count"],26)
        self.assertEqual(m["nls_count"],76)
        self.assertEqual(r["windows_imports_not_bundled"],["notbundled.dll"])
        self.payloads[ver.SERVICES_PATHS["bcrypt"]]=pe()+b"modified"
        self.save()
        with self.assertRaisesRegex(ValueError,"SHA-256"):
            ver.verify(self.path)

    def test_27_component_api_set_source_coherence_and_tamper(self):
        # Existing 26 ELF/PE components remain unchanged.
        extras={**ver.EXTRA_PATHS,**ver.COM_PATHS,**ver.SERVICES_PATHS}
        for name,path in extras.items():
            data=pe()
            self.payloads[path]=data
            self.parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                              "format":"PE","machine":"0xA641",
                              "imports":["kernel32.dll","notbundled.dll"]}
        self.manifest.update(
            version="wine10-arm64ec-bootstrap.0.6",component_count=27,
            startup_dependency_manifest_sha256="a"*64,
            com_dependency_manifest_sha256="b"*64,
            services_dependency_manifest_sha256="c"*64,
        )
        delta=(b"diff --git a/dlls/ntdll/unix/loader.c b/dlls/ntdll/unix/loader.c\n"
               b"CHAROITE_WINE28_PE_DIR\n"
               b"verified isolated Wine28 API-set PE is absent or unreadable\n")
        self.payloads["source/charoite-source-delta.patch"]=delta
        self.manifest["source_files"]["charoite-source-delta.patch"]={
            "path":"source/charoite-source-delta.patch","size":len(delta),
            "sha256":ver.digest(delta)}
        raw=apiset_fixture()
        path=ver.APISET_PATH["apisetschema"]
        self.payloads[path]=raw
        self.parts["apisetschema"]={"path":path,"size":len(raw),
            "sha256":ver.digest(raw),"format":"PE","machine":"0xAA64",
            "imports":[],"api_set_namespace_version":6}
        spec=b"apiset api-ms-win-core-test-l1-1-0 = kernelbase.dll\n"
        make=b"MODULE    = apisetschema.dll\nEXTRADLLFLAGS = -Wb,--data-only\n"
        self.payloads["source/apisetschema.spec"]=spec
        self.payloads["source/apisetschema.Makefile.in"]=make
        module={"machine":"0xaa64","namespace_version":6,
                "namespace_bytes":128,"file_bytes":len(raw),"sha256":ver.digest(raw)}
        proof={"schema_version":1,"source_commit":ver.BASE,"package":"com.charoitx",
            "module":module,"spec_sha256":ver.digest(spec),"make_sha256":ver.digest(make),
            "launch_ready":False,"prefix_created":False,"android_executed":False}
        proof_raw=(json.dumps(proof,sort_keys=True,indent=2)+"\n").encode()
        self.payloads["source/apisetschema-verified.json"]=proof_raw
        self.manifest["api_set_source_manifest_sha256"]=ver.digest(proof_raw)
        for name in ver.APISET_SOURCES:
            content=self.payloads["source/"+name]
            self.manifest["source_files"][name]={
                "path":"source/"+name,"size":len(content),"sha256":ver.digest(content)}
        self.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE,*ver.COM_PE,
                                *ver.SERVICES_PE,"apisetschema") if k!="wineboot")
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(self.payloads["dependency-review.json"])
        self.save()
        manifest,_=ver.verify(self.path)
        self.assertEqual(manifest["component_count"],27)
        self.assertEqual(manifest["version"],"wine10-arm64ec-bootstrap.0.6")
        bad=bytearray(raw)
        struct.pack_into("<I",bad,512,5)
        self.payloads[path]=bytes(bad)
        self.parts["apisetschema"]["sha256"]=ver.digest(bytes(bad))
        self.save()
        with self.assertRaisesRegex(ValueError,"API-set|namespace"):
            ver.verify(self.path)
        self.payloads[path]=raw
        self.parts["apisetschema"]["sha256"]=ver.digest(raw)
        corrupt=proof_raw.replace(b"c74acb09",b"c74acc09")
        self.payloads["source/apisetschema-verified.json"]=corrupt
        self.manifest["source_files"]["apisetschema-verified.json"]["sha256"]=ver.digest(corrupt)
        self.manifest["source_files"]["apisetschema-verified.json"]["size"]=len(corrupt)
        self.manifest["api_set_source_manifest_sha256"]=ver.digest(corrupt)
        self.save()
        with self.assertRaisesRegex(ValueError,"API-set proof"):
            ver.verify(self.path)

    def test_26_services_missing_provenance_rejected(self):
        for name,path in {**ver.EXTRA_PATHS,**ver.COM_PATHS,**ver.SERVICES_PATHS}.items():
            data=pe()
            self.payloads[path]=data
            self.parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                              "format":"PE","machine":"0xA641",
                              "imports":["kernel32.dll","notbundled.dll"]}
        self.manifest["version"]="wine10-arm64ec-bootstrap.0.5"
        self.manifest["component_count"]=26
        self.manifest["startup_dependency_manifest_sha256"]="a"*64
        self.manifest["com_dependency_manifest_sha256"]="b"*64
        self.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE,*ver.COM_PE,*ver.SERVICES_PE) if k!="wineboot")
        self.payloads["dependency-review.json"]=(json.dumps(self.report,sort_keys=True)+"\n").encode()
        self.manifest["dependency_review_sha256"]=ver.digest(self.payloads["dependency-review.json"])
        self.save()
        with self.assertRaisesRegex(ValueError,"services|security"):
            ver.verify(self.path)

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
