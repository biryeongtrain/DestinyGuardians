#!/usr/bin/env python3
"""Read-only W76 generator controls in disposable clones; no native rendering claims."""
import argparse, hashlib, json, runpy, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/generate_vanilla_hud_w76.py"

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snap(root, paths): return {p: (sha(root/p), (root/p).stat().st_mtime_ns) for p in paths if (root/p).is_file()}
def audit():
    m = runpy.run_path(str(ROOT/SCRIPT)); _, outputs = m["outputs"]()
    paths = [SCRIPT, m["INPUT"], *outputs]
    original = snap(ROOT, paths)
    guard = r'''import runpy,sys
sys.dont_write_bytecode=True
def guard(event,args):
    if event=="open" and ((isinstance(args[1],str) and any(c in args[1] for c in "wax+")) or args[2] & (1|2|64|512|1024)):
        raise RuntimeError("write blocked")
    if event in ("os.mkdir","os.remove","os.rename","socket.connect","socket.bind"):
        raise RuntimeError("mutation/network blocked: "+event)
sys.addaudithook(guard)
sys.argv=[sys.argv[1],"--verify"]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
    controls=[]
    for case in ("positive", "corrupt-png", "missing-locale", "translation-key-drift", "sprite-scope-drift"):
        with tempfile.TemporaryDirectory(prefix="destiny-w76-generator-") as td:
            root=Path(td)
            for p in paths:
                (root/p).parent.mkdir(parents=True, exist_ok=True); (root/p).write_bytes((ROOT/p).read_bytes())
            if case=="corrupt-png":
                p=root/"src/main/resources/assets/minecraft/textures/gui/sprites/hud/hotbar.png";p.write_bytes(p.read_bytes()+b"corrupt")
            elif case=="missing-locale":
                (root/"src/main/resources/assets/minecraft/lang/ko_kr.json").unlink()
            elif case=="translation-key-drift":
                (root/"src/main/resources/assets/minecraft/lang/en_us.json").write_text('{"item.minecraft.apple":""}')
            elif case=="sprite-scope-drift":
                p=root/m["INPUT"];d=json.loads(p.read_text());d["sprites"][0]["path"]="assets/minecraft/textures/gui/sprites/hud/armor_full.png";p.write_text(json.dumps(d))
            before=snap(root,paths)
            result=subprocess.run([sys.executable,"-c",guard,str(root/SCRIPT)],capture_output=True,text=True)
            assert (result.returncode==0)==(case=="positive"),(case,result.stdout,result.stderr)
            assert snap(root,paths)==before,case
            controls.append(dict(case=case,passed=True,exitCode=result.returncode,readOnly=True))
    assert snap(ROOT,paths)==original
    return dict(stage="W76",controls=controls,networkAndWritesBlockedDuringVerify=True,originalFilesUnchanged=True)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path);a=p.parse_args();result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
