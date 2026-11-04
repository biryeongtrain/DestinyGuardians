#!/usr/bin/env python3
"""Offline named-source Ace import, deterministic Vorbis + pitch-preserving timed reload.
Original MP3s stay ignored. --verify creates temporary outputs only, never edits pack/source.
"""
from pathlib import Path
import argparse,hashlib,importlib.util,json,subprocess,tempfile,math
ROOT=Path(__file__).resolve().parents[2];ART=ROOT/"art/weapons/w83/audio";RES=ROOT/"src/main/resources"
sha=lambda b:hashlib.sha256(b).hexdigest()
enc=lambda v:(json.dumps(v,ensure_ascii=False,indent=2)+"\n").encode()

def generate():
 spec=importlib.util.spec_from_file_location("w83_audio_helpers",ROOT/"scripts/audio/import_sounds_w33.py");helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
 ff=helper.ffmpeg_path(None);sources=json.loads((ART/"source-pins.json").read_text());out={};records=[];events={};clips=[]
 with tempfile.TemporaryDirectory(prefix="destiny-w83-audio-") as tmp:
  helper.ROOT=Path(tmp);helper.RES=Path(tmp)
  for row in sources:
   source=ROOT/row["privatePath"];assert sha(source.read_bytes())==row["sourceSha256"]
   action=row["action"];key="weapon.ace_of_spades."+action
   cfg=dict(event=key,drive_id=row["id"],original_name=row["originalName"],source_folder=row["folder"],source_folder_id=row["folderId"],source_sha256=row["sourceSha256"],limitations="Named uploader Ace action, not independently acoustically identified; no Memento-specific variant attribution.")
   rec=helper.convert(cfg,source,ff);temp=Path(tmp)/rec["asset_path"]
   path="assets/destiny/sounds/w83/ace_of_spades/"+action+".ogg";out[RES/path]=temp.read_bytes();rec["asset_path"]="src/main/resources/"+path;rec["sound"]="destiny:w83/ace_of_spades/"+action
   events[key]=dict(sounds=[dict(name=rec["sound"],stream=False)])
   if action=="reload":
    duration=helper.stats(helper.decode(ff,temp))["duration_seconds"]
    for ticks in (55,39):
     factor=duration/(ticks/20);assert .5<=factor<=2
     target=Path(tmp)/f"reload-{ticks}.ogg"
     cmd=[ff,"-hide_banner","-v","error","-y","-i",str(temp),"-af",f"atempo={factor:.12f},apad,atrim=end_sample={ticks*1600}","-ac","1","-ar","32000","-map_metadata","-1","-c:a","libvorbis","-q:a","4","-fflags","+bitexact","-flags:a","+bitexact",str(target)]
     subprocess.run(cmd,check=True,capture_output=True);metrics=helper.stats(helper.decode(ff,target));assert metrics["clipped_samples"]==0 and metrics["sample_peak_dbfs"]<=-1
     assert abs(metrics["duration_seconds"]-ticks/20)<.001
     event=f"weapon.reload_w83.ace_of_spades.{ticks}";asset=f"assets/destiny/sounds/w83/reload/ace_of_spades_{ticks}.ogg";out[RES/asset]=target.read_bytes();events[event]=dict(sounds=[dict(name=f"destiny:w83/reload/ace_of_spades_{ticks}",stream=False)])
     clips.append(dict(id="ace_of_spades",ticks=ticks,event=event,sourceEvent=key,sourceSha256=sha(temp.read_bytes()),asset=asset))
     records.append(dict(kind="timed_reload",ticks=ticks,atempo=factor,metrics=metrics,asset=asset,sha256=sha(target.read_bytes())))
   records.append(rec)
 manifest=dict(stage="W83",authorization="User-authorized supplied public Drive sound folder; no redistribution license inferred.",sourceRoot="https://drive.google.com/drive/folders/1kWVlvhqvFkf_If5Q9Zd0mMIM1haa6u4l",sourcePins=sources,ffmpegSha256=sha(Path(ff).read_bytes()),events=events,reloadAudio=clips,records=records,limitations=["Uploader weapon/action names establish source selection, not acoustic listening or original balance timing.","Firefly uses existing supplied solar grenade impact surrogate; no exact Firefly or Memento proc recording inferred.","Reload atempo preserves pitch algorithmically; transients/time alignment remain approximation."],outputs={str(p.relative_to(ROOT)):sha(v) for p,v in out.items()})
 return out,manifest

def main():
 ap=argparse.ArgumentParser();ap.add_argument("--verify",action="store_true");args=ap.parse_args();out,m=generate();out[ART/"implementation.json"]=enc(m)
 # Append new keys only; no old event is renamed, transformed or removed.
 sounds=RES/"assets/destiny/sounds.json";table=json.loads(sounds.read_text())
 for key,value in m["events"].items():
  if key in table:assert table[key]==value,(key,"event drift")
  table[key]=value
 data=RES/"destiny/weapons/w83-exotics.json";rows=json.loads(data.read_text());assert len(rows)==1;rows[0]["reloadAudio"]=m["reloadAudio"]
 if args.verify:
  for p,b in out.items():assert p.read_bytes()==b,p
  assert all(table[k]==v for k,v in m["events"].items())
  assert json.loads(data.read_text())[0]["reloadAudio"]==m["reloadAudio"]
 else:
  for p,b in out.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  sounds.write_bytes(enc(table));data.write_bytes(enc(rows))
 print(json.dumps(dict(verified=args.verify,newOgg=len(m["outputs"]),newEvents=len(m["events"]),reloadTicks=[c["ticks"] for c in m["reloadAudio"]])))
if __name__=="__main__":main()
