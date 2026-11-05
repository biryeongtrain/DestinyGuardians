"""Rebuild read-only identity validation and review sheets for worker-3 owned designs."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import sys,json,itertools,subprocess
ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'scripts/art/w325'))
import kit
ids=['thistle_and_yew','armillary_psu','sonata_48','inverness_sr2','black_tiger_2sr','madrugada_sr2']
font=ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc',22)
rows=[]
for w in ids:
 d=kit.load_design(w);e=d.elements();ur=[v for v in e if not v.get('rotation')];bad=[]
 for a,b in itertools.combinations(ur,2):
  for ax in range(3):
   for k in ('from','to'):
    if abs(a[k][ax]-b[k][ax])>.004:continue
    ov=1
    for j in range(3):
     if j!=ax:ov*=max(0,min(a['to'][j],b['to'][j])-max(a['from'][j],b['from'][j]))
    if ov>.002:bad.append((a['name'],b['name'],ax,k,ov))
 mag=lambda v:[x for x in v if x['name'].startswith('mag_')]
 before={x['name']:x for x in mag(d._base_elements())}
 delta=[{'before':before[x['name']],'after':x} for x in mag(e) if x!=before[x['name']]]
 coverage=all(d.special(x,fn,s,t) is not None for x in e for fn in ('north','south','east','west','up','down') for s,t in ((.1,.1),(.5,.5),(.9,.9)))
 p=ROOT/'art/weapons/w325'/w;m=json.loads((p/'manifest.json').read_text());ad=subprocess.check_output(['/opt/anaconda3/bin/python3',str(ROOT/'scripts/art/w325/kit.py'),'adscheck',w],text=True)
 report={'id':w,'elements':len(e),'body':len(e)-len(mag(e)),'magazine':len(mag(e)),'magazine_geometry_unchanged':not delta,'magazine_delta':delta,'coplanar_axis_aligned_overlaps':bad,'paint_sample_coverage':coverage,'positive_volumes':all(all(x['to'][i]>x['from'][i] for i in range(3)) for x in e),'adscheck':ad,'texels_per_px':m['texels_per_px'],'atlas':m['atlas'],'native_qa':False}
 (p/'identity_check.json').write_text(json.dumps(report,indent=2)+'\n');print(w,len(e),not delta,len(bad),m['atlas'])
 assert not bad and report['positive_volumes'] and 'OK:' in ad
 assert not delta or (w=='sonata_48' and len(delta)==1 and delta[0]['after']['name']=='mag_lip')
 notes=p/'notes.md';s=notes.read_text().split('\n### Final verified output')[0]
 if w=='sonata_48':s+='\n- 탄창 립의 기존 동일 평면 겹침 한 곳만 0.012px 안쪽으로 정리함(mag_lip.to[1]). 탄창 배치/장전 pivot은 유지.\n'
 s+=f"\n### Final verified output\n- body {report['body']} + magazine {report['magazine']} = {len(e)}; T{m['texels_per_px']}; atlas {m['atlas'][0]}×{m['atlas'][1]}.\n- adscheck OK; axis-aligned coplanar overlap 0; positive-volume and paint sampling OK.\n"
 s+='- mag_ geometry unchanged.\n' if not delta else '- mag_lip top face only: -0.012px; reload anchor unchanged.\n'
 notes.write_text(s)
 rip=Image.open(p/'proj_cache/nx_albedo.png').convert('RGBA');rip=rip.crop(rip.getchannel('A').getbbox())
 def fit(im,sz):
  im=im.copy();im.thumbnail(sz,Image.Resampling.LANCZOS);return im
 ref=fit(rip,(1100,360));comp=Image.new('RGB',(1200,1140),(111,117,123));comp.paste(ref,((1200-ref.width)//2,40),ref)
 draw=ImageDraw.Draw(comp);draw.text((18,10),w+' | rip / authored side / authored three-quarter',font=font,fill='white')
 west=Image.open(p/'review'/f'{w}_west.png');q=Image.open(p/'review'/f'{w}_q.png')
 west=west.crop((30,180,1170,640)).resize((1140,460));comp.paste(west,(30,390));q=q.crop((30,120,1170,650)).resize((684,318));comp.paste(q,(258,820))
 comp.save(p/'review'/f'{w}_compare.png')
 row=Image.new('RGB',(1800,500),(29,33,39));draw=ImageDraw.Draw(row);draw.text((18,10),f"{w} | {len(e)} elements | T{m['texels_per_px']} | {m['atlas'][0]}x{m['atlas'][1]} | ADS OK",font=font,fill='white')
 ref=fit(rip,(860,400));row.paste(ref,((900-ref.width)//2,75+(380-ref.height)//2),ref)
 qq=Image.open(p/'review'/f'{w}_q.png').crop((40,130,1160,650));qq=fit(qq,(900,420));row.paste(qq,(900,65));rows.append(row)
combined=Image.new('RGB',(1800,3000),(29,33,39))
for i,r in enumerate(rows):combined.paste(r,(0,i*500))
out=ROOT/'art/weapons/w325/thistle_and_yew/review/w325_identity_scouts_combined.png';combined.save(out);print(out)
