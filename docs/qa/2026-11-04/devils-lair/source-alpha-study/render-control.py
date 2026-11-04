from pathlib import Path
p=Path.cwd()/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py';ns={};s=p.read_text();exec(s[:s.index('for name in sys.argv')],ns)
ns['P']=Path('/tmp/devils-source-alpha');ns['MODELROOT']=ns['P'];ns['PREFIX']=''
ns['render']('marauder','baked')
