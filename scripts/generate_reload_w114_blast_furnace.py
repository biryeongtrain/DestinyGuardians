#!/usr/bin/env python3
"""Blast Furnace W114: inert FBX bone/component/material audit and preserved-cube reload.

Use bundled Python (numpy + Pillow). No DCC, subprocess, network, or cache writes.
Motion is authored after inspecting gameplay, never an animation extraction or IK.
"""
import argparse
import collections
import copy
import hashlib
import io
import itertools
import json
import math
from pathlib import Path
import runpy
import struct
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/destiny'
ART = ROOT / 'art/weapons/w114/blast_furnace'
CACHE = Path('/private/tmp/destiny-weapons-w30/raw/blast_furnace')
KEY = 'weapon_reload_w114_blast_furnace/blast_furnace'
BASE = ASSETS / 'models/weapon/pulse_rifle/blast_furnace.json'
BB = ROOT / 'art/blockbench/weapons/w30/blast_furnace.bbmodel'
FP = ('firstperson_righthand', 'firstperson_lefthand')
PARTS = ('body', 'magazine')
PINS = {'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace_ads.json': '4358fec3f9f1d219543e3ccfc9e441202f883c68bd36d6cedb0e6287be75cd16', 'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace_ads_twohand.json': '028ca734c9a015f082cea232dec18efe06fb9acd23298ae101409182f289ff50', 'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace_twohand.json': '7ce89d2955a298345af08da2083442cdb5ae0c9b168084b085635ecdce83a701', 'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace_inspect_twohand.json': '3a5ce08c0fbd7d93053b761d95e6304bd33fed76e365b6f367266979d6999826', 'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace.json': 'f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706', 'src/main/resources/assets/destiny/models/weapon/pulse_rifle/blast_furnace_inspect.json': 'b616a580f161daf2c0df046edf3b0bbfaee58525707fced7bcf7d748e1cd2674', 'src/main/resources/assets/destiny/items/weapon/blast_furnace.json': 'c5bd18e5ced35dcbfe9bc3ea68a950684104e0907a29f833eb2e97865a2b3d02', 'src/main/resources/assets/destiny/textures/item/weapon/w30/blast_furnace.png': '0f252ca03244d8b2d7d5c63e9d67c90dc87e6bbac3faeb402572aacb7df4cd91', 'art/blockbench/weapons/w30/blast_furnace.bbmodel': '1bc6e5720e7579a952550ca30795bcd31df02c8c5e5e78f0539d0d854f669bc4', 'scripts/build_weapons_w30.py': 'e087fca588231486505691e97b5c2b581382c1055c76d64300dbc24118bf1d83', 'scripts/generate_reload_models_w100.py': 'aef69a0be0a2b4f84c87ff33ce4ca56faf637dcb24b34806293b34b4ea21e97c'}
ARCHIVE_SHA = 'ee15b5351ff45ab2e758780af44c7815eda9e43298805d85326314fa22f3f8ae'
RAW_PINS = {
 'Blast Furnace/Blast Furnace.blend': '7a108d0d15ea50ccc03a1dc9893ad5763116a6658294ac092a6a2b5c3f68aa17',
 'Blast Furnace/Blast Furnace.fbx': '715694ca476cc7a7d42cb6ceeede5758ebad8b237d4955ef9069d62ec3b76c17',
}
# Observed 38.9: turn up; 39.1..39.7: held high/removed; 39.9..40.1:
# replacement approaches underside; 40.3..40.7: seat/return; 40.9: ready.
# Approximate authored rotation/framing/trajectory, with original HIP endpoints.
KEYS = [
 (0, [0,0,0], [0,0,0], [0,0,0]),
 (.10, [8,-6,-18], [-.3,1.0,-.3], [0,0,0]),
 (.22, [58,-10,-22], [-.7,2.8,-.8], [0,-2.0,.15]),
 (.36, [66,-12,-26], [-.8,3.2,-1], [.2,-5.8,.35]),
 (.48, [66,-12,-26], [-.8,3.2,-1], [.2,-5.8,.35]),
 (.62, [64,-11,-25], [-.8,3.1,-1], [.1,-3.4,.2]),
 (.72, [67,-9,-23], [-.6,3.0,-.8], [0,0,0]),
 (.80, [60,-8,-21], [-.4,2.7,-.6], [0,0,0]),
 (.90, [26,-4,-12], [-.1,1.2,-.25], [0,0,0]),
 (1, [0,0,0], [0,0,0], [0,0,0]),
]


def encode(v):
    return (json.dumps(v, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode()


def sha(v):
    return hashlib.sha256(v).hexdigest()


def helpers():
    return runpy.run_path(str(ROOT / 'scripts/generate_reload_models_w100.py'))


def verify_inputs():
    assert sha((CACHE / 'source.archive').read_bytes()) == ARCHIVE_SHA, 'Source archive drift'
    for name, pin in PINS.items():
        assert sha((ROOT / name).read_bytes()) == pin, 'Original drift: ' + name
    for name, pin in RAW_PINS.items():
        assert sha((CACHE / 'extracted' / name).read_bytes()) == pin, 'Raw source drift: ' + name
    provenance = json.loads((ART / 'gameplay-provenance.json').read_bytes())
    assert len(provenance['frames']) == 16
    for f in provenance['frames']:
        assert sha((ROOT / f['path']).read_bytes()) == f['sha256'], f['path']
    return provenance


def source_meshes():
    """Read actual FBX links, skin weights, material slots, and welded topology."""
    h = helpers()
    roots = h['parse_fbx'](CACHE / 'extracted/Blast Furnace/Blast Furnace.fbx')
    objects = next(n[2] for n in roots if n[0] == 'Objects')
    by_id = {n[1][0]: n for n in objects}
    links = [n[1][1:] for r in roots if r[0] == 'Connections' for n in r[2] if n[1][0] == 'OO']
    bb = json.loads(BB.read_bytes())['destiny_w30']
    meshes = []
    for node in objects:
        if node[0] != 'Geometry':
            continue
        gid = node[1][0]
        mid = next(p for c,p in links if c == gid)
        model = by_id[mid]
        name = model[1][1].split('\x00')[0]
        if name not in bb['source_objects']:
            assert name in bb['excluded_objects']
            continue
        props = {p[1][0]: p[1][4:] for c in model[2] if c[0]=='Properties70' for p in c[2]}
        assert all(abs(x-y)<2e-5 for x,y in zip(props['Lcl Rotation'],[-90,0,0]))
        assert all(abs(x-100)<2e-5 for x in props['Lcl Scaling'])
        assert max(map(abs,props['Lcl Translation']))<2e-6
        ch = {c[0]:c for c in node[2]}
        values = ch['Vertices'][1][0]
        raw = list(zip(values[::3],values[1::3],values[2::3]))
        # W30's exact source basis: thin=X, length=Y (muzzle negative), up=Z.
        vertices = [[p[0]*bb['scale']+8,p[2]*bb['scale']+8,p[1]*bb['scale']+8] for p in raw]
        faces, face = [], []
        for i in ch['PolygonVertexIndex'][1][0]:
            face.append(i if i>=0 else -i-1)
            if i<0:
                assert len(face)==3
                faces.append(tuple(face)); face=[]
        assert not face
        materials = [by_id[c][1][1].split('\x00')[0] for c,p in links if p==mid and by_id[c][0]=='Material']
        layer = {c[0]:c[1] for c in ch['LayerElementMaterial'][2]}
        assert layer['MappingInformationType']==['AllSame']
        material = materials[layer['Materials'][0][0]]
        skin = next(c for c,p in links if p==gid and by_id[c][0]=='Deformer')
        weights = {}
        for cid,pid in links:
            if pid != skin:
                continue
            cluster = by_id[cid]
            bone_id = next(c for c,p in links if p==cid and by_id[c][0]=='Model')
            bone = by_id[bone_id][1][1].split('\x00')[0]
            data = {c[0]:c[1] for c in cluster[2]}
            weights[bone] = dict(zip(data.get('Indexes',[[]])[0], data.get('Weights',[[]])[0]))
        mag = weights.get('Magazine',{})
        face_mag = [all(mag.get(v,0)>.5 for v in f) for f in faces]
        assert all(all(mag.get(v,0)>.5 for v in f) or all(mag.get(v,0)<=.5 for v in f) for f in faces)
        parent = list(range(len(raw)))
        def root(i):
            while parent[i]!=i:
                parent[i]=parent[parent[i]]; i=parent[i]
            return i
        def union(a,b): parent[root(a)]=root(b)
        seen = {}
        for i,v in enumerate(raw):
            key=tuple(round(x,6) for x in v)
            if key in seen: union(i,seen[key])
            seen[key]=i
        for a,b,c in faces: union(a,b);union(a,c)
        groups=collections.defaultdict(list)
        for i,f in enumerate(faces): groups[root(f[0])].append(i)
        groups=sorted(groups.values(),key=lambda fs:(-len(fs),min(fs)))
        comps=[]
        for ci,indices in enumerate(groups):
            comps.append(dict(component=ci,sourcePolygonIndices=indices,triangleCount=len(indices),
                magazineTriangles=sum(face_mag[i] for i in indices),
                bounds=h['bounds']([vertices[v] for i in indices for v in faces[i]])))
        meshes.append(dict(name=name,geometryId=gid,material=material,vertices=vertices,faces=faces,
            faceMagazine=face_mag,components=comps,
            boneWeights={b:dict(vertexCount=len(w),minWeight=min(w.values()) if w else None,
                               maxWeight=max(w.values()) if w else None) for b,w in weights.items()}))
    assert sum(len(m['faces']) for m in meshes)==bb['source_triangles']==29124
    bounds=h['bounds']([v for m in meshes for v in m['vertices']])
    assert np.max(np.abs(np.array(bounds)-bb['model_bounds']))<2e-5
    return meshes


def point_triangle_distances(points, triangles):
    """Exact closest distance to triangle planes/interiors or their three edges."""
    p=np.asarray(points)[:,None,:]; t=np.asarray(triangles)[None,:,:,:]
    a,b,c=t[:,:,0],t[:,:,1],t[:,:,2]
    ab=b-a; ac=c-a; ap=p-a
    dot=lambda x,y:np.sum(x*y,axis=-1)
    aa=dot(ab,ab);bb=dot(ab,ac);cc=dot(ac,ac)
    u=dot(ap,ab);v=dot(ap,ac);den=aa*cc-bb*bb
    safe=np.where(den>1e-24,den,1)
    s=(cc*u-bb*v)/safe;tcoord=(aa*v-bb*u)/safe
    projection=a+s[:,:,None]*ab+tcoord[:,:,None]*ac
    plane=dot(p-projection,p-projection)
    result=np.where((s>=0)&(tcoord>=0)&(s+tcoord<=1)&(den>1e-24),plane,np.inf)
    for q,r in ((a,b),(b,c),(c,a)):
        edge=r-q; d=dot(edge,edge)
        frac=np.clip(dot(p-q,edge)/np.where(d>1e-24,d,1),0,1)
        delta=p-(q+frac[:,:,None]*edge)
        result=np.minimum(result,dot(delta,delta))
    return np.sqrt(np.min(result,axis=1))


def partition_audit(meshes, original):
    h=helpers();triangles=[];labels=[];owners=[];component_rows=[]
    for mesh in meshes:
        component_of={i:c['component'] for c in mesh['components'] for i in c['sourcePolygonIndices']}
        for c in mesh['components']:
            component_rows.append(dict(mesh=mesh['name'],material=mesh['material'],**c))
        for i,f in enumerate(mesh['faces']):
            triangles.append([mesh['vertices'][v] for v in f]);labels.append(mesh['faceMagazine'][i])
            owners.append((mesh['name'],component_of[i],mesh['material']))
    triangles=np.array(triangles);labels=np.array(labels,dtype=bool)
    lows=triangles.min(axis=1);highs=triangles.max(axis=1)
    rows=[]
    for i,cube in enumerate(original['elements']):
        lo=np.array(cube['from']);hi=np.array(cube['to']); votes=collections.defaultdict(float)
        hits=np.where(np.all(highs>=lo,axis=1)&np.all(lows<=hi,axis=1))[0]
        mag_below_upper_merge=0.0
        for ti in hits:
            polygon=triangles[ti].tolist()
            for axis in range(3):
                polygon=h['clip_polygon'](polygon,axis,float(lo[axis]),1)
                polygon=h['clip_polygon'](polygon,axis,float(hi[axis]),-1)
                if not polygon:break
            area=h['polygon_area'](polygon)
            if area>1e-10:
                votes[(bool(labels[ti]),owners[ti])]+=area
                if labels[ti]:
                    mag_below_upper_merge += h['polygon_area'](h['clip_polygon'](polygon,1,9.268129,-1))
        total=sum(votes.values());mag=sum(v for (is_mag,_),v in votes.items() if is_mag)
        center=(lo+hi)/2
        samples=[center.tolist()]
        for axis in range(3):
            for edge in (lo,hi):
                p=center.copy();p[axis]=edge[axis];samples.append(p.tolist())
        dm=point_triangle_distances(samples,triangles[labels]);db=point_triangle_distances(samples,triangles[~labels])
        distance_votes=int(np.sum(dm<db))
        selected=mag>total*.5 if total>1e-10 else distance_votes>=4
        rows.append(dict(index=i,part='magazine' if selected else 'body',
            originalElementSha256=sha(encode(cube)),clippedArea=total,magazineArea=mag,
            magazineAreaBelowUpperMerge=mag_below_upper_merge,
            magazineAreaShare=mag/total if total else 0,mixed=mag>1e-8 and total-mag>1e-8,
            sourceSurfaces=[dict(magazine=k[0],mesh=k[1][0],component=k[1][1],material=k[1][2],area=v)
                for k,v in sorted(votes.items(),key=lambda kv:(-kv[1],kv[0]))],
            surfaceDistance=dict(samplePoints=samples,magazine=[round(float(x),8) for x in dm],
                body=[round(float(x),8) for x in db],magazineVotes=distance_votes,
                method='exact point-to-triangle minimum; cube center plus six face centers',
                agreesWithArea=(distance_votes>=4)==selected)))
    indices={part:[r['index'] for r in rows if r['part']==part] for part in PARTS}
    rawarea=sum(h['polygon_area'](t.tolist()) for t in triangles[labels])
    selected_mag=sum(r['magazineArea'] for r in rows if r['part']=='magazine')
    all_mag=sum(r['magazineArea'] for r in rows)
    retained=[r for r in rows if r['part']=='body' and r['magazineArea']>1e-8]
    retained_area=sum(r['magazineArea'] for r in retained)
    retained_below=sum(r['magazineAreaBelowUpperMerge'] for r in retained)
    all_below=sum(r['magazineAreaBelowUpperMerge'] for r in rows)
    region=dict(upperMergeBoundaryY=9.268129,
        boundaryMeaning='Diagnostic model-space cut at the first large fixed-majority merged well cube; not a measured joint, socket or gameplay occlusion plane.',
        retainedIndices=[r['index'] for r in retained],retainedClippedMagazineArea=retained_area,
        retainedAboveUpperMergeArea=retained_area-retained_below,
        retainedAboveUpperMergeFraction=(retained_area-retained_below)/retained_area,
        retainedBelowUpperMergeArea=retained_below,
        lowerRegionAllClippedMagazineArea=all_below,
        lowerRegionCapturedClippedMagazineArea=all_below-retained_below,
        lowerRegionCapturedFraction=(all_below-retained_below)/all_below,
        retainedCubeBounds=h['bounds']([p for r in retained for p in (
            original['elements'][r['index']]['from'],original['elements'][r['index']]['to'])]),
        interpretation='The selected cubes carry the exposed lower hull. Residual magazine area is concentrated in upper well/receiver cubes whose fixed surfaces have the majority. Footage hands occlude that region during exchange; static geometry supports upper-region placement, but does not prove all residual surfaces invisible in native views. A visible retained collar/stub is possible.',
        allClippedMagazineArea=all_mag,selectedClippedMagazineArea=selected_mag,
        rawMagazineArea=rawarea,rawAreaOutsideOriginalCubes=rawarea-all_mag,
        perfectMagazineExtraction=False)
    return dict(stage='W114',weapon='blast_furnace',sourceCubes=249,sourceTriangles=29124,
        classification='strict majority of actual source triangle area clipped to original whole cube; source Magazine skin weights identify moving surfaces',
        sourceMapping='(X,Z,Y) * 30.010419887180735 + (8,8,8); export carrier checked, float source drift <2e-5',
        semanticEvidence='Magazine bone -> Cluster 981254637 -> Skin 654724438 -> Geometry 1967849; 575 vertices weight 1.0, Frame material',
        boundsOnlyForBroadPhase=True,parts=indices,partCounts={k:len(v) for k,v in indices.items()},
        sourceMeshes=[{k:v for k,v in m.items() if k not in ('vertices','faces','faceMagazine','components')} for m in meshes],
        sourceComponents=component_rows,magazineTriangles=int(labels.sum()),
        approximation=dict(wholeCubeSeams=True,perfectMagazineExtraction=False,upperWellResidual=region,rawMagazineArea=rawarea,
            selectedClippedMagazineArea=sum(r['magazineArea'] for r in rows if r['part']=='magazine'),
            capturedClippedMagazineFraction=sum(r['magazineArea'] for r in rows if r['part']=='magazine')/sum(r['magazineArea'] for r in rows),
            capturedRawMagazineFraction=sum(r['magazineArea'] for r in rows if r['part']=='magazine')/rawarea,
            retainedMixedIndices=[r['index'] for r in rows if r['mixed'] and r['part']=='body'],
            alternativeDistanceMajority=dict(indices=[r['index'] for r in rows if r['surfaceDistance']['magazineVotes']>=4],
                explanation='Would additionally transfer upper receiver/well cubes 57,59,61 with more fixed than moving source area. Rejected to keep fixed-majority surfaces on receiver.'),
            allClippedMagazineArea=sum(r['magazineArea'] for r in rows),
            carriedBodyArea=sum(r['clippedArea']-r['magazineArea'] for r in rows if r['part']=='magazine'),
            mixedSelected=[r['index'] for r in rows if r['mixed'] and r['part']=='magazine'],
            distanceDisagreements=[r['index'] for r in rows if not r['surfaceDistance']['agreesWithArea']],
            explanation='Original volume cubes merge nearby surfaces. Whole-cube area majority approximates seams; no new faces, geometry, UV or textures.'),
        cubes=rows)


def sample(progress):
    if not math.isfinite(progress) or not 0<=progress<=1:raise ValueError(progress)
    for a,b in zip(KEYS,KEYS[1:]):
        if progress<=b[0]:
            t=(progress-a[0])/(b[0]-a[0]);t=t*t*(3-2*t)
            return tuple([a[col][i]+(b[col][i]-a[col][i])*t for i in range(3)] for col in (1,2,3))
    raise ValueError(progress)


def png(image):
    data=io.BytesIO();image.save(data,format='PNG',compress_level=9);return data.getvalue()


def partition_contact(meshes,audit,original):
    out=Image.new('RGB',(1400,740),'#111723');d=ImageDraw.Draw(out)
    d.text((20,15),'BLAST FURNACE W114 / ACTUAL FBX TRIANGLES (left) / UNCHANGED ORIGINAL CUBES (right)',fill='white')
    d.text((20,40),'GREEN = Magazine bone surfaces; GREY = Pedestal / sights; AMBER = selected whole cube with mixed fixed surfaces',fill='white')
    for panel in range(2):
        def project(p):return (round(30+panel*700+(p[2]+8)*25),round(530-(p[1]-6)*45))
        if panel==0:
            for selected in (False,True):
                for m in meshes:
                    for f,mag in zip(m['faces'],m['faceMagazine']):
                        if mag!=selected:continue
                        points=[project(m['vertices'][v]) for v in f]
                        d.line(points+[points[0]],fill='#40e6b8' if mag else '#617991',width=1)
        else:
            for row in sorted(audit['cubes'],key=lambda r:r['part']=='magazine'):
                cube=original['elements'][row['index']];a=project(cube['from']);b=project(cube['to'])
                color='#ffae4a' if row['mixed'] and row['part']=='magazine' else '#40e6b8' if row['part']=='magazine' else '#617991'
                d.rectangle((min(a[0],b[0]),min(a[1],b[1]),max(a[0],b[0]),max(a[1],b[1])),outline=color)
                if row['part']=='magazine':d.text((a[0],b[1]),str(row['index']),fill='white')
    d.text((20,590),f"249 whole cubes; {audit['partCounts']} / {audit['magazineTriangles']} actual magazine triangles",fill='white')
    d.text((20,620),'Area clipping decides cube membership; seven exact triangle-distance samples per cube provide independent seam diagnostics.',fill='white')
    d.text((20,680),'CAPTURE: 53.81% raw / 58.36% clipped Magazine area; 8 mixed moving cubes / 6 fixed-majority retained upper-well cubes.',fill='white')
    d.text((20,705),'99.82% of retained area is above Y=9.268129; lower-region capture 99.82%. Not a perfect magazine extraction.',fill='white')
    d.text((20,650),'STATIC DATA AUDIT / NO DCC LIVE CONTROL / NO NEW COVER MECHANISM / NO GEOMETRY OR UV REBAKE',fill='white')
    return png(out)


def preview_contact(original,audit):
    out=Image.new('RGB',(1400,840),'#111723');d=ImageDraw.Draw(out);rotate=helpers()['rotate']
    d.text((15,10),'W114 BLAST FURNACE / AUTHORED LOCAL SIDE PROJECTION / NOT MINECRAFT FRAMEBUFFER OR HAND IK',fill='white')
    for frame in range(21):
        x=frame%7*200;y=frame//7*270+30;rot,translation,offset=sample(frame/20)
        d.text((x+5,y+5),f'{frame:02d} / {frame/20:.2f}',fill='white')
        for row in sorted(audit['cubes'],key=lambda r:r['part']=='magazine'):
            c=original['elements'][row['index']];points=[]
            for v in itertools.product(*zip(c['from'],c['to'])):
                local=[v[i]-8+(offset[i] if row['part']=='magazine' else 0) for i in range(3)]
                # Oblique view shows the vertical body roll and magazine departure.
                v=rotate(local,rot);points.append((x+95+(v[2]+v[0]*.5)*5,y+150-(v[1]+v[0]*.4+translation[1])*8))
            for i,a in enumerate(points):
                for j in range(i):
                    if (i^j) in (1,2,4):d.line((a,points[j]),fill='#40e6b8' if row['part']=='magazine' else '#92a8c0')
    return png(out)


def generate():
    provenance=verify_inputs();original=json.loads(BASE.read_bytes())
    assert len(original['elements'])==249
    meshes=source_meshes();audit=partition_audit(meshes,original)
    out={ART/'partition-audit.json':encode(audit),ART/'partition-contact.png':partition_contact(meshes,audit,original),
         ART/'preview-contact.png':preview_contact(original,audit)}
    out[ART/'original-model-audit.json']=encode(dict(sourcePins=PINS,rawSourcePins=RAW_PINS,
        archiveSha256=ARCHIVE_SHA,cubeCount=249,sourceTriangles=29124,
        originalElementSha256=[sha(encode(e)) for e in original['elements']],
        textures=original['textures'],sourceObjects=json.loads(BB.read_bytes())['destiny_w30']['source_objects'],
        excludedObjects=json.loads(BB.read_bytes())['destiny_w30']['excluded_objects'],
        parser='read-only inert FBX 7400; no scene execution',
        animationNodes=0,sourceAnimationRecovered=False,coverEvidence=False))
    two_hand=runpy.run_path(str(ROOT/'scripts/build_weapons_w30.py'))['two_hand_display']
    two_base=json.loads((BASE.parent/'blast_furnace_twohand.json').read_bytes())['display']
    source_item=json.loads((ASSETS/'items/weapon/blast_furnace.json').read_bytes())
    for part,indices in audit['parts'].items():
        geo={k:copy.deepcopy(v) for k,v in original.items() if k not in ('elements','display')}
        geo['elements']=[copy.deepcopy(original['elements'][i]) for i in indices]
        out[ASSETS/f'models/{KEY}_{part}.json']=encode(geo)
    entries=[]
    for frame in range(21):
        rotation,translation,offset=sample(frame/20);parts={}
        for part in PARTS:
            display=copy.deepcopy(original['display'])
            if frame not in (0,20):
                for context in FP:
                    pose=display[context]
                    pose['rotation']=[round(v+rotation[i],6) for i,v in enumerate(pose['rotation'])]
                    local=helpers()['rotate'](offset,pose['rotation']) if part=='magazine' else [0,0,0]
                    pose['translation']=[round(v+translation[i]+local[i]*pose['scale'][i],6) for i,v in enumerate(pose['translation'])]
            for grip in ('native','twohand'):
                name=f'{KEY}_{frame:02d}_{part}_{grip}'
                pose=display if grip=='native' else two_base if frame in (0,20) else two_hand(display,'pulse_rifle')
                # All non-FP displays keep the exact corresponding accepted carrier base.
                if grip=='twohand':
                    pose=copy.deepcopy(pose)
                    for context in two_base:
                        if context not in FP:pose[context]=copy.deepcopy(two_base[context])
                out[ASSETS/f'models/{name}.json']=encode(dict(parent=f'destiny:{KEY}_{part}',display=pose))
                parts[part,grip]=dict(type='minecraft:model',model='destiny:'+name)
        def composite(grip):return dict(type='minecraft:composite',models=[parts[p,grip] for p in PARTS])
        entries.append(dict(threshold=frame/20,model=dict(type='minecraft:condition',property='minecraft:custom_model_data',index=0,
            on_true=composite('twohand'),on_false=composite('native'))))
    item=copy.deepcopy(source_item)
    item['model']=dict(type='minecraft:select',property='minecraft:display_context',
        cases=[dict(when=list(FP),model=dict(type='minecraft:range_dispatch',property='minecraft:custom_model_data',index=1,
            entries=entries,fallback=source_item['model']))],fallback=source_item['model'])
    out[ASSETS/f'items/{KEY}.json']=encode(item)
    inspection=json.loads(BB.read_bytes());inspection['name']='W114 Blast Furnace / body + source Magazine / static inspection'
    inspection['outliner']=[dict(name=part,origin=[8,8,8],uuid='aad11400-0000-4000-8000-'+('000000000001' if part=='body' else '000000000002'),
        children=[inspection['elements'][i]['uuid'] for i in indices],export=True,isOpen=True) for part,indices in audit['parts'].items()]
    inspection['destiny_w114']=dict(partition='partition-audit.json',motion='authored approximation; static grouped inspection only',
        originalElementOrderPreserved=True,handIK=False)
    out[ART/'inspection.bbmodel']=encode(inspection)
    asset_paths=[p for p in out if p.is_relative_to(ASSETS)]
    assert len(asset_paths)==87
    out[ART/'manifest.json']=encode(dict(stage='W114',weapon='blast_furnace',graphId='destiny:'+KEY,
        generator='scripts/generate_reload_w114_blast_furnace.py',generatorSha256=sha(Path(__file__).read_bytes()),
        assets=87,frames=21,parts=list(PARTS),partCounts=audit['partCounts'],sourceCubes=249,compositeCubes=249,
        progressFloatIndex=1,gripBooleanIndex=0,firstPersonContexts=list(FP),keyframes=KEYS,
        originalSha256=PINS,rawSourceSha256=RAW_PINS,sourceAnimationRecovered=False,handIK=False,
        exactAnimationRip=False,authoredApproximation=True,nativeGameplayVerified=False,
        originalGraphFallbackExact=True,endpointsExactBaseDisplay=True,
        partitionFidelity=audit['approximation'],
        referenceObservations=provenance['observations'],
        limitations='Only 53.81% raw / 58.36% cube-clipped Magazine area moves; eight mixed selected and six fixed-majority retained well cubes. Upper residual collar/stub may remain visible: not perfect magazine extraction. Whole-cube seams approximate original skin boundary. Gameplay hand occludes exact path. Authored transforms/normalized timing, no hands/IK, no bolt or cover, no native client acceptance. Existing runtime/audio/ammo owned by master.',
        sha256={str(p.relative_to(ROOT)):sha(out[p]) for p in asset_paths},
        evidenceSha256={str(p.relative_to(ROOT)):sha(v) for p,v in out.items() if not p.is_relative_to(ASSETS)},
        referenceSha256={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in sorted(ART.glob('reference-*.png'))+[
            ART/'gameplay-provenance.json',ART/'gameplay-contact.png',ART/'reference-notes.md']}))
    return out


def owned_paths():
    batch=json.loads(Path('/private/tmp/destiny-w114/batch.json').read_bytes())
    return set(next(f['owned_paths'] for f in batch['features'] if f['name']=='w114-blast_furnace'))


def write_outputs(outputs,check=False):
    owned=owned_paths()
    for path,data in outputs.items():
        relative=str(path.relative_to(ROOT));assert relative in owned,relative
        if check:assert path.is_file() and path.read_bytes()==data,'Generated output differs: '+relative
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    outputs=generate();write_outputs(outputs,args.check)
    print(('Checked' if args.check else 'Generated')+f' {len(outputs)} deterministic files / 87 assets / 21 frames / 249 original cubes')


if __name__=='__main__':main()
