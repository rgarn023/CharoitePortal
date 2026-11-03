"""Fail-closed API-set schema source build and PE validation tests."""
from pathlib import Path
import importlib.util
import struct
import unittest
import tempfile
import json
ROOT=Path(__file__).resolve().parents[1]
B=(ROOT/"build-apiset-bootstrap.sh").read_text()
W=(ROOT.parent.parent/".github/workflows/charoite-wine-source.yml").read_text()
p=ROOT/"verify-apiset-bootstrap.py"
spec=importlib.util.spec_from_file_location("apiset",p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class APISetContract(unittest.TestCase):
    def test_pinned_ci_only(self):
        for x in ("apisetschema/aarch64-windows/apisetschema.dll","-Wb,--data-only",
                  "charoite-source-validation.txt","COPYING.LIB"):
            self.assertIn(x,B)
        for x in ("build-apiset-bootstrap.sh","verify-apiset-bootstrap.py",
                  "Charoite-Wine-APISet-Schema-Experimental"):
            self.assertIn(x,W)
        for x in ("rm -rf","wineboot -i","WINEPREFIX=","wineserver -f"):
            self.assertNotIn(x,B)
    def test_sealed_proof_revalidated_for_coherent_archive(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            data=bytearray(1024);data[:2]=b"MZ"
            struct.pack_into("<I",data,0x3c,0x80)
            data[0x80:0x84]=b"PE\\x00\\x00"
            struct.pack_into("<HH",data,0x84,0xaa64,1)
            struct.pack_into("<H",data,0x94,0xf0)
            struct.pack_into("<H",data,0x98,0x20b)
            section=0x80+24+0xf0
            data[section:section+8]=b".apiset\\x00"
            struct.pack_into("<IIII",data,section+8,256,0x1000,256,512)
            struct.pack_into("<II",data,512,6,128)
            (root/"apisetschema.dll").write_bytes(bytes(data))
            (root/"apisetschema.spec").write_text(
                "apiset api-ms-win-test = kernelbase.dll\\n"
                "apiset api-ms-win-legacy = kernel32.dll\\n")
            (root/"Makefile.in").write_text(
                "MODULE    = apisetschema.dll\\nEXTRADLLFLAGS = -Wb,--data-only\\n")
            (root/"COPYING.LIB").write_text("Wine LGPL license fixture")
            (root/"pe-file-header.txt").write_text("Machine: IMAGE_FILE_MACHINE_ARM64")
            proof=m.verify(root)
            (root/"verified-apiset.json").write_text(json.dumps(proof,sort_keys=True)+"\\n")
            self.assertEqual(m.verify(root),proof)
            (root/"verified-apiset.json").write_text(
                json.dumps({**proof,"launch_ready":True})+"\\n")
            with self.assertRaisesRegex(ValueError,"proof is inconsistent"):
                m.verify(root)
    def test_pe_namespace_validation(self):
        d=bytearray(1024);d[:2]=b"MZ"
        struct.pack_into("<I",d,0x3c,0x80);d[0x80:0x84]=b"PE\0\0"
        struct.pack_into("<HH",d,0x84,0xaa64,1)
        struct.pack_into("<H",d,0x94,0xf0)
        struct.pack_into("<H",d,0x98,0x20b)
        at=0x80+24+0xf0;d[at:at+8]=b".apiset\0"
        struct.pack_into("<IIII",d,at+8,256,0x1000,256,512)
        struct.pack_into("<II",d,512,6,128)
        self.assertEqual(m.inspect(d)["namespace_version"],6)
        for offset,fmt,value in ((0x84,"<H",0x8664),(512,"<I",5),(516,"<I",5000)):
            broken=bytearray(d);struct.pack_into(fmt,broken,offset,value)
            with self.assertRaises(ValueError):m.inspect(broken)
        with self.assertRaises(ValueError):m.inspect(d[:500])
if __name__=="__main__":unittest.main()
