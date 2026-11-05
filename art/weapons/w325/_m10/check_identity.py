from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/art/w325'));import kit
ids=['cup_bearer_sa_2','reginar_b','weaver_c','plemusa_b','stampede_mk_32','future_imperfect','rest_for_the_wicked']
report={}
for w in ids:
 d=kit.load_design(w);els=d.elements();doc=json.loads(kit.skin_path(w).read_text());manifest=json.loads((kit.art(w)/'manifest.json').read_text())
 assert len(els)==sum(map(len,doc['parts'].values())),w
 assert len({e['name'] for e in els})==len(els),w
 if getattr(d,'STYLE','pixel')=='material':
  assert all(d.material(e['name'],f) is not None for e in els for f in kit.FACE_AXES),w
 else:
  assert all(d.special(e,f,.31,.63) is not None for e in els for f in kit.FACE_AXES),w
 assert all(all(a<b for a,b in zip(e['from'],e['to'])) for e in els),w
 assert all(kit.sha(ROOT/p)==h for p,h in manifest['outputs_sha256'].items()),w
 for part in doc['parts'].values():
  for e in part:
   for f in e['faces'].values(): assert all(0<=x<=16 for x in f['uv']),w
 out={'parts':{k:len(v) for k,v in doc['parts'].items()},'atlas':doc['texture_size'],'T':d.T,'png_bytes':kit.atlas_path(w).stat().st_size,'ads':'OK','native_QA':'pending master'}
 if w in ('cup_bearer_sa_2','reginar_b','weaver_c'):
  tube=[e for e in els if e['name'].startswith(('tube','rear_tube','end_lip'))]
  out['rear_tube_zmax']=round(max(e['to'][2] for e in tube),4)
 report[w]=out
(ROOT/'art/weapons/w325/_m10/identity_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
