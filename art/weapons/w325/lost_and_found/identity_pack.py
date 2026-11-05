"""Lossless identical-island reuse and MaxRects packing after kit.py build.
Run with /opt/anaconda3/bin/python3 art/weapons/w325/lost_and_found/identity_pack.py <weapon-id>.
Source build uses a 1024-wide scratch atlas; published atlas uses the smallest supported lossless layout (512 square or 1024x512). No texels are resampled.
"""
import hashlib, json, sys
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[4]
IDS = ('lost_and_found','nanty_narker','psi_cirrus_ii','agrona_pr2','psi_ferox_ii','bayesian_msu','encore_25')

def pack(rects, size, mode):
    width,height=(size,size) if isinstance(size,int) else size
    free=[(0,0,width,height)]; placed={}
    ordered=sorted(rects, key=lambda r: (-([r[1]*r[2],max(r[1:]),r[2]][mode]),-r[2],-r[1]))
    for key,w,h in ordered:
        choices=[(min(fw-w,fh-h), max(fw-w,fh-h), y,x) for x,y,fw,fh in free if w<=fw and h<=fh]
        if not choices: return None
        _,_,y,x=min(choices); placed[key]=(x,y); new=[]
        for fx,fy,fw,fh in free:
            if x>=fx+fw or x+w<=fx or y>=fy+fh or y+h<=fy: new.append((fx,fy,fw,fh)); continue
            if x>fx: new.append((fx,fy,x-fx,fh))
            if x+w<fx+fw: new.append((x+w,fy,fx+fw-x-w,fh))
            if y>fy: new.append((fx,fy,fw,y-fy))
            if y+h<fy+fh: new.append((fx,y+h,fw,fy+fh-y-h))
        new=list(dict.fromkeys(new))
        free=[r for i,r in enumerate(new) if not any(i!=j and r[0]>=q[0] and r[1]>=q[1] and r[0]+r[2]<=q[0]+q[2] and r[1]+r[3]<=q[1]+q[3] for j,q in enumerate(new))]
    return placed

def run(wid):
    assert wid in IDS
    skin=ROOT/'src/main/resources/destiny/weapon_skins'/f'{wid}.json'
    tex=ROOT/'src/main/resources/assets/destiny/textures/item/weapon/w325'/f'{wid}.png'
    man=ROOT/'art/weapons/w325'/wid/'manifest.json'
    doc=json.loads(skin.read_text()); im=Image.open(tex).convert('RGBA'); imgs={}; refs=[]
    for es in doc['parts'].values():
        for e in es:
            for face in e['faces'].values():
                uv=face['uv']; rect=tuple(round(uv[i]*im.size[i%2]/16) for i in range(4)); patch=im.crop(rect)
                key=(patch.size,hashlib.sha256(patch.tobytes()).hexdigest()); imgs[key]=patch; refs.append((face,key))
    rectangles=[(k,v.width+2,v.height+2) for k,v in imgs.items()]
    sys.path.insert(0,str(ROOT/'scripts/art/w325'))
    import kit
    requested=getattr(kit.load_design(wid),'FINAL_ATLAS',None)
    atlas=tuple(requested) if requested else (512,512)
    placements=next((p for mode in range(3) if (p:=pack(rectangles,atlas,mode)) is not None),None)
    if placements is None and not requested:
        atlas=(1024,512)
        placements=next((p for mode in range(3) if (p:=pack(rectangles,atlas,mode)) is not None),None)
    if placements is None: raise RuntimeError(f'{wid}: cannot fit losslessly into 1024x512')
    out=Image.new('RGBA',atlas)
    for key,patch in imgs.items():
        x,y=placements[key]; w,h=patch.size
        # Clamp border texels in a one-pixel gutter, not a resized approximation.
        out.paste(patch,(x+1,y+1)); out.paste(patch.crop((0,0,w,1)),(x+1,y))
        out.paste(patch.crop((0,h-1,w,h)),(x+1,y+h+1)); out.paste(patch.crop((0,0,1,h)),(x,y+1))
        out.paste(patch.crop((w-1,0,w,h)),(x+w+1,y+1))
        for dx,dy,px,py in [(0,0,0,0),(w+1,0,w-1,0),(0,h+1,0,h-1),(w+1,h+1,w-1,h-1)]: out.putpixel((x+dx,y+dy),patch.getpixel((px,py)))
    for face,key in refs:
        x,y=placements[key]; w,h=imgs[key].size
        face['uv']=[(x+1)*16/atlas[0],(y+1)*16/atlas[1],(x+w+1)*16/atlas[0],(y+h+1)*16/atlas[1]]
        # Verifies exact retained RGBA face contents before writing.
        assert out.crop((x+1,y+1,x+w+1,y+h+1)).tobytes()==imgs[key].tobytes()
    doc['texture_size']=list(atlas); out.save(tex,optimize=True); skin.write_text(json.dumps(doc,separators=(',',':')))
    m=json.loads(man.read_text()); m['atlas']=list(atlas); m['atlas_repack']='identity_pack.py: lossless duplicate-island reuse + MaxRects; no resampling'
    m['surface_style']='material; explicit per-part materials with source luminance relief; sparse decals only'
    m.pop('painted_faces',None)
    for rel in m['outputs_sha256']: m['outputs_sha256'][rel]=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
    man.write_text(json.dumps(m,indent=1,sort_keys=True)+'\n')
    print(f'{wid}: {len(imgs)} unique islands -> {atlas[0]}x{atlas[1]}; exact RGBA verified for {len(refs)} faces')

if __name__=='__main__':
    for wid in sys.argv[1:] or IDS: run(wid)
