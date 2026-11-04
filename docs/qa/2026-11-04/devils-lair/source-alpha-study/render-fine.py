from pathlib import Path
helper=Path.cwd()/'docs/qa/2026-11-03/devils-lair/models/surface-study/render-culled.py';s=helper.read_text();s=s[:s.index('for name in sys.argv')]
# Read each atlas resolution: the earlier helper assumes 2048 and cannot render a 4096 control as-is.
s=s.replace("model=json.loads((MODELROOT/('dl_'+name+'.bbmodel')).read_text());", "model=json.loads((MODELROOT/('dl_'+name+'.bbmodel')).read_text()); atlas_w=model['resolution']['width'];atlas_h=model['resolution']['height'];")
s=s.replace('x0/2048','x0/atlas_w').replace('x1/2048','x1/atlas_w').replace('y1/2048','y1/atlas_h').replace('y0uv/2048','y0uv/atlas_h')
ns={};exec(s,ns);ns['P']=Path('/tmp/devils-alpha-fine');ns['MODELROOT']=ns['P'];ns['PREFIX']='';ns['render']('marauder','baked')
