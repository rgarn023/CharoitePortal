"""Fail-closed FULL Wine29 .0.7 archive integration tests; no Wine execution."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
def module(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

base=module("wine29_fixture",ROOT/"tests/test_bootstrap_bundle.py")
ver=module("wine29_final_verifier",ROOT/"verify-bootstrap-bundle.py")
native=module("wine29_final_native",ROOT/"verify-wine29-native-isolation.py")
ASSEMBLE=(ROOT/"assemble-bootstrap-bundle.py").read_text()
COMPLETE=(ROOT/"build-wine29-complete.sh").read_text()
WORKFLOW=(ROOT.parent.parent/".github/workflows/charoite-wine-source.yml").read_text()


class FullWine29Contract(unittest.TestCase):
    def setUp(self):
        self.fixture=base.BootstrapBundleTest("test_verified_inventory")
        self.fixture.setUp()
        p=self.fixture.payloads
        manifest=self.fixture.manifest
        parts=self.fixture.parts
        sources=manifest["source_files"]
        for name,path in {**ver.EXTRA_PATHS,**ver.COM_PATHS,**ver.SERVICES_PATHS}.items():
            data=base.pe()
            p[path]=data
            parts[name]={"path":path,"size":len(data),"sha256":ver.digest(data),
                         "format":"PE","machine":"0xA641",
                         "imports":["kernel32.dll","notbundled.dll"]}
        manifest.update(version=ver.WINE29_VERSION,component_count=27,
                        startup_dependency_manifest_sha256="a"*64,
                        com_dependency_manifest_sha256="b"*64,
                        services_dependency_manifest_sha256="c"*64)
        old_delta=(b"CHAROITE_WINE28_PE_DIR\n"+
                   b"verified isolated Wine28 API-set PE is absent or unreadable\n")
        p["source/charoite-source-delta.patch"]=old_delta
        sources["charoite-source-delta.patch"]={
            "path":"source/charoite-source-delta.patch",
            "sha256":ver.digest(old_delta),"size":len(old_delta)}
        schema=base.apiset_fixture()
        path=ver.APISET_PATH["apisetschema"]
        p[path]=schema
        parts["apisetschema"]={"path":path,"size":len(schema),
            "sha256":ver.digest(schema),"format":"PE","machine":"0xAA64",
            "imports":[],"api_set_namespace_version":6}
        spec=b"apiset api-ms-win-core-test-l1-1-0 = kernelbase.dll\n"
        make=b"MODULE    = apisetschema.dll\nEXTRADLLFLAGS = -Wb,--data-only\n"
        p["source/apisetschema.spec"]=spec
        p["source/apisetschema.Makefile.in"]=make
        apiset_info={"machine":"0xaa64","namespace_version":6,"namespace_bytes":128,
                     "file_bytes":len(schema),"sha256":ver.digest(schema)}
        apiset_proof={"schema_version":1,"source_commit":ver.BASE,"package":"com.charoitx",
            "module":apiset_info,"spec_sha256":ver.digest(spec),"make_sha256":ver.digest(make),
            "launch_ready":False,"prefix_created":False,"android_executed":False}
        apiset_raw=(json.dumps(apiset_proof,sort_keys=True,indent=2)+"\n").encode()
        p["source/apisetschema-verified.json"]=apiset_raw
        manifest["api_set_source_manifest_sha256"]=ver.digest(apiset_raw)
        for name in ver.APISET_SOURCES:
            raw=p["source/"+name]
            sources[name]={"path":"source/"+name,"size":len(raw),"sha256":ver.digest(raw)}
        for name,markers in ver.WINE29_MARKERS.items():
            path=ver.EXPECTED[name]
            data=p[path]+b"\x00"+b"\x00".join(markers)+b"\x00"
            p[path]=data
            parts[name]["sha256"]=ver.digest(data)
            parts[name]["size"]=len(data)
        delta=(b"diff --git a/loader/main.c b/loader/main.c\n"+
               b"\n".join((b"CHAROITE_WINE29_NATIVE_DIR",b"CHAROITE_WINE29_PE_DIR",
                   b"CHAROITE_WINE29_DATA_DIR",b"Wine29/Wine28 selector conflict",
                   b"libcharoite_wine29_ntdll.so"))+b"\n")
        proof={"generation":ver.WINE29_VERSION,"source_commit":ver.BASE,
               "package":"com.charoitx","delta_sha256":ver.digest(delta),
               "runtime_executable":False,"device_tested":False,
               "native_elf_installed":False,"legacy_wine28_cohort_modified":False,
               "patch_sources":{name:{"before_sha256":"0"*64,"after_sha256":"a"*64}
                   for name in ("loader/main.c","dlls/ntdll/unix/loader.c","server/unicode.c")}}
        proof_raw=(json.dumps(proof,sort_keys=True,indent=2)+"\n").encode()
        for name,raw in (("charoite-wine29-native-source-delta.patch",delta),
                         ("charoite-wine29-native-source-validation.json",proof_raw)):
            p["source/"+name]=raw
            sources[name]={"path":"source/"+name,"sha256":ver.digest(raw),"size":len(raw)}
        manifest["wine29_native_source_proof_sha256"]=ver.digest(proof_raw)
        manifest["wine29_native_source_delta_sha256"]=ver.digest(delta)
        self.fixture.report["bundled_windows_dlls"]=sorted(
            k+".dll" for k in (*ver.PE,*ver.EXTRA_PE,*ver.COM_PE,*ver.SERVICES_PE,"apisetschema")
            if k!="wineboot")
        p["dependency-review.json"]=(json.dumps(self.fixture.report,sort_keys=True)+"\n").encode()
        manifest["dependency_review_sha256"]=ver.digest(p["dependency-review.json"])
        self.fixture.save()

    def tearDown(self):self.fixture.tearDown()

    def test_real_archive_verifier_accepts_only_complete_27_plus_76(self):
        report,_=ver.verify(self.fixture.path)
        self.assertEqual(report["component_count"],27)
        self.assertEqual(report["nls_count"],76)
        self.assertEqual(report["version"],ver.WINE29_VERSION)
        gated=native.verify_archive(self.fixture.path)
        self.assertTrue(gated["source_native_cohort_verified"])
        self.assertFalse(gated["apk_native_install_permitted"])
        self.assertFalse(gated["wineboot_execution_permitted"])

    def test_relabeling_old_archive_does_not_work(self):
        self.fixture.manifest["version"]="wine10-arm64ec-bootstrap.0.6"
        self.fixture.save()
        with self.assertRaisesRegex(ValueError,"Wrong, repeated|Unsafe"):
            ver.verify(self.fixture.path)
        with self.assertRaises(ValueError):
            native.verify_archive(self.fixture.path)

    def test_missing_or_tampered_source_patch_rejected(self):
        self.fixture.payloads.pop("source/charoite-wine29-native-source-delta.patch")
        self.fixture.save()
        with self.assertRaisesRegex((KeyError,ValueError),"Wrong, repeated|missing|not found"):
            ver.verify(self.fixture.path)

    def test_fake_proof_or_old_native_marker_rejected(self):
        self.fixture.manifest["wine29_native_source_proof_sha256"]="0"*64
        self.fixture.save()
        with self.assertRaisesRegex(ValueError,"Wine29 native source"):
            ver.verify(self.fixture.path)
        self.fixture.manifest["wine29_native_source_proof_sha256"]=ver.digest(
            self.fixture.payloads["source/charoite-wine29-native-source-validation.json"])
        body=self.fixture.payloads[ver.EXPECTED["wine"]]
        self.fixture.payloads[ver.EXPECTED["wine"]]=body.replace(
            b"libcharoite_wine29_ntdll.so",b"libcharoite_wine28_ntdll.so")
        self.fixture.parts["wine"]["sha256"]=ver.digest(self.fixture.payloads[ver.EXPECTED["wine"]])
        self.fixture.parts["wine"]["size"]=len(self.fixture.payloads[ver.EXPECTED["wine"]])
        self.fixture.save()
        with self.assertRaisesRegex(ValueError,"selector"):
            ver.verify(self.fixture.path)

    def test_new_cohort_requires_sealed_compiled_source_and_no_apk(self):
        self.assertIn("include_wine29: bool = False", ASSEMBLE)
        self.assertIn("charoite-wine29-native-source-delta.patch", ASSEMBLE)
        self.assertIn("New Wine29 native cohort requires", ASSEMBLE)
        self.assertIn("WINE29_COHERENT_SOURCE_MATCHED_FULL_BUNDLE=PASS", COMPLETE)
        self.assertIn('python3 "$scripts/verify-wine29-native-isolation.py"',COMPLETE)
        self.assertIn('--include-wine29',COMPLETE)
        for forbidden in ("adb install","wineboot -i","rm -rf","shutil.rmtree","su -c"):
            self.assertNotIn(forbidden,COMPLETE)

if __name__=="__main__":unittest.main()
