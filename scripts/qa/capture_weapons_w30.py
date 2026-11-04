#!/usr/bin/env python3
"""W30 visual fixture capture, NOT native gameplay/input verification.

Requires an already-owned local QA server console relay (Unix socket, 0600), an
observation-only Vision 26.3 client on 8102, and the isolated WeaponW30QA actor.
No GUI automation, no injection, no production endpoints, no token persistence.
GUI means native GUI ItemDisplayContext on a world item_display, not an inventory
screen. Stages only its tagged entity and restores the actor's hand/perspective.
"""
import argparse,hashlib,json,pathlib,socket,time,urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[2]
PLAYER='WeaponW30QA'
class Capture:
    def __init__(self,args):
        self.args=args;self.records=[];args.out.mkdir(parents=True,exist_ok=True)
    def http(self,path):
        return urllib.request.urlopen('http://127.0.0.1:8102/'+path,timeout=20).read()
    def command(self,commands,expect=None):
        offset=self.args.server_log.stat().st_size
        with socket.socket(socket.AF_UNIX) as s:
            s.settimeout(10);s.connect(str(self.args.socket));s.sendall(('\n'.join(commands)+'\n').encode());s.recv(100)
        deadline=time.monotonic()+8
        while expect and time.monotonic()<deadline:
            with self.args.server_log.open() as f:f.seek(offset);data=f.read()
            if expect in data:return
            time.sleep(.05)
        if expect:raise RuntimeError('Fixture not acknowledged: '+expect)
    def capture(self,row,context):
        time.sleep(.3) # server ACK is NOT client-render completion; allow native update/equip settling
        before=json.loads(self.http('state'));assert before.get('inWorld') and before.get('screen') is None
        raw=self.http('screenshot');after=json.loads(self.http('state'))
        assert raw.startswith(b'\x89PNG'), 'Not a framebuffer'
        file=f"{context}/{row['id']}.png";path=self.args.out/file;path.parent.mkdir(exist_ok=True);path.write_bytes(raw)
        self.records.append(dict(id=row['id'],family=row['family'],frame=row['frame'],context=context,file=file,
                                 sha256=hashlib.sha256(raw).hexdigest(),before=before,after=after,captured_at=time.time()))
        (self.args.out/'captures.json').write_text(json.dumps(dict(mode='server fixture + native framebuffer, not gameplay input',records=self.records),indent=2)+'\n')
        print(context,row['id'],flush=True)
    def caption(self,row,context):
        label=dict(text=f"{self.args.label} {context} | {row['family']} / {row['frame']} | {row['name']}",color='white')
        return f'title {PLAYER} actionbar '+json.dumps(label)
    def run(self):
        try:
            self._run()
        finally:
            self.command(['kill @e[type=minecraft:item_display,tag=w30_gallery]',
                          f'item replace entity {PLAYER} weapon.mainhand with minecraft:air',f'title {PLAYER} clear'])
            self.http('perspective?mode=first')
    def _run(self):
        rows=json.loads((ROOT/'art/weapons/w30/catalog.json').read_text())
        self.http('perspective?mode=first');self.http('look?yaw=180&pitch=0')
        self.command([f'item replace entity {PLAYER} weapon.mainhand with minecraft:air',
                      'kill @e[type=minecraft:item_display,tag=w30_gallery]',
                      'summon minecraft:item_display 2000.5 82.62 2002.5 {Tags:["w30_gallery"],item_display:"gui",brightness:{block:15,sky:15},transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],scale:[2.5f,2.5f,2.5f]},item:{id:"minecraft:stick",count:1}}'],expect='Summoned new Item Display')
        for row in rows:
            self.command(['data merge entity @e[type=minecraft:item_display,tag=w30_gallery,limit=1] {item:{id:"minecraft:stick",count:1,components:{"minecraft:item_model":"destiny:weapon/'+row['id']+'"}}}',
                          self.caption(row,'gui'),
                          'data get entity @e[type=minecraft:item_display,tag=w30_gallery,limit=1] item'],expect='destiny:weapon/'+row['id'])
            self.capture(row,'gui')
        self.command(['kill @e[type=minecraft:item_display,tag=w30_gallery]'])
        for row in rows:
            self.command([f"destiny weapon equip {row['id']} {PLAYER}",self.caption(row,'hip'),f'data get entity {PLAYER} SelectedItem'],expect='destiny:weapon/'+row['id'])
            self.capture(row,'hip')
        representatives=[]
        for family in dict.fromkeys(r['family'] for r in rows):
            group=[r for r in rows if r['family']==family]
            representatives.append(next((r for r in group if r['frame']=='adaptive'),group[0]))
        representatives += [r for r in rows if r['family']=='sniper_rifle' and r not in representatives]
        for context in ('ads','inspect','third_front'):
            self.http('perspective?mode='+('third_front' if context=='third_front' else 'first'))
            for row in rows if context=='third_front' else representatives:
                pose='hip' if context=='third_front' else context
                self.command([f"destiny weapon equip {row['id']} {PLAYER}",f'destiny weapon pose {pose} {PLAYER}',self.caption(row,context),f'data get entity {PLAYER} SelectedItem'],expect='destiny:weapon/'+row['id'])
                self.capture(row,context)
        self.command([f'item replace entity {PLAYER} weapon.mainhand with minecraft:air',f'title {PLAYER} clear'])
        self.http('perspective?mode=first')

def main():
    p=argparse.ArgumentParser();p.add_argument('--socket',type=pathlib.Path,required=True);p.add_argument('--server-log',type=pathlib.Path,required=True);p.add_argument('--out',type=pathlib.Path,required=True)
    p.add_argument('--label',default='W30')
    args=p.parse_args();Capture(args).run()
if __name__=='__main__':main()
