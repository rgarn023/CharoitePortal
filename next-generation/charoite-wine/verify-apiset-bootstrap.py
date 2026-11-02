#!/usr/bin/env python3
"""Validate pinned Wine 10 data-only API-set namespace, without Wine execution."""
import hashlib
import json
from pathlib import Path
import struct
import sys
BASE = "c74acb09d51b447f5d5ac56c87608d3ec565a767"
def sha(data):
    return hashlib.sha256(data).hexdigest()
def inspect(data):
    if not 512<=len(data)<=4*1024*1024 or data[:2]!=b"MZ":
        raise ValueError("Invalid PE byte limit/header")
    pe=struct.unpack_from("<I",data,0x3c)[0]
    if pe<64 or pe+24>len(data) or data[pe:pe+4]!=b"PE\0\0":
        raise ValueError("No PE signature")
    machine,count=struct.unpack_from("<HH",data,pe+4)
    optional=struct.unpack_from("<H",data,pe+20)[0]
    if machine not in (0xaa64,0xa641) or not 1<=count<=24 or not 96<=optional<=512:
        raise ValueError("Wrong ARM64 PE header")
    if struct.unpack_from("<H",data,pe+24)[0]!=0x20b or pe+24+optional+count*40>len(data):
        raise ValueError("PE32+ section table invalid")
    found=[]
    for i in range(count):
        h=pe+24+optional+i*40
        if data[h:h+8].rstrip(b"\0")!=b".apiset":
            continue
        virtual,_,raw,ptr=struct.unpack_from("<IIII",data,h+8)
        if ptr==0 or raw<8 or virtual<8 or ptr+raw>len(data):
            raise ValueError("Invalid .apiset section bounds")
        version, size=struct.unpack_from("<II",data,ptr)
        if version!=6 or not 8<=size<=min(raw,virtual):
            raise ValueError("API-set namespace v6 required")
        found.append((version,size))
    if len(found)!=1: raise ValueError("Missing or duplicate .apiset section")
    return {"machine":hex(machine),"namespace_version":found[0][0],
            "namespace_bytes":found[0][1],"sha256":sha(data),"file_bytes":len(data)}
def verify(path):
    p=Path(path)
    names={"apisetschema.dll","apisetschema.spec","Makefile.in","COPYING.LIB","pe-file-header.txt"}
    if p.is_symlink() or not p.is_dir() or {f.name for f in p.iterdir()}!=names:
        raise ValueError("Untrusted CI output inventory")
    if any((p/n).is_symlink() or not (p/n).is_file() or not (p/n).stat().st_size for n in names):
        raise ValueError("Missing or unsafe file")
    spec=(p/"apisetschema.spec").read_bytes()
    make=(p/"Makefile.in").read_bytes()
    if not spec.startswith(b"apiset ") or b"kernel32.dll" not in spec or b"kernelbase.dll" not in spec:
        raise ValueError("Unexpected source mapping")
    if b"MODULE    = apisetschema.dll" not in make or b"-Wb,--data-only" not in make:
        raise ValueError("Expected data-only Wine API-set Makefile")
    return {"schema_version":1,"source_commit":BASE,"package":"com.charoitx",
            "module":inspect((p/"apisetschema.dll").read_bytes()),"spec_sha256":sha(spec),
            "make_sha256":sha(make),"launch_ready":False,"prefix_created":False,
            "android_executed":False}
if __name__=="__main__":
    if len(sys.argv)!=2: raise SystemExit("usage: verify-apiset-bootstrap.py CI_OUTPUT")
    path=Path(sys.argv[1]); result=verify(path)
    (path/"verified-apiset.json").write_text(json.dumps(result,sort_keys=True,indent=2)+"\n")
    print("WINE_APISET_NAMESPACE_VERSION_6=PASS")
    print("APISET_SHA256="+result["module"]["sha256"])
    print("LAUNCH_READY=false")
