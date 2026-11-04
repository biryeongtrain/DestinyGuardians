#!/usr/bin/env python3
"""Original Honed Edge count feed glyphs; no countdown for a shot-limited buff.
Offline preview is not an in-game framebuffer. --verify does not write.
"""
from pathlib import Path
import argparse,hashlib,io,json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];RES=ROOT/"src/main/resources/assets/destiny";ART=ROOT/"art/weapons/w84/hud"
FONT=Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf");FONT_SHA="fcf34b330033e26c06e9bd466bea5a3e4b2f39272972275369beb7d8b257ed57"
enc=lambda v:(json.dumps(v,indent=2)+"\n").encode();sha=lambda b:hashlib.sha256(b).hexdigest()
def generate():
 assert sha(FONT.read_bytes())==FONT_SHA
 out={}
 for name,label,w,h in [("perk_honed_edge_w84","Honed Edge",118,24)]:
  im=Image.new("RGBA",(w*4,h*4));d=ImageDraw.Draw(im)
  for size in range(21 if w>10 else 18,0,-1):
   font=ImageFont.truetype(str(FONT),size*4);b=d.textbbox((0,0),label,font=font)
   if b[2]-b[0]<=im.width-8 and b[3]-b[1]<=im.height-8:break
  else:raise RuntimeError("No readable glyph size")
  d.text(((im.width-b[2]+b[0])/2-b[0],(im.height-b[3]+b[1])/2-b[1]),label,font=font,fill="white");im=im.resize((w,h),Image.Resampling.LANCZOS);stream=io.BytesIO();im.save(stream,format="PNG")
  out[RES/f"textures/item/hud/{name}.png"]=stream.getvalue()
  out[RES/f"models/gui/hud/{name}.json"]=enc({"gui_light":"front","textures":{"layer0":f"destiny:item/hud/{name}"},"elements":[{"from":[0,0,8],"to":[16,16,8],"faces":{f:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0} for f in ("north","south")}}]})
  out[RES/f"items/gui/hud/{name}.json"]=enc({"model":{"type":"minecraft:model","model":f"destiny:gui/hud/{name}","tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}})
 manifest=dict(stage="W84",font=str(FONT),fontSha256=FONT_SHA,policy="Authored system-font glyphs; actual fused-round multiplier, not an invented duration; no radar implementation claimed.",outputs={str(p.relative_to(ROOT)):sha(b) for p,b in out.items()});out[ART/"manifest.json"]=enc(manifest);return out
if __name__=="__main__":
 ap=argparse.ArgumentParser();ap.add_argument("--verify",action="store_true");a=ap.parse_args();out=generate()
 for p,b in out.items():
  if a.verify:assert p.read_bytes()==b,p
  else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 print(json.dumps(dict(verified=a.verify,files=len(out))))
