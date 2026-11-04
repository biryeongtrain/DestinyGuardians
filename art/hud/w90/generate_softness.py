#!/usr/bin/env python3
"""W90 OFFLINE candidate only. Reads W89; writes below this file's directory only.

Run: rtk proxy /tmp/destiny-hud-venv/bin/python art/hud/w90/generate_softness.py
Repeat with --verify for byte-exact reconstruction without writes. Pillow 13.0.0.
No imports/execution of W89 generator, no production writes, no client contact.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import PIL
from PIL import Image, ImageChops, ImageDraw, ImageStat

ART = Path(__file__).resolve().parent
ROOT = ART.parents[2]
TEX = ROOT / 'src/main/resources/assets/destiny/textures/item/hud'
PREFIX = 'incoming_w89_critical_'
CUTOFF = 26
LIVE = 32
BAYER = ((0,8,2,10),(12,4,14,6),(3,11,1,9),(15,7,13,5))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(obj):
    return (json.dumps(obj, indent=2, sort_keys=True) + '\n').encode()


def png(im):
    buf = io.BytesIO()
    im.save(buf, format='PNG', compress_level=9)
    return buf.getvalue()


def cutoff(a):
    return a.point(lambda v: v if v >= CUTOFF else 0)


def scramble(x, y):
    h = ((x * 0x1f123bb5) ^ (y * 0x5f356495) ^ 0x90c0ffee) & 0xffffffff
    h ^= h >> 16
    h = (h * 0x7feb352d) & 0xffffffff
    return h ^ (h >> 15)


def thresholds(scale):
    """Per-W89-cell rotated/reflected Bayer ranks; fixed across all pulse frames.

    2x uses the first-level Bayer ranks; 4x uses all 16. These are locally
    stratified ordered samples, NOT a claim of blue noise. Spatial decorrelation
    avoids a single global checker grid but does not guarantee no moire.
    """
    w, h = 512*scale, 288*scale
    data = bytearray(w*h)
    n = scale*scale
    for y in range(288):
        for x in range(512):
            seed = scramble(x,y)
            for sy in range(scale):
                for sx in range(scale):
                    u,v = sx,sy
                    if seed & 1: u = scale-1-u
                    if seed & 2: v = scale-1-v
                    if seed & 4: u,v = v,u
                    rank = BAYER[v][u] if scale == 4 else ((0,2),(3,1))[v][u]
                    # ceil((rank+.5)*26/n) encoded as ceil()-1 for subtract>0.
                    t = math.ceil((rank+.5)*CUTOFF/n)-1
                    data[(y*scale+sy)*w+x*scale+sx] = t
    return Image.frombytes('L',(w,h),bytes(data))


def candidate(a, scale, threshold):
    up = a.resize((512*scale,288*scale),Image.Resampling.NEAREST)
    dots = ImageChops.subtract(up,threshold).point(lambda v: LIVE if v else 0)
    # All old survivors remain full coverage, never lower in opacity. Promote
    # only the narrow 26..31 shoulder to 32 to join the dither ramp monotonically.
    core = up.point(lambda v: max(v,LIVE) if v >= CUTOFF else 0)
    # Retain original subcutoff alpha inside every dot hole. Those samples are
    # still discarded at base LOD, but nonnegative texture filtering then has
    # a>=W89 everywhere and cannot dim/reject an old surviving sample.
    return ImageChops.lighter(up,ImageChops.lighter(dots,core)), up


def coverage(a):
    h = a.histogram()
    count = a.width*a.height
    return dict(alphaMax=a.getextrema()[1], alphaMean=ImageStat.Stat(a).mean[0],
                coverage=sum(h[CUTOFF:])/count, zeroFraction=h[0]/count,
                subcutoffFraction=sum(h[1:CUTOFF])/count)


def profile(a):
    """Vertical normalized-radius band; ±12 source px around screen centre.

    Average the band first (perceptual low-pass); maximum adjacent row step is
    explicitly NOT a maximum fragment jump. Raw dither fragment jump remains32.
    """
    small=a.resize((512,288),Image.Resampling.BOX)
    p=[]
    for y in range(10,80):
        p.append(ImageStat.Stat(small.crop((244,y,268,y+1))).mean[0])
    return dict(topBandRows=list(range(10,80)), alpha=p,
                maxAdjacentBandStep=max(abs(b-a) for a,b in zip(p,p[1:])))


def image_rgba(a):
    im = Image.new('RGBA',a.size,(255,255,255,0))
    im.putalpha(a)
    return im


def scene(size, color):
    im=Image.new('RGBA',size,color)
    d=ImageDraw.Draw(im)
    w,h=size
    d.polygon([(0,h),(w*.42,h*.50),(w*.58,h*.50),(w,h)],fill='#474c50')
    d.rectangle((w*.47,h*.37,w*.53,h*.62),fill='#b3b8b3')
    d.line((w*.5-5,h*.5,w*.5+5,h*.5),fill='white')
    d.line((w*.5,h*.5-5,w*.5,h*.5+5),fill='white')
    return im


def composite(bg,a):
    tint=Image.new('RGBA',a.size,(225,32,43,0))
    tint.putalpha(a)
    out=bg.copy()
    out.alpha_composite(tint)
    return out.convert('RGB')


def overview(bases, candidates):
    sheet=Image.new('RGB',(1536,1100),'#15212c')
    d=ImageDraw.Draw(sheet)
    d.text((16,12),'W90 OFFLINE SYNTHETIC / NOT NATIVE PROOF / cutoff 0.1 model',fill='white')
    d.text((16,32),'Cutoff evaluated BEFORE display downsampling. No compositing onto the already-washed native frame.',fill='#cbd6df')
    for row,(idx,color) in enumerate(((0,'#a9c9ec'),(7,'#a9c9ec'),(7,'#20262c'))):
        arrays=(cutoff(bases[idx]).resize((1024,576),Image.Resampling.NEAREST),
                candidates[2][idx],candidates[4][idx])
        titles=('W89 512x288 cutoff baseline','W90 local dither 1024x576','W90 local dither 2048x1152')
        for col,(a,title) in enumerate(zip(arrays,titles)):
            bg=scene(a.size,color)
            tile=composite(bg,cutoff(a)).resize((512,288),Image.Resampling.BOX)
            x,y=col*512,70+row*338
            sheet.paste(tile,(x,y))
            d.text((x+10,y+294),f'FRAME {idx} / {title}',fill='white')
            d.text((x+10,y+311),'OFFLINE resolved alpha samples; not GPU texture filtering',fill='#bdcbd7')
    return sheet


def stress_sheet(base, fine):
    sheet=Image.new('RGB',(1536,860),'#15212c')
    d=ImageDraw.Draw(sheet)
    d.text((16,12),'W90 OFFLINE FILTER ORDER STRESS / NOT NATIVE PROOF / frame7',fill='white')
    d.text((16,32),'Left: current cutoff; middle: 4x dots resolved after cutoff; right: mean mip2 BEFORE cutoff.',fill='#cbd6df')
    mip=fine.resize((512,288),Image.Resampling.BOX)
    arrays=(cutoff(base),fine,cutoff(mip))
    for i,a in enumerate(arrays):
        im=composite(scene(a.size,'#a9c9ec'),cutoff(a)).resize((512,288),Image.Resampling.BOX)
        sheet.paste(im,(i*512,64))
        crop=composite(scene(a.size,'#a9c9ec'),cutoff(a))
        w,h=a.size
        crop=crop.crop((int(w*.38),int(h*.12),int(w*.62),int(h*.32)))
        crop=crop.resize((480,400),Image.Resampling.NEAREST)
        sheet.paste(crop,(i*512+16,396))
    d.text((16,363),'Cutoff W89',fill='white')
    d.text((528,363),'Dither: optimistic resolved coverage',fill='white')
    d.text((1040,363),'Dither: averaged tail clipped again',fill='white')
    d.text((16,818),'Magnified top-inner edge: dither has real 0<->32 fragment jumps; a smooth macro profile is not smooth per fragment.',fill='white')
    return sheet


def sampling_sheet(base,banks):
    sheet=Image.new('RGB',(1536,740),'#15212c')
    d=ImageDraw.Draw(sheet)
    d.text((16,12),'W90 OFFLINE 1708x960 SAMPLING BOUNDS / NOT NATIVE PROOF / frame0',fill='white')
    d.text((16,32),'Sample/resize raw alpha FIRST; discard at26 SECOND; composite THIRD; shrink labelled panel LAST. No mip/atlas/GPU proof.',fill='#cbd6df')
    for row,(kind,filt) in enumerate((('NEAREST',Image.Resampling.NEAREST),('BILINEAR',Image.Resampling.BILINEAR))):
        for col,(title,a) in enumerate((('W89 original512',base),('W90 local2x',banks[2][0]),('W90 local4x',banks[4][0]))):
            sampled=cutoff(a.resize((1708,960),filt))
            im=composite(scene(sampled.size,'#a9c9ec'),sampled)
            x,y=col*512,68+row*330
            sheet.paste(im.resize((512,288),Image.Resampling.BOX),(x,y))
            d.text((x+10,y+294),f'{title} / {kind} before discard / OFFLINE',fill='white')
    return sheet


def profile_chart(stats):
    sheet=Image.new('RGB',(1200,680),'#15212c')
    d=ImageDraw.Draw(sheet)
    d.text((16,12),'W90 OFFLINE ALPHA BAND PROFILES / NOT NATIVE PROOF',fill='white')
    d.text((16,32),'24-source-pixel-wide vertical band at top centre; resolve to512x288 before band mean. Fragment jumps are not resolved means.',fill='#cbd6df')
    colors=('#e3a28c','#83c9d7','#bba1ec','#f3d679')
    for col,idx in enumerate((0,7)):
        entries={s:next(e for e in stats if e['scale']==s and e['frame']==idx) for s in (2,4)}
        curves=[('W89 cutoff',entries[2]['w89Profile']),
                ('2x cutoff resolved',entries[2]['candidateProfile']),
                ('4x cutoff resolved',entries[4]['candidateProfile']),
                ('4x mean mip2 then cutoff',entries[4]['filterStress'][2]['profile'])]
        x0,y0,w,h=50+col*590,100,500,420
        ymax=80 if idx==0 else 160
        for val in range(0,ymax+1,ymax//8):
            yy=y0+h-val/ymax*h
            d.line((x0,yy,x0+w,yy),fill='#334654')
            d.text((x0-26,yy-5),str(val),fill='#b6c9d5')
        for k,((label,p),color) in enumerate(zip(curves,colors)):
            pts=[(x0+j/69*w,y0+h-v/ymax*h) for j,v in enumerate(p['alpha'])]
            d.line(pts,fill=color,width=2)
            d.text((x0,y0+h+24+k*22),label+f" / max row step {p['maxAdjacentBandStep']:.2f}",fill=color)
        d.text((x0,y0-30),f'FRAME {idx} / alpha byte units',fill='white')
        d.text((x0+w-200,y0+h+5),'source row10 ----------------79',fill='#b6c9d5')
    return sheet


def generate():
    sourcepaths=[TEX/(PREFIX+str(i)+'.png') for i in range(8)]
    sourcepaths += [ROOT/'scripts/generate_critical_hud_w89.py',
                   ROOT/'docs/qa/2026-10-25/w89/native/frames/hp-1-0.png']
    inputs={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sourcepaths}
    bases=[Image.open(p).convert('RGBA').getchannel('A') for p in sourcepaths[:8]]
    assert all(a.size==(512,288) for a in bases)
    # Test every source cell which overlaps the protected high-resolution
    # radius0.60 ellipse, rather than checking only the old pixel centres.
    for base in bases:
        values=base.tobytes()
        for y in range(288):
            dy=max(0,abs(y+.5-144)-.5)/144
            for x in range(512):
                dx=max(0,abs(x+.5-256)-.5)/256
                if math.hypot(dx,dy)<=.60:
                    assert values[y*512+x]==0,'Protected centre overlaps nonzero texel'
    out={}
    stats=[]
    banks={}
    for scale in (2,4):
        ts=thresholds(scale)
        bank=[]
        previous=None
        for i,base in enumerate(bases):
            a,up=candidate(base,scale,ts)
            old=cutoff(up)
            assert ImageChops.subtract(old,a).getbbox() is None,'Lost old visible alpha'
            assert a.getextrema()[1]==base.getextrema()[1],'Peak alpha changed'
            assert ImageChops.subtract(up,a).getbbox() is None,'Raw alpha lower than W89'
            # Any texel wholly outside W89 nonzero support remains clear.
            assert ImageChops.multiply(a,up.point(lambda v: 255 if v==0 else 0)).getbbox() is None
            if previous is not None:
                assert ImageChops.subtract(previous,a).getbbox() is None,'Pulse nonmonotone'
            previous=a
            bank.append(a)
            name=f'incoming_w90_local{scale}_{i}'
            root=ART/f'prototypes/local{scale}x/assets/destiny'
            texture=f'destiny:item/hud/{name}'
            out[root/f'textures/item/hud/{name}.png']=png(image_rgba(a))
            out[root/f'textures/item/hud/{name}.png.mcmeta']=encode({'texture':{'mipmap_strategy':'mean'}})
            out[root/f'models/gui/hud/{name}.json']=encode({
                'gui_light':'front','ambientocclusion':False,
                'textures':{'layer0':texture,'particle':texture},
                'elements':[{'from':[0,0,8],'to':[16,16,8],'shade':False,
                    'faces':{f:{'texture':'#layer0','uv':[0,0,16,16],'tintindex':0}
                             for f in ('north','south')}}]})
            out[root/f'items/gui/hud/{name}.json']=encode({'model':{
                'type':'minecraft:model','model':f'destiny:gui/hud/{name}',
                'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}})
            entry=dict(frame=i,scale=scale,w89Raw=coverage(base),w89Cutoff=coverage(cutoff(base)),
                highResOnlyCutoff=coverage(old),candidateRaw=coverage(a),candidate=coverage(cutoff(a)),
                w89Profile=profile(cutoff(base)),candidateProfile=profile(cutoff(a)),
                maxRawFragmentJumpAtDitherBoundary=LIVE,
                oldVisibleTexelsLost=0,peakUnchanged=True,clearSupportPreserved=True,
                meanAlphaAddedVsW89Cutoff=ImageStat.Stat(cutoff(a)).mean[0]-ImageStat.Stat(old).mean[0],
                filterStress=[])
            # Model order matters: GPU filters/mips the texture BEFORE discard.
            # Nearest and bilinear are screen-resampling bounds, not GPU proof.
            for factor in (1,2,4):
                size=(a.width//factor,a.height//factor)
                sampled=a if factor==1 else a.resize(size,Image.Resampling.BOX)
                ref=up if factor==1 else up.resize(size,Image.Resampling.BOX)
                c=cutoff(sampled)
                r=cutoff(ref)
                assert ImageChops.subtract(r,c).getbbox() is None,'Mean mip lost old visibility'
                entry['filterStress'].append(dict(meanMipLevel=int(math.log2(factor)),size=size,
                    candidate=coverage(c),w89AtSameGrid=coverage(r),
                    lostOldVisibleSamples=sum(v>0 for v in ImageChops.subtract(r,c).tobytes()),
                    profile=profile(c)))
            for width,height in ((1708,960),(1366,768),(854,480)):
                for kind,filt in (('nearest',Image.Resampling.NEAREST),('bilinear',Image.Resampling.BILINEAR)):
                    c=cutoff(a.resize((width,height),filt))
                    r=cutoff(up.resize((width,height),filt))
                    assert ImageChops.subtract(r,c).getbbox() is None,'Screen sampling lost old visibility'
                    entry['filterStress'].append(dict(screen=[width,height],sample=kind,
                        candidate=coverage(c),w89AtSameGrid=coverage(r),
                        lostOldVisibleSamples=sum(v>0 for v in ImageChops.subtract(r,c).tobytes()),
                        profile=profile(c)))
            stats.append(entry)
        banks[scale]=bank
    out[ART/'offline/overview.png']=png(overview(bases,banks))
    out[ART/'offline/filter-stress.png']=png(stress_sheet(bases[7],banks[4][7]))
    out[ART/'offline/sampling-1708.png']=png(sampling_sheet(bases[0],banks))
    out[ART/'offline/alpha-profiles.png']=png(profile_chart(stats))
    out[ART/'offline/metrics.json']=encode(dict(nativeProof=False,cutoff=0.1,
        method='fixed cell-scrambled ordered coverage; live alpha32; shoulder26..31 promoted32; holes retain original subcutoff alpha',
        profileDefinition='Top 24-source-pixel-wide band; row10..79; BOX resolve to512x288 then mean. Macro discontinuity only.',
        samplingLimits='Pillow byte-alpha arithmetic. No GPU/OIT/atlas/gamma/UV derivative emulation. Mip and sampling approximations only.',
        frames=stats))
    manifest=dict(stage='W90 candidate',nativeVerified=False,pillowVersion=PIL.__version__,
        generatorSha256=sha(Path(__file__).read_bytes()),inputSha256=inputs,
        formula='a<26: alpha32 if rank+.5 < a*N/26 else a; a>=26: max(a,32); white RGB',
        invariants=['Raw alpha pointwise >= nearest-upscaled W89, including subcutoff holes','All W89 cutoff-surviving texels retained or raised','Peaks unchanged77..160',
                    'W89 zero-alpha support remains zero','All frames monotone per texel'],
        drawbacks=['0-to32 raw fragment discontinuity','Shoulder and formerly clipped tail brighter',
                   'Fixed grain/moire/phase crawl possible','Mean minification can reclip tail',
                   '2x/4x texture memory is4x/16x W89; atlas cost unmeasured'],
        outputSha256={str(p.relative_to(ART)):sha(v) for p,v in out.items()})
    out[ART/'manifest.json']=encode(manifest)
    assert inputs=={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sourcepaths},'Inputs changed during generation'
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    outputs=generate()
    for p,raw in outputs.items():
        assert p.is_relative_to(ART)
        if args.verify:
            assert p.read_bytes()==raw,f'Output drift: {p}'
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(raw)
    print(json.dumps(dict(files=len(outputs),verified=args.verify,nativeVerified=False,
                         productionWrites=0,scales=[2,4])))


if __name__=='__main__':
    main()
