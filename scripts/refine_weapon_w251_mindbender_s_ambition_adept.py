#!/usr/bin/env python3
"""W251: carved bone shoulders, hooked grip and lit continuous metal planes.

Regenerates from the original authored design and inert source material maps.
No incremental filtering, animation changes, raw-source writes or PBR claim.
"""
import argparse, base64, collections, copy, hashlib, importlib.util, io, json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
KEY = 'mindbender_s_ambition_adept'
ART = f'art/weapons/w251/{KEY}/'
ASSET = 'src/main/resources/assets/destiny/'
MODEL = ASSET + f'models/weapon_surface_w123/{KEY}.json'
TEXTURE = ASSET + f'textures/item/weapon/w123/{KEY}.png'
EDGE = 1024


def module():
    spec = importlib.util.spec_from_file_location('w251_mindbender_base', ROOT / f'scripts/generate_surface_w123_{KEY}.py')
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def encode(v): return (json.dumps(v, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
def sha(v): return hashlib.sha256(v).hexdigest()
def png(im):
    f = io.BytesIO(); im.save(f, 'PNG'); return f.getvalue()


def rotation(r):
    a = [math.radians(r.get(k, r.get('angle', 0) if r.get('axis') == k else 0)) for k in 'xyz']
    x,y,z = a; cx,sx,cy,sy,cz,sz = math.cos(x),math.sin(x),math.cos(y),math.sin(y),math.cos(z),math.sin(z)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]]) @ np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]]) @ np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])


def vertices(e):
    p=np.array([[e['to' if mask>>a&1 else 'from'][a] for a in range(3)] for mask in range(8)])
    o=np.array(e.get('rotation', {}).get('origin', [0,0,0]))
    return (p-o) @ rotation(e.get('rotation', {})).T + o


def refine(d):
    remove = {'forebone', 'grip', 'stock'}
    parts = [p for p in d['parts'] if p['group'] not in remove and p['geometry']['name'] != 'action_solid']
    def box(name,c,size,mat,group,motif='bone',R=None):
        c=np.array(c,float);s=np.array(size,float)
        e={'name':name,'from':np.round(c-s/2,7).tolist(),'to':np.round(c+s/2,7).tolist()}
        if R is not None:
            y=math.asin(float(np.clip(-R[2,0],-1,1)))
            x=math.atan2(R[2,1],R[2,2]); z=math.atan2(R[1,0],R[0,0])
            e['rotation']={'origin':np.round(c,7).tolist(), **{a:round(math.degrees(b),7) for a,b in zip('xyz',(x,y,z))}}
        parts.append(dict(group=group,material=mat,motif=motif,kind='authored_solid',geometry=e))
    def rounded(name,c,size,b,mat,group,motif='bone',angle=0):
        # Six substantial filled volumes form one octagonal cross-section.
        # Bevel strips are the actual silhouette, not coplanar decorative plates.
        w,h,L=size; r=min(b,w*.35,h*.35); c=np.array(c,float); turn=rotation({'x':angle})
        for suffix,sz in [('spine',[w-2*r,h,L]),('wide',[w,h-2*r,L])]:
            box(name+'_'+suffix,c,sz,mat,group,motif,turn)
        for sx in (-1,1):
            for sy in (-1,1):
                off=np.array([sx*(w/2-r),sy*(h/2-r),0]);rc=turn@off+c
                box(f'{name}_facet_{sx}_{sy}',rc,[math.sqrt(2)*r,math.sqrt(2)*r,L],mat,group,motif,turn@rotation({'z':45}))
    def beam(name,a,b,width,depth,mat,group,motif='bone',bevel=.15):
        # a/b are z,y authored landmarks in the original grip frame.
        dz,dy=b[0]-a[0],b[1]-a[1]
        rounded(name,[8,(a[1]+b[1])/2,(a[0]+b[0])/2],[width,depth,math.hypot(dz,dy)],bevel,mat,group,motif,-math.degrees(math.atan2(dy,dz)))
    rounded('action', [8,11.49,5.30],[1.17,1.62,7.40],.20,'blue','receiver','runes')
    rounded('bone_forearm', [8,10.46,-2.64],[1.62,.89,4.92],.22,'bone','forebone')
    beam('bone_front_shoulder',[-5.58,10.35],[-4.71,10.52],1.52,.80,'bone','forebone',bevel=.21)
    beam('bone_rear_shoulder',[-.45,10.45],[.35,10.22],1.48,.81,'bone_edge','forebone',bevel=.21)
    # Two bowed top rails and tapered tooth describe the source's carved fore-end.
    for side in (-1,1):
        c=[8+side*.61,10.91,-2.51]
        rounded(f'bone_long_ridge_{side}',c,[.31,.24,4.27],.065,'bone_edge','forebone')
    beam('bone_terminal_tooth',[-.03,10.05],[.26,9.55],.47,.35,'bone','forebone',bevel=.10)
    beam('grip_neck',[7.17,10.42],[7.60,9.62],.89,1.15,'bone_edge','grip',bevel=.20)
    beam('grip_palm',[7.59,9.64],[8.47,7.71],.92,1.25,'bone','grip',bevel=.23)
    beam('grip_heel',[8.42,7.83],[8.61,7.11],.86,1.17,'bone','grip',bevel=.23)
    beam('grip_hook',[8.60,7.13],[8.22,6.81],.69,.49,'bone_edge','grip',bevel=.14)
    # Broad cheek and a curved rear hook replace the previous two rectangular bars.
    rounded('stock_tang',[8,11.21,10.09],[.72,1.12,1.25],.14,'black','stock','runes')
    beam('stock_cheek',[10.53,11.40],[14.25,11.24],.83,1.17,'bone','stock',bevel=.25)
    beam('stock_crown',[10.72,11.88],[14.26,11.76],.72,.33,'bone_edge','stock',bevel=.10)
    beam('stock_rear_crown',[14.11,11.47],[14.48,10.80],.84,1.07,'bone','stock',bevel=.23)
    beam('stock_hook',[14.48,10.90],[14.39,9.30],.77,.88,'bone','stock',bevel=.23)
    beam('stock_point',[14.39,9.37],[14.18,8.66],.57,.48,'bone_edge','stock',bevel=.15)
    beam('butt_pad',[14.92,11.51],[14.89,9.18],.70,.54,'steel','stock','pad',bevel=.12)
    beam('stock_lower_catch',[11.98,10.63],[12.29,9.96],.62,.63,'steel','stock','pad',bevel=.15)
    for p in parts:
        e=p['geometry'];r=e.get('rotation')
        if r and 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
    d['parts']=parts;d['revision']='W251';d['method']='Authored rounded bone shoulders, continuous metal facets and source-aligned relief UV'
    return d


def compile_model(m,d,maps):
    atlas=Image.new('RGBA',(EDGE,EDGE),(25,32,36,255));requests=[]
    for s in d['parts']:
        s['geometry']['faces']={}
        for f in m.FACES:
            p=vertices(s['geometry'])[list(m.FACES[f])];density=17
            w=max(4,math.ceil(np.linalg.norm(p[1]-p[0])*density));h=max(4,math.ceil(np.linalg.norm(p[3]-p[0])*density))
            requests.append((h,w,s['geometry']['name'],f,s))
    requests.sort(key=lambda q:(-q[0],-q[1],q[2],q[3]));x=y=2;row=0;islands=[]
    for h,w,name,f,s in requests:
        if x+w+2>EDGE:x=2;y+=row+4;row=0
        if y+h+2>EDGE:raise ValueError('Atlas overflow')
        tile=m.tile(s,f,w,h,maps);rgb=np.array(tile).astype(float)
        yy,xx=np.mgrid[:h,:w];u=(xx+.5)/w;v=(yy+.5)/h
        # Material relief remains in the original map. This edge/rim work gives
        # long faces a readable form at neutral full daylight without random grit.
        normal=rotation(s['geometry'].get('rotation',{}))@np.array(m.H['NORMALS'][f])
        direction=.90+.10*max(0,float(normal[1]))+.035*abs(float(normal[0]))
        rim=np.minimum(np.minimum(u,1-u)*w,np.minimum(v,1-v)*h)
        factor=direction+.085*np.exp(-rim/1.15)-.07*np.exp(-(rim-2.2)**2/2.8)
        rgb[:,:,:3]*=factor[:,:,None];rgb[:,:,3]=255
        tile=Image.fromarray(np.uint8(np.clip(rgb,0,255)))
        atlas.paste(Image.fromarray(np.pad(np.array(tile),((2,2),(2,2),(0,0)),mode='edge')),(x-2,y-2))
        s['geometry']['faces'][f]={'uv':[v*16/EDGE for v in (x,y,x+w,y+h)],'texture':'#0'}
        islands.append({'element':name,'face':f,'pixels':[x,y,x+w,y+h]});x+=w+4;row=max(row,h)
    d['atlas']={'size':EDGE,'gutter':2,'islands':islands,'used_height':y+row+2}
    return atlas,{'credit':'W251 Mindbender / source-aligned bone relief and rounded semantic solids','ambientocclusion':True,'gui_light':'side','textures':{'0':f'destiny:item/weapon/w123/{KEY}','particle':f'destiny:item/weapon/w123/{KEY}'},'elements':[copy.deepcopy(s['geometry']) for s in d['parts']],'display':json.loads((ROOT/m.BASE).read_bytes())['display']}


def inspection(m,d,model,atlas):
    es=[];groups=collections.defaultdict(list)
    for s,e in zip(d['parts'],model['elements']):
        b=copy.deepcopy(e);r=b.pop('rotation',{});rot=[r.get(a,r.get('angle',0) if r.get('axis')==a else 0) for a in 'xyz']
        b.update(type='cube',uuid=m.uid(b['name']),origin=r.get('origin',[8,8,8]),rotation=rot,box_uv=False,autouv=0)
        for f in b['faces'].values():f['texture']=0;f['uv']=[v*EDGE/16 for v in f['uv']]
        es.append(b);groups[s['group']].append(b['uuid'])
    return {'meta':{'format_version':'4.10','model_format':'free','box_uv':False},'name':'Mindbender W251 inspection','resolution':{'width':EDGE,'height':EDGE},'elements':es,'outliner':[{'name':g,'uuid':m.uid(g),'origin':[8,8,8],'rotation':[0,0,0],'children':c} for g,c in groups.items()],'textures':[{'name':KEY+'.png','id':'0','uuid':m.uid('texture'),'width':EDGE,'height':EDGE,'uv_width':EDGE,'uv_height':EDGE,'source':'data:image/png;base64,'+base64.b64encode(png(atlas)).decode()}],'display':model['display']}


def compare(m,meshes,before,oldtex,after,atlas):
    W,H=900,340;sheet=Image.new('RGB',(1800,1400),'#171e27');draw=ImageDraw.Draw(sheet)
    draw.text((20,14),'MINDBENDER / W251 / SAME CAMERA AND CPU LIGHT',fill='white',font_size=27)
    photo=Image.open(m.PHOTO).convert('RGB').crop((640,300,1880,770));photo.thumbnail((880,300));sheet.paste(photo,(15,60))
    draw.text((930,75),'Reference: actual default weapon photo',fill='white',font_size=24)
    draw.text((930,115),f'Before {len(before["elements"])} / after {len(after["elements"])} cubes',fill='white',font_size=23)
    draw.text((930,155),'Rounded bone / hooked stock / source relief',fill='white',font_size=21)
    # The old generator uses axis/angle records; the26.3 renderer helper uses XYZ.
    before=copy.deepcopy(before)
    for e in before['elements']:
        r=e.get('rotation')
        if r and 'axis' in r:e['rotation']={'origin':r['origin'],r['axis']:r['angle']}
    points=np.concatenate([v['vertices'] for v in meshes])
    for row,(name,cam) in enumerate([('SIDE',[1,0,0]),('FRONT OBLIQUE',[1,.48,-.65]),('REAR OBLIQUE',[-1,.4,.66])]):
        ext=m.H['frame'](points,cam,W,H)
        for col,(model,tex) in enumerate([(before,oldtex),(after,atlas)]):
            im,_=m.H['render'](m.H['model_triangles']({'full':model},tex),cam,ext,(W,H));sheet.paste(im,(col*W,370+row*H))
            draw.text((col*W+15,380+row*H),('BEFORE' if col==0 else 'W251')+' / '+name,fill='white',font_size=19)
    return png(sheet)


def generate():
    m=module();meshes,meta,ref=m.source_meshes();maps=m.paint_maps(meshes)
    before_d=m.make_design(meta,ref);oldtex,before=m.compile_model(copy.deepcopy(before_d),maps)
    # Current renderer helper accepts native26.3 XYZ rotations; source inputs stay inert.
    m.vertices=vertices
    d=refine(copy.deepcopy(before_d));atlas,model=compile_model(m,d,maps)
    n=len(model['elements']);assert n<=1000
    out={MODEL:encode(model),TEXTURE:png(atlas),ART+'design.json':encode(d),ART+'inspection.bbmodel':encode(inspection(m,d,model,atlas)),ART+'comparison.png':compare(m,meshes,before,oldtex,model,atlas)}
    out[ART+'review.md']=('''# 정신왜곡자의 야망 W251\n\n원작 기본 안료 사진과 기존 리핑 FBX·diffuse를 참고했다. 긴 금속 총몸에 실제 경사면을 만들고, 앞 뼈대의 어깨·손바닥 파지·갈고리 끝·뒤 뼈 개머리판을 굵기가 다른 둥근 단면으로 구성했다. 뼈 홈과 Hive 문자는 원래 방향별 diffuse에서 유지하며 무관한 문양이나 노이즈를 추가하지 않았다.\n\n1024 atlas, 면별 UV와 제한적인 림 명암을 사용한다. 파지 원점·display·총구·조준기·탄약·장전 모션은 유지한다. 비교는 같은 CPU 조명/카메라의 이전/이후이며 실제 게임 검수와 PBR 복원을 뜻하지 않는다. 실제 자원팩·1/3인칭·ADS·장전 검수는 master가 기록한다.\n'''+f'\n출력: {n} cubes / 0 triangle adapters; 이전 {len(before["elements"])}.\n').encode()
    out[ART+'manifest.json']=encode({'revision':'W251','weapon':KEY,'assembled_elements':n,'previous_elements':len(before['elements']),'texture_size':[EDGE,EDGE],'input_sha256':d['input_sha256'],'source':str(m.PHOTO),'display_preserved':model['display']==before['display'],'native_accepted':False,'output_sha256':{k:sha(v) for k,v in out.items()}})
    return out


def main():
    p=argparse.ArgumentParser();p.add_argument('--verify',action='store_true');args=p.parse_args();out=generate()
    for rel,data in out.items():
        target=ROOT/rel
        if args.verify:assert target.read_bytes()==data,rel
        else:target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    print(json.dumps({'weapon':KEY,'elements':json.loads(out[MODEL])['elements'].__len__(),'verified':args.verify}))


if __name__=='__main__':main()
