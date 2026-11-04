#!/usr/bin/env python3
"""Decode production audio and verify that review WAVs are the actual pack clips."""
import array, importlib.util, json, math, sys, wave, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/audio"))
import import_shadowshot_w34 as importer

def main():
    manifest=json.loads((ROOT/"src/main/resources/destiny/sounds/w34.json").read_text())
    importer.check(manifest);ff=importer.ffmpeg_path(None)
    review=ROOT/"run/deliverables/w34-shadowshot";rows=[]
    for i,(key,record) in enumerate(manifest["events"].items(),1):
        path=ROOT/record["asset_path"];decoded=importer.decode(ff,path);measured=importer.stats(decoded)
        for field in ["duration_seconds","sample_peak_dbfs","rms_dbfs","clipped_samples"]:
            assert abs(measured[field]-record["output"][field])<.0001,(key,field)
        action=key.rsplit(".",1)[1]
        with wave.open(str(review/(f"{i:02d}_"+action+".wav"))) as w:
            assert (w.getnchannels(),w.getsampwidth(),w.getframerate())==(1,2,32000)
            pcm=array.array("h",w.readframes(w.getnframes()))
        expected=[round(max(-1,min(1,v))*32767) for v in decoded]
        assert list(pcm)==expected,key
        assert (review/(f"{i:02d}_"+action+".ogg")).read_bytes()==path.read_bytes()
        rows.append(dict(event=key,**measured))
    zpath=review.with_suffix(".zip")
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        for f in review.iterdir():
            if f.is_file():assert z.read(f.name)==f.read_bytes(),f
    report=dict(events=rows,review_zip_sha256=importer.sha(zpath.read_bytes()),
        review_wavs="Exact 16-bit PCM decode of production OGG",listening="User review pending; this is not an acoustic listening assertion")
    importer.dump(ROOT/"docs/qa/2026-10-23/w34/audio-verification.json",report)
    print(json.dumps(report,indent=2))
if __name__=="__main__":main()
