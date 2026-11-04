#!/usr/bin/env python3
"""One isolated pack: existing canonical / frozen R4 / current R5, no product writes."""
from pathlib import Path
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parents[2]
RES=ROOT/'src/main/resources'
FROZEN=ROOT/'docs/qa/2026-10-25/w118/r4-whole'
OUTPUT=Path('/private/tmp/destiny-w118-native/server/world/resources.zip')
def dump(v):return (json.dumps(v,separators=(',',':'))+'\n').encode()
def build():
    pins=json.loads((FROZEN/'SHA256SUMS.json').read_text());out={}
    for weapon,family in (('blast_furnace','pulse_rifle'),('hammerhead','machine_gun')):
        for state in ('original','prior_r4','revised'):
            if state=='prior_r4':
                raw=(FROZEN/(weapon+'.json')).read_bytes();texture=(FROZEN/(weapon+'.png')).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==pins[weapon+'.json']
                assert hashlib.sha256(texture).hexdigest()==pins[weapon+'.png']
                model=json.loads(raw)
                # R4 replaces the product atlas. Preserve R4's own pixels/UVs in QA namespace.
                model['textures']={k:'w118qa:item/prior_r4/'+weapon for k in model['textures']}
                raw=dump(model)
                out[f'assets/w118qa/textures/item/prior_r4/{weapon}.png']=texture
            else:
                path=(f'assets/destiny/models/weapon/{family}/{weapon}.json' if state=='original' else
                      f'assets/destiny/models/weapon_surface_w115/{weapon}.json')
                raw=(RES/path).read_bytes()
            key=weapon+'_'+state
            out[f'assets/w118qa/models/{key}.json']=raw
            out[f'assets/w118qa/items/{key}.json']=dump(dict(model=dict(type='minecraft:model',model='w118qa:'+key),hand_animation_on_swap=False))
    out['pack.mcmeta']=dump(dict(pack=dict(description='W118 isolated original / prior R4 / R5 candidates',min_format=[97,1],max_format=[97,1])))
    assert len(out)==15
    return out

if __name__=='__main__':
    assert OUTPUT.parent.is_dir() and not OUTPUT.exists(),'Fresh owned W118 runtime only'
    for p in OUTPUT.parents:assert not p.is_symlink()
    assert json.loads((OUTPUT.parents[2]/'OWNER.json').read_text())['stage']=='W118'
    import importlib.util
    spec=importlib.util.spec_from_file_location('surface_pack',ROOT/'scripts/generate_surface_pack_w115.py')
    assembly=importlib.util.module_from_spec(spec);spec.loader.exec_module(assembly)
    assert all(assembly.art_revision(w)==5 for w in ('blast_furnace','hammerhead')),'Wait for both reviewed R5 candidates before native pack preparation'
    payloads=build()
    with zipfile.ZipFile(OUTPUT,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for name,data in sorted(payloads.items()):
            info=zipfile.ZipInfo(name,date_time=(2026,10,25,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
    print(json.dumps(dict(files=len(payloads),path=str(OUTPUT),sha256=hashlib.sha256(OUTPUT.read_bytes()).hexdigest())))
