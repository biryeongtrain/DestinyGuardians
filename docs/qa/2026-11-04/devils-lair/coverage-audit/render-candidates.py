from pathlib import Path
import json,shutil
helper=Path.cwd()/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py';s=helper.read_text();s=s[:s.index('for name in sys.argv')]
s=s.replace("[('front',0),('side',90),('threequarter',35)]", "[('threequarter',35)]")
ns={};exec(s,ns)
rows=json.loads(Path('/tmp/devils-coverage-audit/audit.json').read_text())
for row in rows:
 if not row.get('ordinaryTransparentCentres'):continue
 name=row['name'];p=Path('/tmp/devils-coverage-audit')/name;before=p/'before';before.mkdir(exist_ok=True);shutil.copy2(p/('before-dl_'+name+'.bbmodel'),before/('dl_'+name+'.bbmodel'))
 ns['P']=p;ns['MODELROOT']=before;ns['PREFIX']='before_';ns['render'](name,'baked')
 ns['MODELROOT']=p;ns['PREFIX']='after_';ns['render'](name,'baked')
 print('RENDERED',name,flush=True)
