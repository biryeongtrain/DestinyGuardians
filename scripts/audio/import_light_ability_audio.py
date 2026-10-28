#!/usr/bin/env python3
"""Import selected, source-pinned Light Ability single-WEM cues; never mix a bank."""
import argparse, array, hashlib, json, math, struct, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE_NAME="Destiny-Light-Abilities-2026-10-28"
CUE_SHA="2e0272bdaf54ef9253e6163e5d5f092c0692a96f9242fdb5f731b1786dc14aad"
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,o):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+"\n")
def command(ffmpeg,args):return subprocess.run(["rtk","proxy",str(ffmpeg),"-hide_banner","-v","error",*args],check=True,capture_output=True).stdout
def decode(ffmpeg,p):
 a=array.array("f",command(ffmpeg,["-i",str(p),"-f","f32le","-acodec","pcm_f32le","-"]))
 if not a or any(not math.isfinite(x) for x in a):raise ValueError("Invalid PCM: "+str(p))
 return {"samples":len(a),"peak":max(abs(x) for x in a),"rms":math.sqrt(sum(x*x for x in a)/len(a))}
def main():
 ap=argparse.ArgumentParser();ap.add_argument("--source",type=Path,required=True);ap.add_argument("--root",type=Path,default=ROOT);ap.add_argument("--ffmpeg",type=Path,required=True);ap.add_argument("--check",action="store_true");a=ap.parse_args()
 root=a.root.resolve();res=root/"src/main/resources";cues=a.source/"CUE-SHEETS.json"
 if sha(cues)!=CUE_SHA:raise ValueError("Cue sheet changed; review the new delivery")
 lookup={(x["group"],x["sound"]):x for x in read(cues)};sounds_path=res/"assets/destiny/sounds.json";sounds=read(sounds_path);before=json.loads(json.dumps(sounds));records=[];unique={}
 for klass in ["hunter","titan","warlock"]:
  selection=read(root/("art/audio/w233/"+klass+"-selection.json"))
  for binding in selection["bindings"]:
   cue=lookup[binding["group"],binding["sound"]]
   if cue.get("commonCandidate") or cue["name"]==cue["sound"]:raise ValueError("Unresolved/common candidate must not be auto assigned")
   if binding["status"] not in ("source_clip","named_candidate") or (binding["status"]=="source_clip" and not cue["sourceFrames"]):raise ValueError("Invalid evidence label")
   f=next(x for x in cue["files"] if x["tag"]==binding["wem"]);source=a.source/f["file"]
   if sha(source)!=f["sha256"]:raise ValueError("Source hash mismatch: "+str(source))
   event=binding["event"]
   if not event.startswith(klass+"."):raise ValueError("Class scope mismatch")
   asset="light_w233/"+binding["wem"].lower();dest=res/("assets/destiny/sounds/"+asset+".ogg")
   if asset not in unique:
    if not a.check:
     dest.parent.mkdir(parents=True,exist_ok=True);command(a.ffmpeg,["-y","-i",str(source),"-vn","-af","volume=0.5","-ac","1","-ar","48000","-c:a","libvorbis","-q:a","5",str(dest)])
    data=dest.read_bytes();i=data.index(b"\x01vorbis");channels=data[i+11];rate=struct.unpack_from("<I",data,i+12)[0]
    if channels!=1 or rate!=48000:raise ValueError("Expected mono Vorbis 48kHz")
    pcm=decode(a.ffmpeg,dest)
    if pcm["peak"]<=0 or pcm["peak"]>=1:raise ValueError("Silent/clipped output: "+asset)
    if abs(pcm["samples"]/rate-f["duration"])>.08:raise ValueError("Duration drift")
    unique[asset]={"sha256":sha(dest),"channels":channels,"sampleRate":rate,**pcm}
   definition={"sounds":[{"name":"destiny:"+asset,"stream":False,"attenuation_distance":32}]}
   old=sounds.get(event)
   if a.check and old!=definition:raise ValueError("Mapping mismatch: "+event)
   sounds[event]=definition
   records.append({**binding,"sourceName":cue["name"],"nameStatus":cue["nameStatus"],"confidence":cue["confidence"],"sourceFrames":cue["sourceFrames"],"sequenceTimings":cue["sequenceTimings"],"sourceFile":f["file"],"sourceSha256":f["sha256"],"bank":cue["bank"],"output":"assets/destiny/sounds/"+asset+".ogg","processed":unique[asset],"previousDefinition":old if not a.check else None})
 if len({x["event"] for x in records})!=len(records):raise ValueError("Duplicate event binding")
 provenance_path=root/"art/audio/w233/applied.json"
 if not a.check:
  write(sounds_path,sounds);write(provenance_path,{"sourceDelivery":SOURCE_NAME,"cueSheetSha256":CUE_SHA,"processing":"single selected WEM; mono 48000Hz Vorbis q5; gain0.5; no trim, mix, loop or tempo change","identityLimit":"FNV name candidates remain candidates. Wwise container/layer reconstruction and original-game A/B listening are not certified.","bindings":records})
 else:
  previous=read(provenance_path);assert previous["cueSheetSha256"]==CUE_SHA
  assert {x["event"]:x["processed"]["sha256"] for x in previous["bindings"]}=={x["event"]:x["processed"]["sha256"] for x in records}
 print(json.dumps({"checked":a.check,"bindings":len(records),"uniqueMonoFiles":len(unique),"decodedAllSelected":True,"sourcePinned":True}))
if __name__=="__main__":main()
