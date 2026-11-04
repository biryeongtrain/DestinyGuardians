#!/usr/bin/env python3
"""Owned W32 visual fixtures, NOT native input tests; see the w32 QA README.

--control-relay accepts a session-owned 0600 UNIX observation proxy, not a token.
Only WeaponW30QA and tagged w32_side mannequins are changed. No production use.
"""
import argparse,json,pathlib,socket
from capture_weapons_w30 import Capture,ROOT,PLAYER

class GripCapture(Capture):
    def http(self,path):
        if not self.args.control_relay or path in ('state','screenshot'):
            return super().http(path)
        with socket.socket(socket.AF_UNIX) as s:
            s.settimeout(25);s.connect(str(self.args.control_relay))
            s.sendall(json.dumps(dict(route=path)).encode()+b'\n');data=b''
            while not data.endswith(b'\n'):
                chunk=s.recv(65536)
                if not chunk:raise ConnectionError('Observation proxy closed')
                data+=chunk
        response=json.loads(data)
        if response.get('error'):raise RuntimeError('Observation mutation refused: '+str(response))
        return data
    def mannequin(self,row,two):
        grip='TWO_HAND' if two else 'NATIVE'
        return 'item replace entity @e[type=minecraft:mannequin,tag=w32_side,limit=1] weapon.mainhand with destiny:weapon_preview[minecraft:item_model="destiny:weapon/'+row['id']+'",minecraft:custom_data={destiny_weapon_preview:"'+row['id']+'",destiny_weapon_grip:"'+grip+'"},minecraft:custom_model_data={strings:["hip"]}]'
    def run(self):
        try:self._run()
        finally:
            self.command(['kill @e[type=minecraft:mannequin,tag=w32_side]',
                          f'item replace entity {PLAYER} weapon.mainhand with minecraft:air',f'title {PLAYER} clear'])
            self.http('perspective?mode=first');self.http('look?yaw=180&pitch=0')
    def _run(self):
        rows=json.loads((ROOT/'art/weapons/w30/catalog.json').read_text())
        self.http('perspective?mode=first');self.http('look?yaw=180&pitch=0')
        self.command([f'item replace entity {PLAYER} weapon.mainhand with minecraft:air',
                      'kill @e[type=minecraft:mannequin,tag=w32_side]',
                      'summon minecraft:mannequin 2000.5 81 2003.5 {Tags:["w32_side"],Rotation:[65f,0f],NoGravity:1b,Invulnerable:1b}'],expect='Summoned new Mannequin')
        for row in rows:
            two=row['family'] not in ('hand_cannon','sidearm','bow','sword','glaive')
            self.command([self.mannequin(row,two),self.caption(row,'observer'),
                          'data get entity @e[type=minecraft:mannequin,tag=w32_side,limit=1] equipment'],expect='destiny:weapon/'+row['id'])
            self.capture(row,'observer')
        for row in [r for r in rows if r['family'] in ('hand_cannon','sidearm')]:
            self.command([self.mannequin(row,True),self.caption(row,'optional_two_hand'),
                          'data get entity @e[type=minecraft:mannequin,tag=w32_side,limit=1] equipment'],expect='destiny:weapon/'+row['id'])
            self.capture(row,'optional_two_hand')
        self.command(['kill @e[type=minecraft:mannequin,tag=w32_side]'])
        representatives=[]
        for family in dict.fromkeys(r['family'] for r in rows):
            group=[r for r in rows if r['family']==family]
            representatives.append(next((r for r in group if r['frame']=='adaptive'),group[0]))
        representatives += [r for r in rows if r['family']=='sniper_rifle' and r not in representatives]
        for context in ('hip','ads','inspect','third_front'):
            self.http('perspective?mode='+('third_front' if context=='third_front' else 'first'))
            for row in rows if context in ('hip','third_front') else representatives:
                pose='hip' if context=='third_front' else context
                self.command([f"destiny weapon equip {row['id']} {PLAYER}",f'destiny weapon pose {pose} {PLAYER}',self.caption(row,context),f'data get entity {PLAYER} SelectedItem'],expect='destiny:weapon/'+row['id'])
                self.capture(row,context)
        row=next(r for r in rows if r['id']=='ammit_ar2')
        for grip in ('native','two_hand'):
            for context in ('hip','ads','inspect','third_front'):
                self.http('perspective?mode='+('third_front' if context=='third_front' else 'first'))
                pose='hip' if context=='third_front' else context
                self.command([f'destiny weapon equip ammit_ar2 {PLAYER}',f'destiny weapon grip {grip} {PLAYER}',f'destiny weapon pose {pose} {PLAYER}',self.caption(row,'compare_'+grip+'_'+context),f'data get entity {PLAYER} SelectedItem'],expect='destiny:weapon/ammit_ar2')
                self.capture(row,'compare_'+grip+'_'+context)

def main():
    p=argparse.ArgumentParser();p.add_argument('--socket',type=pathlib.Path,required=True);p.add_argument('--server-log',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True)
    p.add_argument('--control-relay',type=pathlib.Path);p.add_argument('--label',default='W32')
    GripCapture(p.parse_args()).run()
if __name__=='__main__':main()
