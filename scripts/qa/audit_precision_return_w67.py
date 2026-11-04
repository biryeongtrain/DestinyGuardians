#!/usr/bin/env python3
"""Clone-only read-only generator and reviewed-audio guard positive/negative controls."""
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
DATA = 'scripts/extract_precision_return_w67.py'
AUDIO = 'scripts/qa/verify_reload_audio_w67.py'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def audit():
    provenance = json.loads((ROOT/'art/weapons/w67/references/provenance.json').read_text())
    audio = runpy.run_path(str(ROOT/AUDIO))
    files = {DATA, AUDIO, *audio['REVIEWED'],
             'src/main/resources/destiny/weapons/w67-precision-return.json',
             'art/weapons/w67/reference-notes.md',
             *[f'art/weapons/w67/references/{n}.json' for n in ('mechanics', 'socket-pools', 'provenance')]}
    sources = provenance['sourceHashes']
    for record in sources.values():
        p = Path(record['path']); p = p if p.is_absolute() else ROOT/p
        assert sha(p) == record['sha256'], p
        if p.is_relative_to(ROOT): files.add(str(p.relative_to(ROOT)))
    before = {p: sha(ROOT/p) for p in files}
    result = dict(stage='W67', consumedPins=len(sources), realFilesChecked=len(files),
                  positiveControls={}, negativeControls={})
    with tempfile.TemporaryDirectory(prefix='destiny-w67-audit-') as tmp:
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
                ('changed-input', DATA, 'art/weapons/w40/definitions.json', False),
                ('missing-input', DATA, 'art/weapons/w40/definitions.json', True),
                ('changed-json-output', DATA, 'src/main/resources/destiny/weapons/w67-precision-return.json', False),
                ('changed-markdown-output', DATA, 'art/weapons/w67/reference-notes.md', False),
                ('changed-reviewed-runtime', AUDIO, 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java', False)]:
            p = clone/target; saved = p.read_bytes()
            if missing: p.unlink()
            else: p.write_bytes(saved+b'\n')
            r = run(script); assert r['exitCode'] != 0, name
            if script == AUDIO: assert 'W67 reviewed source drift' in r['output'], r
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
