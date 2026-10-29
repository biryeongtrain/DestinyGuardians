#!/usr/bin/env python3
"""W251 용광로 형상·면 UV. 원본 semantic 설계로부터 결정적으로 재생성."""
import sys
sys.dont_write_bytecode=True
import generate_surface_w123_blast_furnace as original
from refine_weapon_w251_hammerhead import Author,run

def design(meshes,meta):
    d=original.make_design(meshes,meta);a=Author(d)
    contact={s['geometry']['name']:s for ss in d['parts'].values() for s in ss}
    a.remove('Receiver_main','Receiver_rear','Receiver_crown_front','Receiver_bridge','Upper_shoulder_-1','Upper_shoulder_1',
        'Front_crown','Front_roof_chamfer_-1','Front_roof_chamfer_1','Front_nose_block','Front_lower_core','Front_panel_notch',
        'Cheek_pad','Cheek_shoulder_-1','Cheek_shoulder_1','Grip_core','Grip_backstrap','Stock_buttpad',
        'Magazine_core','Magazine_floorplate','Optic_post_-1','Optic_post_1','Optic_hood','Red_breech','Breech_bevel_-1','Breech_bevel_1')
    # Front roof is a broad, continuous convex crown. Side slots stay genuinely
    # open onto the red barrel. Solid lower panel ends with a diagonal notch.
    a.section('W251_foreend_roof',[8,13.39,-1.59],[1.80,.60,8.68],.22,'crown','foreend','crown')
    a.section('W251_foreend_nose',[8,12.53,-4.75],[1.86,1.44,2.56],.29,'frame','foreend','nose')
    a.section('W251_foreend_lower',[8,12.07,.14],[1.86,.94,5.18],.20,'frame','foreend','armory_vents')
    a.section('W251_front_slot_rise',[8,12.42,-2.57],[1.83,.58,.94],.17,'frame','foreend','armory_vents',pitch=-28)
    # Broad receiver side survives as one face, convex crown and lower shoulder
    # break the slab at different heights. Breech remains an independent mass.
    a.section('W251_receiver_lower',[8,11.76,6.20],[1.86,1.08,7.05],.22,'frame','receiver','receiver')
    a.section('W251_receiver_bridge',[8,12.84,5.00],[1.87,1.00,3.90],.25,'frame','receiver','receiver')
    a.section('W251_receiver_crown',[8,13.40,4.64],[1.57,.55,3.80],.19,'crown','receiver','crown')
    a.section('W251_receiver_rear',[8,11.45,10.70],[1.66,.38,2.20],.13,'frame','receiver','rear_panel')
    a.section('W251_breech',[8,13.02,7.88],[1.16,1.16,2.05],.23,'red','breech','breech')
    # Long cheek contact with actual rounded section, a dipped leading ramp and
    # a sloped tail into the stock spine. Red bedding stays visible underneath.
    a.section('W251_cheek_middle',[8,13.39,13.38],[1.69,.62,3.35],.23,'rubber','stock','pad')
    a.section('W251_cheek_front_rise',[8,13.25,11.28],[1.63,.56,1.22],.20,'rubber','stock','pad',pitch=-16)
    a.section('W251_cheek_tail',[8,13.30,15.30],[1.62,.54,.84],.19,'rubber','stock','pad',pitch=16)
    # Same grip envelope/axis and exact wrist contact. Filleted cross-section
    # gives genuine front/rear depth instead of a black rectangle on each side.
    for old,new,cut,group in (('Grip_core','W251_grip',.24,'grip'),('Grip_backstrap','W251_backstrap',.09,'grip'),('Stock_buttpad','W251_stock_butt',.18,'stock')):
        spec=contact[old];e=spec['geometry'];c=[(x+y)/2 for x,y in zip(e['from'],e['to'])];sz=[y-x for x,y in zip(e['from'],e['to'])]
        a.round_grip(new,c,sz,cut,spec['material'],group,e['rotation']['x'])
    # Real optic aperture: angled upper shoulders meet a short bridge without
    # filling the native sight opening. Bottom sill and emitter are unchanged.
    for side in (-1,1):
        a.box(f'W251_optic_lower_post_{side}',[8+side*.38,14.49,7.90],[.17,.80,.30],'frame','optic','optic')
        a.box(f'W251_optic_top_shoulder_{side}',[8+side*.32,14.99,7.90],[.17,.38,.30],'crown','optic','optic',(0,0,side*24))
    a.box('W251_optic_top',[8,15.12,7.90],[.50,.18,.30],'crown','optic','optic')
    # Mag still uses the same moving carrier, neck and latch. Bevels follow its
    # tilted cross-section, rather than placing unrotated strips over the core.
    a.round_grip('W251_magazine',[8.00624,8.24,11.77],[.94,2.94,2.45],.17,'olive','magazine',-8,'magazine')
    for s in d['parts']['magazine']:
        if s['geometry']['name'].startswith('W251_magazine'):s['motif']='magazine'
    a.section('W251_magazine_floor',[8.00624,6.72,11.71],[1.05,.27,2.70],.10,'olive','magazine','floorplate','magazine',pitch=-8)
    d['palette']={'frame':[57,63,69],'crown':[75,82,88],'recess':[18,22,27],
        'red':[176,34,29],'red_edge':[201,47,34],'steel':[148,156,163],
        'olive':[68,72,59],'rubber':[28,32,35],'violet':[86,71,128]}
    d['improvements']=[
        '긴 앞 외장·receiver를 넓은 면과 실제 사선 어깨로 재구성하고 빨간 총열의 양옆 빈 공간은 유지했다.',
        '볼받침의 둥근 단면과 낮은 앞 경사·뒤쪽 내려오는 경사를 원본 사진·rip에 맞춰 추가했다.',
        '손 파지 축을 유지한 그립과 기울어진 탄창에 둥근 단면을 넣고 가늠쇠 상단을 사선 어깨로 연결했다.',
        'Black Armory 패널·쌍열 각인·총구 vent·올리브 탄창 채널과 대각 홈을 world 연속 UV에 그렸다.']
    return d
if __name__=='__main__':run('blast_furnace',original,design)
