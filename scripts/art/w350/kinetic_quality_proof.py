"""Comparison contacts and HUD derived from the real native JSON renders."""
import sys,json,hashlib
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3]
for wid in sys.argv[1:] or ['crimson','thorn','outbreak_perfected']:
 ad=ROOT/'art/weapons/w350'/wid;out=ad/'review-r2'
 for view in ['side','oblique']:
  sheet=Image.new('RGBA',(2400,748),(112,119,126,255));dr=ImageDraw.Draw(sheet)
  for col,(path,title) in enumerate([(ad/('source_material_'+view+'.png'),'READ-ONLY SOURCE / supplied shader color'),(out/('native_'+view+'.png'),'R2 ACTUAL NATIVE JSON / canonical finish / in-game QA pending')]):
   im=Image.open(path).convert('RGBA');sheet.alpha_composite(im,(col*1200,48));dr.text((col*1200+15,16),title,fill='white')
  sheet.convert('RGB').save(out/('source_vs_native_'+view+'.png'))
 side=Image.open(out/'native_side.png').convert('RGBA');box=side.getchannel('A').getbbox();icon=side.crop(box);icon.thumbnail((244,116),Image.Resampling.LANCZOS);canvas=Image.new('RGBA',(256,128));canvas.alpha_composite(icon,((256-icon.width)//2,(128-icon.height)//2));p=ROOT/f'src/main/resources/assets/destiny/textures/item/weapon/w350/{wid}_hud.png';canvas.save(p,optimize=True)
 manifest=json.loads((ad/'manifest.json').read_text());manifest['outputsSha256'][str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest();(ad/'manifest.json').write_text(json.dumps(manifest,separators=(',',':'))+'\n')
 contract=dict(resolution=[1200,700],sourceSide='source_material_side.png',sourceOblique='source_material_oblique.png',nativeSide='review-r2/native_side.png',nativeOblique='review-r2/native_oblique.png',nativeOpposite='review-r2/native_opposite_oblique.png',sourcePixelToModel=json.loads((ad/'r2-authored-solids.json').read_text())['sourceFrame'],directions=dict(side=[0,-1,0],oblique=[-.65,-1,.45],opposite=[.65,1,.45]),sourceBasis='Crimson/Outbreak +Y source view is mapped to native -Y; source X is negative native X. Thorn +X source view maps to native -Y; source Y is native X.',note='Orthographic width matches source 1200px view; manually authored profiles preserve source projected proportions, transverse solid depths are authored approximations.')
 (ad/'camera-contract-r2.json').write_text(json.dumps(contract,indent=2)+'\n')
 print(wid,'proof and HUD complete')
