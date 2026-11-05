"""Worker-3 material R2 pass audit and side/source sheets; does not modify geometry."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,hashlib,subprocess,itertools,collections
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/art/w325'));import kit
ids=['thistle_and_yew','armillary_psu','sonata_48','inverness_sr2','black_tiger_2sr','madrugada_sr2']
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
rows=[];atlasrows=[]
def fit(im,sz):
 im=im.copy();im.thumbnail(sz,Image.Resampling.LANCZOS);return im
for w in ids:
 p=ROOT/'art/weapons/w325'/w;d=kit.load_design(w);els=d.elements();before=json.loads((p/'material_r2_baseline.json').read_text())
 geom=hashlib.sha256(json.dumps(els,sort_keys=True).encode()).hexdigest();assert geom==before['geometry_sha256'];assert d.T==before['source_manifest']['texels_per_px']
 assert hashlib.sha256((ROOT/'scripts/art/w325/kit.py').read_bytes()).hexdigest()==before['kit_sha256']
 mats={};counts=collections.Counter();disabled=[];samples=0;marks=0;bad=[]
 for e in els:
  for face in ('north','south','east','west','up','down'):
   m=d.material(e['name'],face);assert m is not None
   if isinstance(m,str):key=m;spec=d.MATERIALS[m]
   else:
    spec=m;key=next(k for k,v in d.MATERIALS.items() if v['kind']==m['kind'] and v['color']==m['color'])
   mats[key]=spec;counts[key]+=1
   if spec.get('detail')==0:disabled.append(e['name']+'/'+face)
   for s in (.125,.375,.625,.875):
    for t in (.125,.375,.625,.875):samples+=1;marks+=d.special(e,face,s,t) is not None
 ur=[e for e in els if not e.get('rotation')]
 for a,b in itertools.combinations(ur,2):
  for ax in range(3):
   for k in ('from','to'):
    if abs(a[k][ax]-b[k][ax])>.004:continue
    ov=1
    for j in range(3):
     if j!=ax:ov*=max(0,min(a['to'][j],b['to'][j])-max(a['from'][j],b['from'][j]))
    if ov>.002:bad.append((a['name'],b['name'],ax,k))
 assert not bad
 ad=subprocess.check_output(['/opt/anaconda3/bin/python3',str(ROOT/'scripts/art/w325/kit.py'),'adscheck',w],text=True);assert 'OK:' in ad
 manifest=json.loads((p/'manifest.json').read_text());assert manifest['atlas']==before['source_manifest']['atlas']
 for path,sha in manifest['outputs_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==sha
 report={'style':d.STYLE,'geometry_unchanged':True,'geometry_sha256':geom,'elements':len(els),'material_definitions':d.MATERIALS,'used_materials':sorted(mats),'faces_per_material':counts,'explicit_mapping_faces':sum(counts.values()),'source_relief_disabled_faces':disabled,'special_sample_fraction':marks/samples,'coplanar_overlaps':bad,'adscheck':ad,'atlas':manifest['atlas'],'T':d.T,'native_qa':False,'rubber_polymer_luma_gap':abs(sum(d.MATERIALS.get('lower',d.MATERIALS['polymer'])['color'][i]*v for i,v in enumerate((.299,.587,.114)))-sum(d.MATERIALS['rubber']['color'][i]*v for i,v in enumerate((.299,.587,.114))))}
 assert report['rubber_polymer_luma_gap']>=25
 (p/'material_r2_check.json').write_text(json.dumps(report,indent=2)+'\n');print(w,len(els),manifest['atlas'],'decals',round(marks/samples,4),'materials',sorted(mats))
 notes=p/'notes.md';s=notes.read_text().split('\n## W123 material R2 pass')[0]
 s+='\n## W123 material R2 pass (2026-11-05, supersedes flat identity paint)\n'
 s+='- STYLE=material. Whole-face special fills removed. Material colours sampled/selected from nx/px rip render; W123 Beloved/Gnawing Hunger grain and per-material shading are the style references.\n'
 for key in sorted(mats):
  v=d.MATERIALS[key];s+=f"- {key}: {v['kind']} RGB{tuple(v['color'])}, source relief detail={v['detail']}.\n"
 s+='- R2: exposed receiver sideplates, rails, trigger guards and port rims use metal/steel; rubber darkened against polymer. Hand-authored magazine channels, cooling slots, grip ribs and cartridge separators added as sparse texel lines. special retains logos/markings, sparse optic status pixels, limited camouflage stencils and port accents. Projection disabled on authored/base-adapted optics, added aperture walls and other mismatched faces (see material_r2_check.json).\n'
 s+=f"- Geometry hash unchanged; {len(els)} elements; atlas {manifest['atlas']}; T{d.T}; ADS OK; 0 axis-aligned coplanar overlaps.\n"
 s+='- Native Minecraft, FPS and dynamic PBR not checked. Material relief/brush shading is baked RGBA, not physically based reflection.\n'
 notes.write_text(s)
 rip=Image.open(p/'proj_cache/nx_albedo.png').convert('RGBA');rip=rip.crop(rip.getchannel('A').getbbox())
 row=Image.new('RGB',(1800,500),(29,33,39));dr=ImageDraw.Draw(row);dr.text((18,10),f"{w} | material R2 pass | T{d.T} | {manifest['atlas']} | source / model",font=font,fill='white')
 ref=fit(rip,(860,400));row.paste(ref,((900-ref.width)//2,75+(380-ref.height)//2),ref)
 qq=fit(Image.open(p/'review'/f'{w}_q.png').crop((40,130,1160,650)),(900,420));row.paste(qq,(900,65));rows.append(row);row.save(p/'review'/f'{w}_material_r2_compare.png')
 ar=Image.new('RGB',(1100,550),(26,30,35));dr=ImageDraw.Draw(ar);dr.text((10,5),w+' | material atlas',font=font,fill='white')
 tex=Image.open(kit.atlas_path(w));tex=fit(tex,(1024,500));ar.paste(tex,(10,42),tex);atlasrows.append(ar)
combined=Image.new('RGB',(1800,3000),(29,33,39))
for i,r in enumerate(rows):combined.paste(r,(0,i*500))
out=ROOT/'art/weapons/w325/thistle_and_yew/review/w325_material_r2_scouts_combined.png';combined.save(out)
atlas=Image.new('RGB',(2200,1650),(26,30,35))
for i,r in enumerate(atlasrows):atlas.paste(r,((i%2)*1100,(i//2)*550))
atlas.save(ROOT/'art/weapons/w325/thistle_and_yew/review/w325_material_r2_atlases.png')
print(out)
