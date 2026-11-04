#!/usr/bin/env python3
"""Import the four supplied completion sounds without trimming or pitch changes."""
import argparse, hashlib, json, subprocess
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(); parser.add_argument('source',type=Path); args=parser.parse_args()
    ff=ROOT/'run/private-sources/w33/tools/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1'
    base=ROOT/'src/main/resources/assets/destiny_fireteam'; manifest=[]
    sounds=json.loads((base/'sounds.json').read_text())
    for i in range(1,5):
        source=args.source/('Transmat_Basic'+('' if i==1 else '_'+str(i))+'.mp3')
        before=sha(source); target=base/f'sounds/sfx/respawn_complete_{i}.ogg'
        subprocess.run([str(ff),'-v','error','-y','-i',str(source),'-map_metadata','-1','-ac','1','-c:a','libvorbis','-q:a','5',str(target)],check=True)
        assert sha(source)==before
        sounds[f'respawn_complete_{i}']={'sounds':[f'destiny_fireteam:sfx/respawn_complete_{i}']}
        def seconds(path):
            raw=subprocess.check_output([str(ff),'-v','error','-i',str(path),'-f','f32le','-ar','48000','-ac','1','-'])
            return len(raw)/4/48000
        source_seconds, output_seconds = seconds(source), seconds(target)
        assert abs(source_seconds-output_seconds)<.03
        manifest.append({'source':str(source),'sourceSha256':before,'output':str(target.relative_to(ROOT)),'outputSha256':sha(target),'sourceSeconds':source_seconds,'outputSeconds':output_seconds})
    (base/'sounds.json').write_text(json.dumps(sounds,indent=2)+'\n')
    (ROOT/'src/main/resources/destiny/down/respawn-audio-provenance.json').write_text(json.dumps({'files':manifest,'conversion':'Full-length mono Vorbis quality 5, no trim/normalization/pitch change','selection':'Server uniform nextInt(4), same variant for owner and eligible team','ffmpegSha256':sha(ff)},indent=2)+'\n')
if __name__=='__main__': main()
