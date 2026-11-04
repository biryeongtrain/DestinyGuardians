#!/usr/bin/env python3
"""Explicitly snapshot W81 source pins after tests; read-only verifier is separate."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 previous=json.loads((ROOT/'art/weapons/w80/implementation.json').read_text())
 paths=set(previous['sha256'])
 for folder in ['src/main/java','src/gametest/java','src/test/java','art/hud/w81-damage-feedback']:
  paths.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='implementation.json')
 paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/qa').glob('*w81*.py'))
 paths.update(['src/gametest/resources/fabric.mod.json',
 'scripts/qa/pin_runtime_w81.py','scripts/qa/verify_runtime_w81.py'])
 hashes={p:sha(ROOT/p) for p in sorted(paths)}
 result=dict(stage='W81',baseline='W80',jarSha256=sha(ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar'),
 newClientAssets=0,wholeGoalAchieved=False,sha256=hashes)
 (ROOT/'art/hud/w81-damage-feedback/implementation.json').write_text(json.dumps(result,indent=2)+'\n')
 changed=[p for p,h in previous['sha256'].items() if hashes.get(p)!=h]
 out=dict(previousPins=len(previous['sha256']),currentPins=len(hashes),changedPreviousPins=changed,
 addedPins=sorted(set(hashes)-set(previous['sha256'])))
 (ROOT/'docs/qa/2026-10-24/w81/source-delta.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(dict(pins=len(hashes),changed=changed,added=len(out['addedPins']))))
if __name__=='__main__':main()
