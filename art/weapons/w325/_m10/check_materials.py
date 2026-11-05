import json,sys,hashlib
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT/'scripts/art/w325'));import kit
baseline=json.loads((ROOT/'art/weapons/w325/_m10/material_geometry_baseline.json').read_text());report={}
for w,basehash in baseline.items():
 d=kit.load_design(w);els=d.elements()
 h=hashlib.sha256(json.dumps(els,sort_keys=True).encode()).hexdigest();assert h==basehash,(w,'geometry drift')
 assert d.STYLE=='material'
 used={};painted=total=disabled=0
 for e in els:
  for f in kit.FACE_AXES:
   m=d.material(e['name'],f);assert m is not None
   if isinstance(m,str):key=m;m=d.MATERIALS[key]
   else:
    key=next(k for k,v in d.MATERIALS.items() if v['kind']==m['kind'] and v['color']==m['color'])
   assert m['kind'] in kit.Baker.KINDS and len(m['color'])==3
   used[key]=dict(d.MATERIALS[key]);disabled+=m.get('detail')==0
   for s in (.1,.3,.5,.7,.9):
    for t in (.1,.3,.5,.7,.9):total+=1;painted+=d.special(e,f,s,t) is not None
 assert painted/total<.30,(w,'whole face special fill')
 manifest=json.loads((kit.art(w)/'manifest.json').read_text());assert all(kit.sha(ROOT/p)==v for p,v in manifest['outputs_sha256'].items())
 report[w]={'style':'material','geometry_sha256':h,'geometry_unchanged':True,'materials':used,'special_sample_percent':round(100*painted/total,3),'detail_zero_faces':disabled,'atlas':manifest['atlas'],'T':d.T,'png_bytes':kit.atlas_path(w).stat().st_size,'adscheck':'OK','native_QA':'not run'}
(kit.ROOT/'art/weapons/w325/_m10/material_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS:',len(report),'weapons: unchanged geometry, explicit material on all faces, sparse special, output hashes')
print('PNG total',sum(v['png_bytes'] for v in report.values()))
