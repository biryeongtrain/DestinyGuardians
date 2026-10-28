from pathlib import Path
import hashlib,json,zipfile
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w221';jar=r/'build/libs/destiny-guardians-0.1.0+26.3.jar'
old=json.loads((q.parent/'w220/retained-shotgun-audio.json').read_text());rows=[]
with zipfile.ZipFile(jar) as z:
 for row in old['cues']:
  b=(r/'src/main/resources'/row['entry']).read_bytes();assert z.read(row['entry'])==b;rows.append({'entry':row['entry'],'sha256':hashlib.sha256(b).hexdigest()})
 sounds=json.loads(z.read('assets/destiny/sounds.json'));source=json.loads((r/'src/main/resources/assets/destiny/sounds.json').read_text())
 events={k:sounds[k] for k in old['events']};assert events==old['events']=={k:source[k] for k in events}
report={'jarSha256':hashlib.sha256(jar.read_bytes()).hexdigest(),'sourceAssetsMatchCurrentJar':True,'cues':rows,'events':events,'note':'Current W221 artifact retains W210 sample bytes and registry. W219 added the cancellable final emitter; this W221 art batch preserves it and does not repeat the W219 acoustic/event scenarios. This file checks asset identity and makes no acoustic listening claim.'}
(q/'retained-shotgun-audio.json').write_text(json.dumps(report,indent=2)+'\n');print({'shotgunCueBytesAndRegistryRetained':True})
