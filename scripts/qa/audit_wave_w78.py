#!/usr/bin/env python3
"""Disposable read-only/source-corruption controls for the W78 verifier; no builds or network."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,importlib.util,json,tempfile,shutil,socket,urllib.request
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location("wave_verify",ROOT/"scripts/verify_wave_w78.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
def forbidden(*a,**kw):raise AssertionError("No writes/network during verification")
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--out",type=Path,required=True);a=p.parse_args();rows=[]
    for name in ["positive","profile-length-drift","missing-profile","intrinsic-identity-drift","official-index-drift","missing-cache"]:
        with tempfile.TemporaryDirectory(prefix="destiny-w78-verifier-") as tmp:
            root=Path(tmp)
            for file in module.PINS:
                target=root/file;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/file,target)
            # Small non-cache pinned inputs in the source index are preservation inputs as well.
            index=json.loads((ROOT/"art/weapons/w78/references/cached-source-index.json").read_text())
            for row in index["files"]:
                if row["path"].startswith("run/"):continue
                target=root/row["path"];target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/row["path"],target)
            if name=="profile-length-drift":
                target=root/"src/main/resources/destiny/weapons/w78-wave.json";d=json.loads(target.read_text());d["weapons"][0]["length"]=22;target.write_text(json.dumps(d))
            if name=="missing-profile":(root/"src/main/resources/destiny/weapons/w78-wave.json").unlink()
            if name=="intrinsic-identity-drift":
                target=root/"art/weapons/w78/references/pinned-identities.json";d=json.loads(target.read_text());d["weapons"][0]["frameHash"]=3690882495;target.write_text(json.dumps(d))
            if name=="official-index-drift":
                target=root/"art/weapons/w78/references/cached-source-index.json";d=json.loads(target.read_text());d["files"][0]["sha256"]="0"*64;target.write_text(json.dumps(d))
            sources=ROOT/"run/private-sources/w73" if name!="missing-cache" else root/"absent-cache"
            before={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob("*") if f.is_file()}
            error=None
            try:
                with patch.object(Path,"write_text",forbidden),patch.object(Path,"write_bytes",forbidden),patch.object(Path,"mkdir",forbidden),patch.object(socket,"socket",forbidden),patch.object(urllib.request,"urlopen",forbidden):
                    module.verify(root,sources)
            except (ValueError,FileNotFoundError) as e:error=str(e)
            after={str(f.relative_to(root)):hashlib.sha256(f.read_bytes()).hexdigest() for f in root.rglob("*") if f.is_file()}
            assert before==after and ((error is None)==(name=="positive")),(name,error)
            rows.append(dict(control=name,passed=True,rejected=error is not None,reason=error,unchanged=True,writesAndNetworkBlocked=True))
    a.out.write_text(json.dumps(dict(stage="W78",controls=rows,allPassed=True),indent=2)+"\n");print("W78 verifier controls:",len(rows),"passed")
if __name__=="__main__":main()
