#!/usr/bin/env python3
"""Clone-only Ammit reload generator audit; no real model/texture edits."""
import argparse
import hashlib
import json
import runpy
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = 'scripts/generate_reload_models_w69.py'
AUDIO = 'scripts/qa/verify_reload_audio_w69.py'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit():
    manifest = json.loads((ROOT/'art/weapons/w69/manifest.json').read_text())
    files = {DATA, 'art/weapons/w69/manifest.json', *manifest['sourceSha256'], *manifest['sha256']}
    sources = manifest['sourceSha256']
    for path, expected in sources.items():
        assert sha(ROOT/path) == expected, path
    before = {p: sha(ROOT/p) for p in files}
    result = dict(stage='W69', consumedPins=len(sources), realFilesChecked=len(files),
                  positiveControls={}, negativeControls={})
    with tempfile.TemporaryDirectory(prefix='destiny-w69-audit-') as tmp:
        clone = Path(tmp)
        for p in files:
            (clone/p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/p, clone/p)

        def run(script, deny=False):
            if deny:
                code = '''import sys,runpy
sys.dont_write_bytecode=True
def guard(event,args):
    if event.startswith("socket."):raise RuntimeError("network forbidden")
    if event=="open" and (isinstance(args[1],str) and any(c in args[1] for c in "wax+") or args[2]&0x603):raise RuntimeError("write forbidden")
sys.addaudithook(guard)
sys.argv=[sys.argv[1],"--verify"]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
                cmd = [sys.executable, '-B', '-c', code, str(clone/script)]
            else:
                cmd = [sys.executable, '-B', str(clone/script), *(['--verify'] if script == DATA else [])]
            p = subprocess.run(cmd, cwd=clone, capture_output=True, text=True)
            return dict(exitCode=p.returncode, output=p.stdout+p.stderr)

        for deny in (False, True):
            r = run(DATA, deny); assert r['exitCode'] == 0, r
            result['positiveControls']['data-read-only' if deny else 'data-clone'] = r
        for name, script, target, missing in [
                ('changed-input', DATA, 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json', False),
                ('missing-input', DATA, 'src/main/resources/assets/destiny/models/weapon/auto_rifle/ammit_ar2.json', True),
                ('changed-model-output', DATA, 'src/main/resources/assets/destiny/models/weapon_reload_w69/ammit_ar2_10_magazine_native.json', False),
                ('changed-item-output', DATA, 'src/main/resources/assets/destiny/items/weapon_reload_w69/ammit_ar2.json', False)]:
            p = clone/target; saved = p.read_bytes()
            if missing: p.unlink()
            else: p.write_bytes(saved+b'\n')
            r = run(script); assert r['exitCode'] != 0, name
            result['negativeControls'][name] = r
            p.write_bytes(saved)
    assert before == {p: sha(ROOT/p) for p in files}, 'Real source/output changed'
    result['realInputsOutputsUnchanged'] = True
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--out', type=Path); a = p.parse_args()
    result = audit()
    if a.out: a.out.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, sort_keys=True))
