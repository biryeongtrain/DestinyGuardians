from pathlib import Path
from PIL import Image,ImageDraw
import json,sys
root=Path(sys.argv[1]);out=root/"screenshots";out.mkdir(exist_ok=True)
sheet=Image.new("RGB",(1920,4*260),(23,27,34));draw=ImageDraw.Draw(sheet);chosen=[]
for row,mode in enumerate(["hit","protected","miss","kill"]):
 d=json.loads((root/"sequences"/("w223-hit-"+mode+".json")).read_text());data=json.loads(d["stdout"]);files=[root/"frames"/c["file"] for c in data["captures"]]
 for col,path in enumerate(files[:5]):
  im=Image.open(path).convert("RGB");w,h=im.size;crop=im.crop((w//2-192,h//2-112,w//2+192,h//2+112));sheet.paste(crop,(col*384,row*260+32));draw.text((col*384+8,row*260+8),mode+" / "+path.stem.rsplit("-",1)[-1],fill="white");chosen.append(str(path.relative_to(root)))
sheet.save(out/"hit-confirmation-review.png");(out/"hit-selected-frames.json").write_text(json.dumps(chosen,indent=2)+"\n")
