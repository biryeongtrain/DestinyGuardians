#!/usr/bin/env python3
"""Shared W350 hand wrappers and HUD aliases. Never changes authored worker geometry."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
ASSETS=ROOT/'src/main/resources/assets/destiny'
DATA=ROOT/'src/main/resources/destiny/weapons/w350-exotics.json'
def write(p,data):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(data,separators=(',',':'))+'\n')
def main():
    rows=json.loads(DATA.read_text())
    template_item=json.loads((ASSETS/'items/gui/hud/ammo_weapon_w112_ace_of_spades.json').read_text())
    template_model=json.loads((ASSETS/'models/gui/hud/ammo_weapon_w112_ace_of_spades.json').read_text())
    for r in rows:
        id=r['catalog']['id']
        for prefix in ['weapon/','weapon_reload_w350/','weapon_aim_w350/']:
            src=ASSETS/'items'/(prefix+id+'.json')
            write(ASSETS/'items/weapon_hands_w201'/(prefix+id+'.json'),json.loads(src.read_text()))
        key='ammo_weapon_w112_'+id
        item=json.loads(json.dumps(template_item).replace('ammo_weapon_w112_ace_of_spades',key))
        model=json.loads(json.dumps(template_model))
        candidates=[f'item/hud/w350/ammo_{id}',f'item/weapon/w350/{id}_hud']
        texture=next(t for t in candidates if (ASSETS/'textures'/(t+'.png')).exists())
        model['textures']['layer0']='destiny:'+texture
        write(ASSETS/'items/gui/hud'/(key+'.json'),item)
        write(ASSETS/'models/gui/hud'/(key+'.json'),model)
    # Shared circular sniper mask; the gun remains visible to observers, not inside its own optic.
    scope={'model':{'type':'minecraft:select','property':'minecraft:display_context',
        'cases':[{'when':['firstperson_righthand','firstperson_lefthand'],'model':{'type':'minecraft:empty'}}],
        'fallback':{'type':'minecraft:model','model':'destiny:weapon_w350/whisper_of_the_worm/full'}}}
    write(ASSETS/'items/weapon_scope_w350/whisper_of_the_worm.json',scope)
    write(ASSETS/'items/weapon_hands_w201/weapon_scope_w350/whisper_of_the_worm.json',scope)
    # Keep lossless placement pins current when an authored atlas changes after native review.
    atlas_catalog=ROOT/'src/main/resources/destiny/pack/atlas_routes.json'
    catalog=json.loads(atlas_catalog.read_text())
    prefix='assets/destiny/textures/item/weapon/w350/'
    catalog['routes']=[r for r in catalog['routes'] if r['texturePrefix']!=prefix]
    routes=[]
    for row in rows:
        id=row['catalog']['id']
        atlas=ASSETS/'textures/item/weapon/w350'/(id+'.png')
        route={'sha256':hashlib.sha256(atlas.read_bytes()).hexdigest(),
               'texturePrefix':prefix,'from':'minecraft:items','to':'minecraft:blocks'}
        catalog['routes'].append(route)
        routes.append({'id':id,**route})
    atlas_catalog.write_text(json.dumps(catalog,indent=2)+'\n')
    write(ROOT/'art/weapons/w350/atlas-routing.json',{
        'reason':'Native R2 item atlas stitching overflow; lossless placement in the existing block atlas.',
        'routes':routes})
    print('Prepared 27 hand wrappers, nine HUD silhouettes and the Whisper scope route')
if __name__=='__main__': main()
