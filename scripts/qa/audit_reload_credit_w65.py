#!/usr/bin/env python3
"""Isolated controls for the W65 read-only extractor and audio source guard.

Never mutates real inputs. A successful negative means the copied verifier
rejected tampering, not that altered source has been supported.
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

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = 'scripts/extract_reload_credit_w65.py'
AUDIO = 'scripts/qa/verify_reload_audio_w65.py'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit():
    module = runpy.run_path(str(ROOT / GENERATOR))
    outputs = [str(p.relative_to(ROOT)) for p in module['generate']()]
    files = [GENERATOR, *module['INPUTS'], *outputs]
    audio = runpy.run_path(str(ROOT / AUDIO))
    guarded = list(audio['CURRENT_FILES'])
    files = sorted(set(files + [AUDIO] + guarded))
    before = {p: digest(ROOT / p) for p in files}
    report = {'stage': 'W65', 'filesReconstructed': len(outputs),
              'inputPins': {p: before[p] for p in module['INPUTS']},
              'negativeControls': {}}
    with tempfile.TemporaryDirectory(prefix='destiny-w65-audit-') as tmp:
        clone = Path(tmp)
        for p in files:
            (clone / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / p, clone / p)

        def run(script, denied=False):
            if denied:
                code = '''import sys,runpy
sys.dont_write_bytecode=True
def guard(event,args):
    if event.startswith("socket."): raise RuntimeError("network forbidden")
    if event=="open" and (isinstance(args[1],str) and any(c in args[1] for c in "wax+") or args[2]&0x603):
        raise RuntimeError("write forbidden")
sys.addaudithook(guard)
sys.argv=[sys.argv[1],"--verify"]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
                cmd = [sys.executable, '-B', '-c', code, str(clone / script)]
            else:
                cmd = [sys.executable, '-B', str(clone / script), '--verify']
            p = subprocess.run(cmd, cwd=clone, capture_output=True, text=True)
            return {'exitCode': p.returncode, 'output': p.stdout + p.stderr}

        for label, denied in [('clonePositive', False), ('networkAndWriteForbiddenPositive', True)]:
            result = run(GENERATOR, denied)
            assert result['exitCode'] == 0, result
            report[label] = result
        for label, target, missing in [
                ('changed-input', module['INPUTS'][0], False),
                ('missing-input', module['INPUTS'][0], True),
                ('changed-output', outputs[0], False)]:
            p = clone / target
            saved = p.read_bytes()
            if missing:
                p.unlink()
            else:
                p.write_bytes(saved + b'\n')
            result = run(GENERATOR)
            assert result['exitCode'] != 0, label
            p.write_bytes(saved)
            report['negativeControls'][label] = result
        # This must fail before attempting W63 legacy reconstruction/ffmpeg.
        target = clone / guarded[0]
        target.write_bytes(target.read_bytes() + b'\n')
        p = subprocess.run([sys.executable, '-B', str(clone / AUDIO)], cwd=clone,
                           capture_output=True, text=True)
        result = {'exitCode': p.returncode, 'output': p.stdout + p.stderr}
        assert p.returncode != 0 and 'W65 reviewed source drift' in result['output'], result
        report['audioReviewedSourceNegative'] = result
    assert before == {p: digest(ROOT / p) for p in files}, 'Real source changed'
    report['realInputsAndOutputsUnchanged'] = True
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.out:
        args.out.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, sort_keys=True))
