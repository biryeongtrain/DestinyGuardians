#!/usr/bin/env python3
"""Capture genuine Copper Golem 26.3 framebuffer frames; never normalizes or hides HUD.

Run concurrently with a server-side cast. The JSON contains measured capture times,
not a claimed video FPS. Raw frames/contact sheets are scratch; select evidence separately.
"""
import argparse
import io
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from PIL import Image, ImageDraw

def get(path):
    with urllib.request.urlopen("http://127.0.0.1:8102/"+path,timeout=20) as response:
        return response.read()

def main():
    p=argparse.ArgumentParser()
    p.add_argument("name")
    p.add_argument("--seconds",type=float,default=3)
    p.add_argument("--interval",type=float,default=.12)
    p.add_argument("--out",type=Path,default=Path("/tmp/destiny-h15-frames"))
    a=p.parse_args(); directory=a.out/a.name;directory.mkdir(parents=True,exist_ok=True)
    state=json.loads(get("state"))
    if not state.get("inWorld"):raise RuntimeError("Client not in a world")
    start=time.monotonic(); frames=[];times=[]
    utc=datetime.now(timezone.utc).isoformat()
    while time.monotonic()-start<a.seconds:
        before=time.monotonic()-start
        raw=get("screenshot");frame=Image.open(io.BytesIO(raw)).convert("RGB")
        (directory/f"{len(frames):03}.png").write_bytes(raw)
        times.append(before);frames.append(frame)
        time.sleep(max(0,a.interval-(time.monotonic()-start-before)))
    thumbs=[]
    for i,frame in enumerate(frames):
        t=frame.copy();t.thumbnail((427,239));canvas=Image.new("RGB",(427,261),"#191b20");canvas.paste(t,(0,22))
        ImageDraw.Draw(canvas).text((6,4),f"{i:02} / {times[i]:.3f}s",fill="white");thumbs.append(canvas)
    columns=4;rows=(len(thumbs)+columns-1)//columns
    sheet=Image.new("RGB",(427*columns,261*rows),"#191b20")
    for i,t in enumerate(thumbs):sheet.paste(t,((i%columns)*427,(i//columns)*261))
    sheet.save(directory/"contact.jpg",quality=88)
    scaled=[]
    for f in frames:
        f=f.copy();f.thumbnail((1024,574));scaled.append(f)
    durations=[max(1,round((times[i+1]-times[i])*1000)) for i in range(len(times)-1)]+[round(a.interval*1000)]
    scaled[0].save(directory/"sequence.webp",save_all=True,append_images=scaled[1:],duration=durations,loop=0,quality=80)
    metadata={"capture_start_utc":utc,"client_state":state,"frame_times_seconds":times,
              "source_size":list(frames[0].size),"hud_normalized":False,"frames":len(frames)}
    (directory/"frames.json").write_text(json.dumps(metadata,indent=2)+"\n")
    print(json.dumps({"name":a.name,"frames":len(frames),"directory":str(directory)}),flush=True)

if __name__=="__main__":main()
