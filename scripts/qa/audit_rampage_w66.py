#!/usr/bin/env python3
"""Clone-only positive/negative controls; real source/outputs must stay byte-identical.
Run with bundled Python/Pillow. No private source downloads, app or game launch.
"""
import argparse
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
DATA='scripts/extract_rampage_w66.py'
HUD='scripts/generate_rampage_hud_w66.py'
AUDIO='scripts/qa/verify_reload_audio_w66.py'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def audit():
    # Load generator code without executing its CLI. Runtime files are never executed.
    hud=runpy.run_path(str(ROOT/HUD)); generated=hud['generate']()
    provenance=json.loads((ROOT/'art/weapons/w66/references/provenance.json').read_text())
    data_outputs=[DATA,'src/main/resources/destiny/weapons/w66-rampage.json',
                  'art/weapons/w66/reference-notes.md',*[f'art/weapons/w66/references/{n}.json'
                  for n in ('mechanics','socket-pools','provenance')]]
    audio=runpy.run_path(str(ROOT/AUDIO))
    files=set(data_outputs+[HUD,AUDIO,*audio['REVIEWED']])
    files.update(str(p.relative_to(ROOT)) for p in generated)
    files.update(json.loads((ROOT/'art/hud/w66-rampage/manifest.json').read_text())['reused_texture_sha256'])
    for record in provenance['sourceHashes'].values():
        p=Path(record['path']);p=p if p.is_absolute() else ROOT/p
        assert sha(p)==record['sha256'],p
        if p.is_relative_to(ROOT):files.add(str(p.relative_to(ROOT)))
    before={p:sha(ROOT/p) for p in files}
    result={'stage':'W66','dataConsumedPins':len(provenance['sourceHashes']),
            'realFilesChecked':len(files),'positiveControls':{},'negativeControls':{}}
    with tempfile.TemporaryDirectory(prefix='destiny-w66-audit-') as tmp:
        clone=Path(tmp)
        for p in files:
            (clone/p).parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/p,clone/p)

        def run(script,deny=False):
            if deny:
                code='''import sys,runpy
sys.dont_write_bytecode=True
from PIL import Image,ImageDraw,ImageFont
def guard(event,args):
    if event.startswith("socket."):raise RuntimeError("network forbidden")
    if event=="open" and (isinstance(args[1],str) and any(c in args[1] for c in "wax+") or args[2]&0x603):raise RuntimeError("write forbidden")
sys.addaudithook(guard)
sys.argv=[sys.argv[1],"--verify"]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
                cmd=[sys.executable,'-B','-c',code,str(clone/script)]
            else:cmd=[sys.executable,'-B',str(clone/script),*(['--verify'] if script!=AUDIO else [])]
            p=subprocess.run(cmd,cwd=clone,capture_output=True,text=True)
            return {'exitCode':p.returncode,'output':p.stdout+p.stderr}

        for script in (DATA,HUD):
            for denied in (False,True):
                label=Path(script).stem+('-read-only' if denied else '-clone')
                r=run(script,denied);assert r['exitCode']==0,r
                result['positiveControls'][label]=r
        for label,script,target,missing in [
                ('data-changed-input',DATA,'art/weapons/w40/definitions.json',False),
                ('data-missing-input',DATA,'art/weapons/w40/definitions.json',True),
                ('data-changed-output',DATA,'art/weapons/w66/reference-notes.md',False),
                ('hud-changed-output',HUD,'src/main/resources/assets/destiny/textures/item/hud/perk_rampage_w66_x2.png',False),
                ('hud-missing-dependency',HUD,'src/main/resources/assets/destiny/textures/item/hud/perk_buff_w61.png',True),
                ('audio-changed-reviewed-runtime',AUDIO,'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java',False)]:
            p=clone/target;saved=p.read_bytes()
            if missing:p.unlink()
            else:p.write_bytes(saved+b'\n')
            r=run(script);assert r['exitCode']!=0,label
            if script==AUDIO:assert 'W66 reviewed source drift' in r['output'],r
            p.write_bytes(saved);result['negativeControls'][label]=r
    assert before=={p:sha(ROOT/p) for p in files},'Real source/output changed'
    result['realInputsOutputsUnchanged']=True
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
