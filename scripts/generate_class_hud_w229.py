#!/usr/bin/env python3
"""Additive original ability silhouettes; preserves existing Hunter and weapon HUD assets."""
from pathlib import Path
import json
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / 'src/main/resources/assets/destiny'
S = 4

def asset(name, paint):
    im = Image.new('RGBA', (64*S, 64*S))
    d = ImageDraw.Draw(im)
    def line(points, width=3, fill='white'):
        d.line([(x*S,y*S) for x,y in points], fill=fill, width=width*S, joint='curve')
    def poly(points, fill='white'):
        d.polygon([(x*S,y*S) for x,y in points], fill=fill)
    paint(line, poly)
    paths = [ROOT/'textures/item/hud'/f'{name}.png', ROOT/'models/gui/hud'/f'{name}.json', ROOT/'items/gui/hud'/f'{name}.json']
    for p in paths: p.parent.mkdir(parents=True, exist_ok=True)
    im.resize((64,64), Image.Resampling.LANCZOS).save(paths[0])
    model = {'gui_light':'front','textures':{'layer0':'destiny:item/hud/'+name},
             'elements':[{'from':[0,0,8],'to':[16,16,8],'faces':{f:{'texture':'#layer0','uv':[0,0,16,16],'tintindex':0} for f in ('north','south')}}]}
    definition = {'model':{'type':'minecraft:model','model':'destiny:gui/hud/'+name,
                          'tints':[{'type':'minecraft:custom_model_data','index':0,'default':16777215}]}}
    for p,data in zip(paths[1:],[model,definition]): p.write_text(json.dumps(data,indent=2)+'\n')

asset('titan_hammer', lambda l,p:(l([(17,54),(39,16)],7),p([(26,7),(53,23),(47,35),(20,19)]),l([(28,11),(49,24)],2,(30,30,30,255))))
asset('titan_havoc', lambda l,p:(p([(21,13),(28,9),(39,9),(47,17),(46,32),(37,42),(22,38),(15,26)]),l([(9,52),(23,42),(31,55),(41,45),(56,53)],4),l([(30,15),(30,28),(40,28)],2,(30,30,30,255))))
asset('titan_shield', lambda l,p:(l([(32,5),(53,13),(52,36),(43,49),(32,58),(21,49),(12,36),(11,13),(32,5)],4),l([(32,17),(32,44)],5),l([(21,29),(43,29)],5)))
asset('warlock_daybreak', lambda l,p:(p([(48,3),(49,21),(30,43),(23,36)]),l([(17,32),(36,49)],5),l([(25,42),(13,56)],5),l([(9,24),(14,16),(18,23)],3),l([(42,45),(50,38),(55,47)],3)))
asset('warlock_storm', lambda l,p:(p([(34,4),(17,32),(29,32),(21,59),(49,24),(36,24),(44,4)]),l([(9,15),(5,26),(9,38)],2),l([(55,26),(59,38),(54,50)],2)))
asset('warlock_nova', lambda l,p:(l([(32,12),(47,18),(53,32),(46,46),(32,53),(18,46),(12,32),(18,18),(32,12)],5),p([(32,23),(41,32),(32,41),(23,32)]),l([(5,7),(13,15)],3),l([(52,50),(60,57)],3)))
asset('titan_barricade', lambda l,p:(l([(8,53),(8,16),(32,7),(56,16),(56,53)],5),l([(20,18),(20,50)],2),l([(32,15),(32,52)],2),l([(44,18),(44,50)],2),l([(4,56),(60,56)],4)))
asset('warlock_rift', lambda l,p:(l([(8,45),(16,37),(32,34),(48,37),(56,45),(48,53),(32,57),(16,53),(8,45)],3),l([(32,10),(32,40)],4),l([(22,23),(42,23)],4),l([(19,42),(32,47),(45,42)],2)))
asset('warlock_snap', lambda l,p:(l([(15,52),(27,34),(20,24),(25,15),(33,26),(41,17),(47,22),(37,38),(39,51)],7),l([(47,7),(51,1)],2),l([(53,14),(61,12)],2)))
asset('warlock_singularity', lambda l,p:(l([(32,14),(48,22),(48,42),(32,51),(16,42),(16,22),(32,14)],4),p([(32,22),(42,32),(32,43),(22,32)]),l([(4,32),(11,32)],3),l([(53,32),(60,32)],3)))
print('W229: generated 10 class-specific HUD silhouettes')
