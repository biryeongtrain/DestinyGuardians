#!/usr/bin/env python3
"""Reproduce the user-authorized Deadfall video edits from a pinned, private AAC source.

No downloads, system audio capture, or automatic playback. Originals stay gitignored.
"""
import argparse, array, hashlib, json, math, shutil, subprocess, tempfile, wave, zipfile
from pathlib import Path
from import_sounds_w33 import decode, stats, ffmpeg_path, dump, sha

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "run/private-sources/w34"
RES = ROOT / "src/main/resources"
QA = ROOT / "docs/qa/2026-10-23/w34"
SOURCE_SHA = "4a6776d942b49a8fd614927b86ca93b79a89cee22809c733b3b566b0c714dd5f"
SOURCE_URL = "https://www.youtube.com/watch?v=O0uvtZMID9E&t=1050s"
RATE = 32000
# These are mix edits, not claims of isolated game stems or exact acoustic action labels.
EDITS = [
    ("start", 1047.17, 1047.48, 0, 20, "Leading Deadfall energy rise; activation assignment is provisional."),
    ("draw", 1047.48, 1047.82, 0, 16, "Following rising-energy region fitted to the server 0.35s draw; not an isolated bow-string stem."),
    ("fire", 1047.82, 1048.48, 0, 35, "Main transient and immediate decay in the Deadfall cast mix; other cast layers may remain."),
    ("impact", 1048.60, 1049.20, -2, 60, "Secondary transient/decay used as anchor impact. Off-screen impact identity is not independently verified."),
    ("end", 1049.25, 1049.70, -9, 150, "Authored quiet closing decay cut from the release tail, NOT an identified Deadfall shutdown recording."),
]
FILTERS = "highpass=f=40,lowpass=f=14000,afftdn=nr=6:nf=-46:tn=0"

def wav(path, samples):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = array.array("h", (round(max(-1, min(1, v))*32767) for v in samples))
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm.tobytes())

def extract(ffmpeg, source, start, end):
    raw = subprocess.run([ffmpeg,"-hide_banner","-v","error","-ss",str(start),"-i",str(source),
        "-t",str(round(end-start,6)),"-vn","-af",FILTERS,"-ac","1","-ar",str(RATE),"-f","f32le","-"],
        check=True,capture_output=True).stdout
    samples = array.array("f", raw)
    if len(samples) != round((end-start)*RATE) or any(not math.isfinite(x) for x in samples):
        raise ValueError("Unexpected decoded segment length or invalid PCM")
    return samples

def check(manifest):
    source = CACHE / manifest["source"]["cache_name"]
    if not source.exists() or sha(source.read_bytes()) != SOURCE_SHA:
        raise ValueError("Missing or changed private AAC source; do not change the source hash blindly")
    definitions = json.loads((RES/"assets/destiny/sounds.json").read_text())
    for key, record in manifest["events"].items():
        if sha((ROOT/record["asset_path"]).read_bytes()) != record["output"]["sha256"]:
            raise ValueError("Modified output: "+key)
        sequence = RES/"destiny/sounds/w36.json"
        active = json.loads(sequence.read_text())["events"].get(key, record) if sequence.exists() else record
        if definitions[key]["sounds"][0]["name"] != active["sound"]:
            raise ValueError("Video overlay inactive: "+key)
    return source

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,default=CACHE/"O0uvtZMID9E-source.m4a")
    ap.add_argument("--ffmpeg");ap.add_argument("--check",action="store_true")
    args=ap.parse_args();mf=RES/"destiny/sounds/w34.json"
    if args.check:
        check(json.loads(mf.read_text()));print("W34 historical video-derived edits verified with current sequence overlay");return
    if sha(args.source.read_bytes()) != SOURCE_SHA:
        raise SystemExit("Source SHA256 differs from the reviewed AAC; refusing to import")
    ff=ffmpeg_path(args.ffmpeg);CACHE.mkdir(parents=True,exist_ok=True)
    expected=CACHE/"O0uvtZMID9E-source.m4a"
    if args.source.resolve()!=expected.resolve():shutil.copy2(args.source,expected)
    records={};review=ROOT/"run/deliverables/w34-shadowshot"
    review.mkdir(parents=True,exist_ok=True)
    preview=array.array("f");silence=array.array("f",[0.0])*round(.5*RATE)
    with tempfile.TemporaryDirectory(dir=CACHE) as tmp:
        for i,(action,start,end,extra,fadeout,note) in enumerate(EDITS,1):
            samples=extract(ff,expected,start,end);before=stats(samples)
            gain=min(9.,-21-before["rms_dbfs"],-6-before["sample_peak_dbfs"])+extra
            scale=10**(gain/20);fadein=round(.002*RATE);fade=round(fadeout*.001*RATE)
            for j in range(len(samples)):
                samples[j]*=scale*min(1.,(j+1)/fadein,(len(samples)-j)/fade)
            output=Path(tmp)/(action+".ogg")
            cmd=[ff,"-hide_banner","-v","error","-y","-f","f32le","-ar",str(RATE),"-ac","1","-i","pipe:0",
                 "-map_metadata","-1","-c:a","libvorbis","-q:a","4","-fflags","+bitexact","-flags:a","+bitexact",str(output)]
            for attempt in range(3):
                subprocess.run(cmd,input=samples.tobytes(),capture_output=True,check=True)
                decoded=decode(ff,output);measurement=stats(decoded)
                if measurement["clipped_samples"]==0 and measurement["sample_peak_dbfs"]<=-1:break
                correction=-3-measurement["sample_peak_dbfs"];gain+=correction
                samples=array.array("f",(x*10**(correction/20) for x in samples))
            else:raise ValueError("Vorbis decode peak safety failed")
            key="hunter.void.super."+action;resource="destiny:w34/hunter/void/super/"+action
            relative="src/main/resources/assets/destiny/sounds/w34/hunter/void/super/"+action+".ogg"
            records[key]={"event":key,"sound":resource,"asset_path":relative,"status":"video_mix_edit",
                "source_window_seconds":[start,end],"source_sha256":SOURCE_SHA,"limitations":note,
                "transforms":{"filter":FILTERS,"gain_db":round(gain,6),"fade_in_ms":2,"fade_out_ms":fadeout,
                    "resample_hz":RATE,"channels":1,"pitch_shift":False,"time_stretch":False},
                "output":dict(measurement,codec="vorbis",channels=1,sample_rate_hz=RATE,bytes=output.stat().st_size,sha256=sha(output.read_bytes()))}
            dest=ROOT/relative;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(output,dest)
            # Reviewer WAV is decoded from the exact production OGG, not a different pre-encode master.
            wav(review/(f"{i:02d}_"+action+".wav"),decoded)
            shutil.copy2(output,review/(f"{i:02d}_"+action+".ogg"))
            preview.extend(decoded);preview.extend(silence)
    manifest={"schema_version":1,"wave":"w34","overrides_wave":"w33",
        "source":{"url":SOURCE_URL,"video_id":"O0uvtZMID9E","title":"Destiny 2 All SUPER Sounds - MEGA SHOWCASE including NEW SUPERS + PRISMATIC",
            "uploader":"thatguyHoody","chapter":"Shadowshot - Deadfall","chapter_seconds":[1045,1064],
            "container":"m4a","codec":"aac","cache_name":expected.name,"bytes":expected.stat().st_size,"sha256":SOURCE_SHA},
        "authorization":"User requested processing this YouTube video's Shadowshot sound and receiving review files; no redistribution license inferred.",
        "verification_limits":"Chapter and actual frames reviewed; cuts selected from waveform/transients. No independent acoustic listening or isolated-stem verification. Conservative denoise does not guarantee removal of ambience/other effects.",
        "events":records,"summary":{"replaced_event_keys":5,"unique_ogg_files":5,"ogg_bytes":sum(r["output"]["bytes"] for r in records.values())}}
    dump(mf,manifest)
    definitions=json.loads((RES/"assets/destiny/sounds.json").read_text())
    for key,record in records.items():
        definitions[key]={"subtitle":"subtitles.destiny."+key,"sounds":[{"name":record["sound"],"stream":False,"attenuation_distance":32}]}
    from import_shadowshot_w36 import apply as apply_sequence
    apply_sequence(definitions)
    dump(RES/"assets/destiny/sounds.json",definitions)
    dump(QA/"manifest.json",manifest)
    wav(review/"00_all_processed_preview.wav",preview)
    # A short unprocessed comparison excerpt only, never the full 21-minute source.
    raw=subprocess.run([ff,"-hide_banner","-v","error","-ss","1047.10","-i",str(expected),"-t","2.65","-ac","1","-ar",str(RATE),"-f","f32le","-"],capture_output=True,check=True).stdout
    wav(review/"06_source_comparison_17m27.10-17m29.75.wav",array.array("f",raw))
    dump(review/"manifest.json",manifest)
    (review/"README.txt").write_text("Shadowshot Deadfall W34 review\n00: start / draw / fire / impact / end, with 0.5s gaps.\n01-05: individual clips. WAVs are decoded from the actual pack OGG.\n06: 2.65s original mixed-audio comparison.\nThe 'end' is an authored release-tail fade, not an identified original shutdown.\nImpact/action boundaries are provisional; ambience and overlapping game effects may remain.\nSource: "+SOURCE_URL+"\nNo independent acoustic listening was possible in this tool session.\nNo redistribution license inferred.\n")
    checksum="".join(sha(p.read_bytes())+"  "+p.name+"\n" for p in sorted(review.iterdir()) if p.is_file() and p.name!="SHA256SUMS")
    (review/"SHA256SUMS").write_text(checksum)
    zip_path=review.with_suffix(".zip")
    with zipfile.ZipFile(zip_path,"w",compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(review.iterdir()):
            if p.is_file():
                zi=zipfile.ZipInfo(p.name,date_time=(2026,10,23,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,p.read_bytes())
    check(manifest);print(json.dumps(dict(manifest["summary"],review_zip=str(zip_path)),indent=2))
if __name__=="__main__":main()
