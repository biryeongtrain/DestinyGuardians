#!/usr/bin/env python3
"""21 sampled first-person HIP->ADS transforms for all57 ranged entries.
Parent/display children only; actual bow draw/nock remains independent.
W45 snipers stay opaque; LFRs use exact W45 scope endpoints/geometry/tints.
--verify reconstructs bytes read-only. Not client-frame interpolation/IK.
"""
import argparse,copy,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
A=ROOT/'src/main/resources/assets/destiny'
PREFIX='weapon_aim_w70'
SCOPE={'bite_of_the_fox','beloved','apostate','line_in_the_sand','stormchaser'}
BOW={'biting_winds','whispering_slab'}
CONTEXTS=['firstperson_righthand','firstperson_lefthand']
def encode(v):return (json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode()
def sha(v):return hashlib.sha256(v).hexdigest()
def generate():
    output={};inputs={};rows=[]
    def read(path):
        raw=path.read_bytes();inputs[str(path.relative_to(ROOT))]=sha(raw);return json.loads(raw)
    def display(hip,ads,p):
        d=copy.deepcopy(hip)
        for c in CONTEXTS:
            for field in ('rotation','translation','scale'):
                d[c][field]=[round(x+(y-x)*p,6) for x,y in zip(hip[c][field],ads[c][field])]
        return d
    def child(key,parent,d):
        output[A/f'models/{key}.json']=encode({'parent':'destiny:'+parent,'display':d})
        return {'type':'minecraft:model','model':'destiny:'+key}
    def grip(native,two):return {'type':'minecraft:condition','property':'minecraft:custom_model_data','index':0,'on_true':two,'on_false':native}
    def samples(graphs,fallback):return {'type':'minecraft:range_dispatch','property':'minecraft:custom_model_data','index':3,'entries':[{'threshold':f/20,'model':g} for f,g in enumerate(graphs)],'fallback':fallback}
    def scope_select(ordinary,scoped):return {'type':'minecraft:select','property':'minecraft:custom_model_data','index':0,'cases':[{'when':'scope','model':scoped}],'fallback':ordinary}
    def wrapper(original,fp,fallback):
        v=copy.deepcopy(original);v['model']={'type':'minecraft:select','property':'minecraft:display_context','cases':[{'when':CONTEXTS,'model':fp}],'fallback':fallback};return v
    transform=ROOT/'scripts/build_weapons_w30.py';inputs[str(transform.relative_to(ROOT))]=sha(transform.read_bytes())
    two_hand=runpy.run_path(str(transform))['two_hand_display']
    for e in read(ROOT/'art/weapons/w30/catalog.json'):
        if e['family'] in ('sword','glaive'):continue
        wid=e['id'];base=f"weapon/{e['family']}/{wid}";key=f'{PREFIX}/{wid}'
        hip=read(A/f'models/{base}.json');ads=read(A/f'models/{base}_ads.json');original=read(A/f'items/weapon/{wid}.json')
        endpoint=ads['display'];scope=read(A/f'items/weapon_scope_w45/{wid}.json') if wid in SCOPE else None
        is_lfr=e['family']=='linear_fusion_rifle' and scope is not None
        if is_lfr:
            scope_native=read(A/f'models/weapon_scope_w45/{wid}_native.json');endpoint=scope_native['display']
        normal=[];scoped=[]
        for f in range(21):
            d=display(hip['display'],endpoint,f/20)
            normal.append(grip(child(f'{key}_{f:02}_native',base,d),child(f'{key}_{f:02}_twohand',base,two_hand(d,e['family']))))
            if is_lfr:
                graph=copy.deepcopy(scope['model']['cases'][0]['model'])
                for branch,style in [('on_false','native'),('on_true','twohand')]:
                    node=child(f'{key}_scope_{f:02}_{style}',scope_native['parent'].split(':',1)[1],d if style=='native' else two_hand(d,e['family']))
                    graph[branch]['model']=node['model']
                scoped.append(graph)
        fallback=scope_select(original['model'],scope['model']) if scope else original['model']
        fp=samples(normal,original['model'])
        if is_lfr:fp=scope_select(fp,samples(scoped,scope['model']))
        output[A/f'items/{key}.json']=encode(wrapper(original,fp,fallback))
        bow_states=0
        if wid in BOW:
            bow=read(A/f'items/weapon_bow_w50/{wid}.json')
            source_range=bow['model']['cases'][0]['model']['fallback']
            assert source_range['type']=='minecraft:range_dispatch' and source_range['index']==2
            parts={}
            def collect(node):
                if isinstance(node,dict):
                    if node.get('type')=='minecraft:model':
                        parent=node['model'].split(':',1)[1]
                        if parent.startswith('weapon_bow_w50/'):
                            assert parent.endswith('_hip')
                            parts[parent]=read(A/f'models/{parent}.json')
                    for v in node.values():collect(v)
                elif isinstance(node,list):
                    for v in node:collect(v)
            for state in source_range['entries']:collect(state['model'])
            bow_frames=[]
            for f in range(21):
                models={}
                for parent,geo in parts.items():
                    pose_ads=read(A/f'models/{parent[:-4]}_ads.json')
                    suffix=parent.split('/')[-1][len(wid)+1:-4]
                    models['destiny:'+parent]=child(f'{key}_bow_{suffix}_{f:02}',parent,display(geo['display'],pose_ads['display'],f/20))
                def replace(node):
                    if isinstance(node,dict):
                        if node.get('type')=='minecraft:model' and node.get('model') in models:return copy.deepcopy(models[node['model']])
                        return {k:replace(v) for k,v in node.items()}
                    if isinstance(node,list):return [replace(v) for v in node]
                    return node
                frame_range=copy.deepcopy(source_range)
                frame_range['entries']=[{'threshold':v['threshold'],'model':replace(v['model'])} for v in source_range['entries']]
                frame_range['fallback']=normal[f]
                bow_frames.append(frame_range)
            output[A/f'items/{key}_bow.json']=encode(wrapper(bow,samples(bow_frames,bow['model']),bow['model']))
            bow_states=len(source_range['entries'])
        rows.append(dict(id=wid,family=e['family'],frames=21,grips=['native','twohand'],bowStates=bow_states,
                         scope=is_lfr,opaqueScope=e['family']=='sniper_rifle' and scope is not None,
                         endpoint='W45 scope display' if is_lfr else 'original W30 ADS display'))
    assert len(rows)==57
    output[ROOT/'art/weapons/w70/manifest.json']=encode(dict(stage='W70',generator='scripts/generate_aim_models_w70.py',frames=21,progressFloatIndex=3,
        interpolation='Linear Euler/translation/scale endpoints at20TPS sampled progress; not render-frame interpolation.',
        newGeometry=0,newTextures=0,originalsUnchanged=True,nativeGameplayVerified=False,handIK=False,weapons=rows,
        inputSha256=inputs,outputSha256={str(p.relative_to(ROOT)):sha(raw) for p,raw in output.items()}))
    return output
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    out=generate()
    for path,raw in out.items():
        if a.verify:
            if not path.is_file() or path.read_bytes()!=raw:raise SystemExit('W70 asset differs: '+str(path.relative_to(ROOT)))
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    print(f'{"Verified" if a.verify else "Generated"} {len(out)} W70 files')
