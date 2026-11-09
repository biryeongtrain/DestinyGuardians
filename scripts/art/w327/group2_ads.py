"""Deliverance/Forbearance-only ADS vertical alignment after master native review.
Preserve original crown/mast geometry; aim just above the authored highest sight.
Only first-person display translation Y changes, blended over the donor 21 frames.
HIP frame 00, rotation, scale, depth, non-first-person contexts and reload stay intact.
"""
import argparse,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
# Native capture center (854,480); authored geometry extrema, not guessed screen offsets.
SPECS={
    'deliverance':dict(donor='hollow_words',folder='weapon_sight_w153',donor_sight_y=14.48,top_y=15.105,target_y=15.22),
    'forbearance':dict(donor='deafening_whisper',folder='weapon_sight_w149',donor_sight_y=15.86,top_y=16.654361361384616,target_y=16.77),
}
SCALE=.9

def build(source_root=ROOT):
    outputs=[]
    for wid,spec in SPECS.items():
        folder=Path('src/main/resources/assets/destiny/models')/spec['folder']
        output=ROOT/folder;output.mkdir(parents=True,exist_ok=True)
        dy=-SCALE*(spec['target_y']-spec['donor_sight_y'])
        for frame in range(21):
            for style in ['native','twohand']:
                source=source_root/folder/f"{spec['donor']}_{frame:02}_{style}.json"
                doc=json.loads(source.read_text().replace(spec['donor'],wid))
                for context in ['firstperson_righthand','firstperson_lefthand']:
                    t=doc['display'][context]['translation'];t[1]=round(t[1]+dy*frame/20,6)
                path=output/f'{wid}_{frame:02}_{style}.json'
                path.write_text(json.dumps(doc,indent=2)+'\n');outputs.append(path)
    return outputs

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source-root',type=Path,default=ROOT);args=parser.parse_args()
    print('Wrote',len(build(args.source_root)),'weapon-specific ADS leaves')
