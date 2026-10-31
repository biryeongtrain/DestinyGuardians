"""Import selected, untrimmed Ghost lines; source remains read-only."""
import csv,json,hashlib,subprocess,wave
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path("/Users/qf/Downloads/Destiny-Ghost-Tutorial-2026-10-31/Destiny-Ghost-Tutorial-2026-10-31")
A=ROOT/"src/main/resources/assets/destiny"
ff=ROOT/"run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
selected=dict(awaken="80B603EC",walk="80B6051F",titan="80B5F1CC",hunter="80B5F1CE",warlock="80B5F1D0",light="80B5F1D4",equip="80B5E22A",fire="80B5F1F3",aim="80A623E8",traverse="80B5FA91",grenade="80B5E1D0",melee="80A8E804",class_ability="80B5F561",super="80B60C8C",ascend="80B5F344")
selected.update({"chirp1":"80A027C7","chirp2":"80A027C8","chirp3":"80A027C9"})
subs={r["dialogue_tag"]:r for r in csv.DictReader((SOURCE/"subtitles_en_ko.csv").open(encoding="utf-8-sig"))}
sounds=json.loads((A/"sounds.json").read_text()); report={}
for key,tag in selected.items():
 src=next((SOURCE/("audio/chirps" if key.startswith("chirp") else "audio/voice")).rglob("*"+tag+"*.wav")); row=subs.get(tag,{"korean":"", "english":"nonverbal Ghost link tickle"})
 with wave.open(str(src)) as w: duration=w.getnframes()/w.getframerate()
 dst=A/f"sounds/tutorial/ghost/{key}.ogg"; dst.parent.mkdir(parents=True,exist_ok=True)
 subprocess.run([str(ff),"-v","error","-y","-i",str(src),"-ac","1","-ar","48000","-af","loudnorm=I=-19:TP=-2:LRA=7","-c:a","libvorbis","-q:a","4",str(dst)],check=True)
 subprocess.run([str(ff),"-v","error","-i",str(dst),"-f","null","-"],check=True)
 sounds[f"tutorial.ghost.{key}"]={"sounds":[{"name":f"destiny:tutorial/ghost/{key}","stream":not key.startswith("chirp")}]}
 report[key]={"text":row["korean"],"english":row["english"],"ticks":round(duration*20)+10,"duration_sec":duration,"source":str(src.relative_to(SOURCE)),"source_sha256":hashlib.sha256(src.read_bytes()).hexdigest(),"output_sha256":hashlib.sha256(dst.read_bytes()).hexdigest(),"output_bytes":dst.stat().st_size}
(A/"sounds.json").write_text(json.dumps(sounds,ensure_ascii=False,indent=2)+"\n")
p=ROOT/"src/main/resources/data/destiny/tutorial/ghost_lines.json"; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
(ROOT/"art/ghost/w280/audio-manifest.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
(ROOT/"art/ghost/w280/sounds-fragment.json").write_text(json.dumps({k:v for k,v in sounds.items() if k.startswith("tutorial.ghost.")},indent=2)+"\n")
print("clips",len(report),"bytes",sum(r["output_bytes"] for r in report.values()))
