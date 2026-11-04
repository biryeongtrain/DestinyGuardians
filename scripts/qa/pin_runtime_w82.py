#!/usr/bin/env python3
"""Snapshot W82 source after tests. Verification remains read-only."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 previous=json.loads((ROOT/'art/hud/w81-damage-feedback/implementation.json').read_text())
 paths=set(previous['sha256'])
 for folder in ['src/main/java','src/gametest/java','src/test/java','art/weapons/w82']:
  paths.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).rglob('*') if p.is_file() and p.name!='implementation.json')
 paths.update(str(p.relative_to(ROOT)) for p in (ROOT/'scripts/qa').glob('*w82*.py'))
 paths.add('src/gametest/resources/fabric.mod.json')
 hashes={p:sha(ROOT/p) for p in sorted(paths)}
 result=dict(stage='W82',baseline='W81',jarSha256=sha(ROOT/'build/libs/destiny-guardians-0.1.0+26.3.jar'),
 newClientAssets=0,wholeGoalAchieved=False,sha256=hashes)
 (ROOT/'art/weapons/w82/implementation.json').write_text(json.dumps(result,indent=2)+'\n')
 changed=[p for p,h in previous['sha256'].items() if hashes.get(p)!=h]
 out=dict(previousPins=len(previous['sha256']),currentPins=len(hashes),changedPreviousPins=changed,
 addedPins=sorted(set(hashes)-set(previous['sha256'])))
 (ROOT/'docs/qa/2026-10-25/w82/source-delta.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps(dict(pins=len(hashes),changed=changed,added=len(out['addedPins']))))
if __name__=='__main__':main()
