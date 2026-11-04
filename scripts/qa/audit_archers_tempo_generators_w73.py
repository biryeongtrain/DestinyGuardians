#!/usr/bin/env python3
"""Isolated clone verification controls. Never modifies real generator inputs/outputs.
Verification runs with file writes, mkdir and socket networking rejected.
"""
import sys
sys.dont_write_bytecode=True
import argparse,contextlib,hashlib,io,json,runpy,socket,tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[2]
def sha(b):return hashlib.sha256(b).hexdigest()
def snapshot(root):
    return {str(p.relative_to(root)):(sha(p.read_bytes()),p.stat().st_mtime_ns) for p in root.rglob("*") if p.is_file()}
def blocked(*a,**k):raise AssertionError("Verification attempted a write, mkdir or network connection")
def invoke(main,argv):
    buf=io.StringIO()
    with patch.object(sys,"argv",argv),patch.object(Path,"write_bytes",blocked),patch.object(Path,"write_text",blocked),patch.object(Path,"mkdir",blocked),patch.object(socket.socket,"connect",blocked),patch("socket.create_connection",blocked),contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):
        try:result=main();ok=result in (None,0)
        except SystemExit as error:ok=error.code in (None,0)
    return ok,buf.getvalue()
def audit():
    reports=[]
    data=runpy.run_path(str(ROOT/"scripts/extract_archers_tempo_w73.py"))
    outputs,_=data["extract"](SimpleNamespace(root=ROOT,sources_dir=ROOT/"run/private-sources/w73"))
    source_before={str(p):sha(p.read_bytes()) for p in (ROOT/"run/private-sources/w73").iterdir() if p.is_file()}
    for name,value in outputs.items():assert (ROOT/name).read_bytes()==data["encoded"](value)
    with tempfile.TemporaryDirectory(prefix="destiny-w73-data-control-") as t:
        clone=Path(t)
        for name,value in outputs.items():p=clone/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data["encoded"](value))
        argv=["extract_archers_tempo_w73.py","--verify","--root",str(ROOT),"--output-root",str(clone)]
        before=snapshot(clone);ok,log=invoke(data["main"],argv);assert ok and snapshot(clone)==before
        reports.append(dict(generator="data",case="positive-clone",passed=True,readOnly=True))
        for name in outputs:
            p=clone/name;raw=p.read_bytes();p.write_bytes(raw+b"\n");before=snapshot(clone)
            ok,log=invoke(data["main"],argv);assert not ok and snapshot(clone)==before
            reports.append(dict(generator="data",case="changed-output",path=name,passed=True,readOnly=True));p.write_bytes(raw)
        p=clone/next(iter(outputs));raw=p.read_bytes();p.unlink();before=snapshot(clone)
        ok,log=invoke(data["main"],argv);assert not ok and snapshot(clone)==before
        reports.append(dict(generator="data",case="missing-output",passed=True,readOnly=True))
    hud=runpy.run_path(str(ROOT/"scripts/generate_archers_tempo_hud_w73.py"));real=hud["generate"]()
    real_before={str(p):sha(p.read_bytes()) for p in real}
    with tempfile.TemporaryDirectory(prefix="destiny-w73-hud-control-") as t:
        clone=Path(t)
        for p,raw in real.items():q=clone/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(raw)
        manifest=json.loads(real[ROOT/"art/hud/w73-archers-tempo/manifest.json"])
        for p in manifest["reused_texture_sha256"]:
            q=clone/p;q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes((ROOT/p).read_bytes())
        g=hud["main"].__globals__;g.update(ROOT=clone,ASSETS=clone/"src/main/resources/assets/destiny",ART=clone/"art/hud/w73-archers-tempo")
        argv=["generate_archers_tempo_hud_w73.py","--verify"]
        before=snapshot(clone);ok,log=invoke(hud["main"],argv);assert ok and snapshot(clone)==before
        reports.append(dict(generator="hud",case="positive-clone",passed=True,readOnly=True))
        for p in real:
            q=clone/p.relative_to(ROOT);raw=q.read_bytes();q.write_bytes(raw+b"\n");before=snapshot(clone)
            ok,log=invoke(hud["main"],argv);assert not ok and snapshot(clone)==before
            reports.append(dict(generator="hud",case="changed-output",path=str(p.relative_to(ROOT)),passed=True,readOnly=True));q.write_bytes(raw)
        q=clone/"src/main/resources/assets/destiny/items/gui/hud/perk_archers_tempo_w73_extra.json";q.write_text("{}\n");before=snapshot(clone)
        ok,log=invoke(hud["main"],argv);assert not ok and snapshot(clone)==before
        reports.append(dict(generator="hud",case="unexpected-extra-file",passed=True,readOnly=True))
    assert source_before=={str(p):sha(p.read_bytes()) for p in (ROOT/"run/private-sources/w73").iterdir() if p.is_file()}
    assert real_before=={str(p):sha(p.read_bytes()) for p in real}
    return dict(stage="W73",scenarios=reports,scenarioCount=len(reports),realInputsAndOutputsUnchanged=True,
                filesystemWritesAndMkdirBlockedDuringVerify=True,networkConnectBlockedDuringVerify=True,nativeClientEvidence=False)
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path,required=True);a=p.parse_args();r=audit()
    a.out.write_text(json.dumps(r,indent=2)+"\n");print(json.dumps(dict(stage="W73",cases=r["scenarioCount"],status="PASS")))
