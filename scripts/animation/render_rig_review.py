"""Render sampled, unretargeted bone motion for review. Requires Pillow, not Blender.

These orthographic projections are source-rig evidence, not Minecraft screenshots,
mesh contact validation, or a reconstructed Destiny camera. Frame durations retain
the sampled fps; source endpoints and rotation-only weapon motion remain visible.
"""
import argparse
import json
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

BG = '#101922'
FG = '#d9e6f1'
BLUE = '#66d5ec'
ORANGE = '#ffba62'


def font(size):
    try:
        return ImageFont.truetype('/System/Library/Fonts/Menlo.ttc', size)
    except OSError:
        return ImageFont.load_default(size=size)


def render(data, clip, output):
    bones = data['bones']
    indices = {b['name']: i for i,b in enumerate(bones)}
    parents = [indices.get(b['parent'], -1) for b in bones]
    # Include the pose head and weapon-local axes in the fixed per-clip framing.
    spans = []
    for horizontal in (0,1):
        points = [p for f in clip['frames'] for p in f['heads']]
        lo = [min(p[horizontal] for p in points), min(p[2] for p in points)]
        hi = [max(p[horizontal] for p in points), max(p[2] for p in points)]
        center = [(a+b)/2 for a,b in zip(lo,hi)]
        scale = 350 / max(hi[0]-lo[0], hi[1]-lo[1], .01)
        spans.append((center,scale))

    def draw(frame):
        canvas = Image.new('RGB', (960,560), BG)
        pen = ImageDraw.Draw(canvas)
        pen.text((25,15), data['group'] + '  /  ' + clip['tag'], fill=FG, font=font(18))
        pen.text((25,43), f"{frame['seconds']:.3f} / {clip['durationSeconds']:.3f} s   {data['fps']:g} fps",fill=BLUE,font=font(16))
        for view, horizontal in enumerate((0,1)):
            center,scale = spans[view]
            def xy(p):
                return (view*480+240+(p[horizontal]-center[0])*scale, 290-(p[2]-center[1])*scale)
            pen.text((view*480+25,80), ('X/Z' if horizontal==0 else 'Y/Z')+' armature space',fill='#9bb5c8',font=font(15))
            for i,parent in enumerate(parents):
                if parent < 0:
                    continue
                p,q = frame['heads'][i],frame['heads'][parent]
                color = ORANGE if bones[i].get('weaponBone') else BLUE
                pen.line([xy(p),xy(q)],fill=color,width=2)
            for i,bone in enumerate(bones):
                if bone.get('weaponBone') or bone['semanticName']=='b_r_hand':
                    m = frame['matrices'][i]
                    origin = frame['heads'][i]
                    for axis,color in enumerate(('#ec7376','#8cde8c','#7da3ff')):
                        endpoint = [origin[k]+m[k][axis]*.075 for k in range(3)]
                        pen.line([xy(origin),xy(endpoint)],fill=color,width=2)
        pen.text((25,507), 'SOURCE BONES ONLY | no mesh / no Minecraft / no contact validation',fill='#9bb5c8',font=font(14))
        pen.text((25,531), 'Orange: weapon bones. RGB: weapon/hand axes. Forward sign unverified.',fill='#9bb5c8',font=font(13))
        return canvas

    frames = [draw(f) for f in clip['frames']]
    # GIF time is in 10ms units. Cumulative rounding avoids 30fps becoming 33.3fps.
    timestamps = [round(i*100/data['fps'])*10 for i in range(len(frames)+1)]
    durations = [timestamps[i+1]-timestamps[i] for i in range(len(frames))]
    output.mkdir(parents=True,exist_ok=True)
    frames[0].save(output/(clip['tag']+'.gif'),save_all=True,append_images=frames[1:],
                   duration=durations,loop=0,disposal=2)
    sheet = Image.new('RGB',(1440,560),BG)
    for j in range(6):
        index = round(j*(len(frames)-1)/5)
        thumb = frames[index].resize((480,280))
        sheet.paste(thumb,((j%3)*480,(j//3)*280))
    sheet.save(output/(clip['tag']+'-contact-sheet.png'))
    return dict(tag=clip['tag'],frames=len(frames),fps=data['fps'],
                originalDurationSeconds=clip['durationSeconds'],
                gifCycleSeconds=sum(durations)/1000,
                gifIncludesLastEndpointHold=True,
                space='armature object',gameplayOrContactVerified=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('samples',type=Path,nargs='+')
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--tags',nargs='+',required=True)
    args=parser.parse_args()
    outputs=[]
    for path in args.samples:
        data=json.loads(path.read_text())
        for clip in data['clips']:
            if clip['tag'] in args.tags:
                outputs.append(render(data,clip,args.output))
    if set(args.tags)!={x['tag'] for x in outputs}:
        raise ValueError('Requested review clips missing from evaluated samples')
    (args.output/'review-index.json').write_text(json.dumps(outputs,indent=2)+'\n')
    print(json.dumps(outputs))


if __name__=='__main__':
    main()
