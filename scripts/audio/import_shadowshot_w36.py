#!/usr/bin/env python3
"""One uninterrupted Deadfall source interval, played once at activation. No downloads."""
import argparse, array, json, math, shutil, subprocess, wave, zipfile
from pathlib import Path
from import_sounds_w33 import decode, stats, ffmpeg_path, dump, sha
from import_shadowshot_w34 import CACHE, SOURCE_SHA, SOURCE_URL, RATE, FILTERS, extract, wav
ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/"src/main/resources"
MF=RES/"destiny/sounds/w36.json"
REVIEW=ROOT/"run/deliverables/w36-shadowshot"
QA=ROOT/"docs/qa/2026-10-23/w36"
KEY="hunter.void.super.start"
# .35s from this contiguous interval's beginning to W34's reviewed release boundary.
# Trim the early .30s swell, NOT internal stages, to keep the existing seven-tick cast.
BEGIN, END = 1047.47, 1049.70

def apply(definitions):
    if not MF.exists(): return None
    m=json.loads(MF.read_text()); rec=m["events"][KEY]
    source=CACHE/m["source"]["cache_name"]
    if sha(source.read_bytes())!=SOURCE_SHA or sha((ROOT/rec["asset_path"]).read_bytes())!=rec["output"]["sha256"]:
        raise ValueError("Changed W36 source/output; refusing stale overlay")
    definitions[KEY]={"subtitle":"subtitles.destiny."+KEY,"sounds":[{"name":rec["sound"],"stream":False,"attenuation_distance":32}]}
    return {"manifest":"destiny/sounds/w36.json","replaced_keys":[KEY],"note":"One continuous original interval; only start is dispatched by Void. Legacy phase assets are historical/audition compatibility only."}

def verify():
    m=json.loads(MF.read_text());defs=json.loads((RES/"assets/destiny/sounds.json").read_text());copy=json.loads(json.dumps(defs))
    apply(copy)
    assert defs==copy,"W36 overlay inactive"
    ff=ffmpeg_path(None);rec=m["events"][KEY];path=ROOT/rec["asset_path"];samples=decode(ff,path);measure=stats(samples)
    for k in ["duration_seconds","sample_peak_dbfs","rms_dbfs","clipped_samples"]:
        assert abs(measure[k]-rec["output"][k])<.0001,(k,measure[k])
    with wave.open(str(REVIEW/"shadowshot_continuous.wav")) as w:
        assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,RATE)
        assert list(array.array("h",w.readframes(w.getnframes())))==[round(max(-1,min(1,v))*32767) for v in samples]
    assert (REVIEW/"shadowshot_continuous.ogg").read_bytes()==path.read_bytes()
    with zipfile.ZipFile(REVIEW.with_suffix(".zip")) as z:
        assert z.testzip() is None
        for f in REVIEW.iterdir():
            if f.is_file():assert z.read(f.name)==f.read_bytes()
    report=dict(measured=measure,output_sha256=sha(path.read_bytes()),zip_sha256=sha(REVIEW.with_suffix(".zip").read_bytes()),
                continuity="One source interval; no internal cuts, joins, padding or per-stage fades",review_wav="Exact int16 decode of production OGG",listening="User audition pending; not independently heard")
    dump(QA/"audio-verification.json",report);return report

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--check",action="store_true");args=ap.parse_args()
    if args.check:print(json.dumps(verify(),indent=2));return
    source=CACHE/"O0uvtZMID9E-source.m4a"
    if sha(source.read_bytes())!=SOURCE_SHA:raise ValueError("Pinned original AAC missing or changed")
    ff=ffmpeg_path(None);samples=extract(ff,source,BEGIN,END);before=stats(samples)
    gain=min(9.,-21-before["rms_dbfs"],-6-before["sample_peak_dbfs"])
    for i in range(len(samples)):
        samples[i]*=10**(gain/20)*min(1.,(i+1)/round(.002*RATE),(len(samples)-i)/round(.15*RATE))
    dest=RES/"assets/destiny/sounds/w36/hunter/void/super/cast.ogg";dest.parent.mkdir(parents=True,exist_ok=True)
    subprocess.run([ff,"-hide_banner","-v","error","-y","-f","f32le","-ar",str(RATE),"-ac","1","-i","pipe:0",
                    "-map_metadata","-1","-c:a","libvorbis","-q:a","4","-fflags","+bitexact","-flags:a","+bitexact",str(dest)],input=samples.tobytes(),capture_output=True,check=True)
    decoded=decode(ff,dest);measure=stats(decoded)
    assert measure["clipped_samples"]==0 and measure["sample_peak_dbfs"]<=-1
    rec=dict(event=KEY,sound="destiny:w36/hunter/void/super/cast",asset_path=str(dest.relative_to(ROOT)),
             status="continuous_video_mix_edit",source_window_seconds=[BEGIN,END],source_sha256=SOURCE_SHA,
             transforms=dict(filter=FILTERS,gain_db=round(gain,6),fade_in_ms=2,fade_out_ms=150,sample_rate_hz=RATE,channels=1,
                             internal_cuts=0,concatenation=False,inserted_silence=False,time_stretch=False,pitch_shift=False),
             output=dict(measure,codec="vorbis",channels=1,sample_rate_hz=RATE,bytes=dest.stat().st_size,sha256=sha(dest.read_bytes())))
    m=dict(schema_version=1,wave="w36",overrides_wave="w34",source=dict(url=SOURCE_URL,video_id="O0uvtZMID9E",chapter="Shadowshot - Deadfall",cache_name=source.name,sha256=SOURCE_SHA),
           events={KEY:rec},playback=dict(trigger="successful activation only",suppressed_phase_actions=["draw","fire","impact","end"],release_reference_seconds=.35,
                                         note="Mixed impact/tail stays on recorded timeline, not spatially rescheduled to actual projectile collision. Gameplay impact remains collision-driven."),
           verification_limits="One contiguous original AAC interval; trimmed leading .30s swell to align reference release with seven ticks. No independent acoustic listening or isolated-stem verification; ambience/overlapping source effects may remain.")
    dump(MF,m);defs=json.loads((RES/"assets/destiny/sounds.json").read_text());apply(defs);dump(RES/"assets/destiny/sounds.json",defs)
    legacy=RES/"destiny/sounds/w33.json";d=json.loads(legacy.read_text());d["active_sequence_overlay"]=apply(defs);dump(legacy,d)
    REVIEW.mkdir(parents=True,exist_ok=True);wav(REVIEW/"shadowshot_continuous.wav",decoded);shutil.copy2(dest,REVIEW/"shadowshot_continuous.ogg");dump(REVIEW/"manifest.json",m)
    (REVIEW/"README.txt").write_text("Shadowshot W36: ONE continuous source interval, 17:27.47-17:29.70.\nNo internal edits, stage gaps or concatenation. Whole clip plays ONCE at activation.\nWAV is int16 decode of production OGG. Recorded impact/tail is not rescheduled to projectile collision.\nNo independent listening claim; source mix can include ambience.\nSource: "+SOURCE_URL+"\nNo redistribution license inferred.\n")
    (REVIEW/"SHA256SUMS").write_text("".join(sha(f.read_bytes())+"  "+f.name+"\n" for f in sorted(REVIEW.iterdir()) if f.is_file() and f.name!="SHA256SUMS"))
    with zipfile.ZipFile(REVIEW.with_suffix(".zip"),"w",compression=zipfile.ZIP_DEFLATED) as z:
        for f in sorted(REVIEW.iterdir()):
            if f.is_file():
                zi=zipfile.ZipInfo(f.name,date_time=(2026,10,23,0,0,0));zi.compress_type=zipfile.ZIP_DEFLATED;z.writestr(zi,f.read_bytes())
    dump(QA/"manifest.json",m);print(json.dumps(verify(),indent=2))
if __name__=="__main__":main()
