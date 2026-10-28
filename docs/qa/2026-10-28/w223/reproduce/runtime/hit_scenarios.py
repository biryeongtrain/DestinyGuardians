import json,time,threading
import qa,batch,scenarios
P=batch.P

def run():
    scenarios.equip('austringer')
    batch.fixture([f'guardian class none {P}',f'destiny weapon standalone {P}'],'hit-non-guardian')
    qa.save('oracles/hit-before.json',{'state':qa.client('control/state')})
    for mode in ['hit','protected','miss','kill']:
        cmds=['kill @e[tag=w223_hit_target]', 'time set noon']
        if mode!='miss':
            nbt='{NoAI:1b,Silent:1b,Tags:["w223_hit_target"],Health:'+('1.0f' if mode=='kill' else '100.0f')+(',Invulnerable:1b}' if mode=='protected' else '}')
            cmds.append('summon minecraft:iron_golem 0 65 7 '+nbt)
        cmds += [f'item modify entity {P} weapon.mainhand {{"type":"minecraft:set_custom_data","tag":"{{destiny_weapon_rounds:11,destiny_weapon_reserve:150}}"}}']
        batch.fixture(cmds,'hit-'+mode+'-fixture');time.sleep(.65)
        timeline=[];done=threading.Event()
        def monitor():
            while not done.is_set():
                try:timeline.append({'at':time.time(),'text':qa.command([f'destiny debug weapon-presentation-status {P}'],'WeaponPresentation')})
                except Exception as e:timeline.append({'error':str(e)})
                done.wait(.04)
        thread=threading.Thread(target=monitor);thread.start()
        try:result=qa.client(steps=[{'keys':['use'],'ticks':2,'yaw':0,'pitch':5},{'keys':[],'ticks':24}],label='w223-hit-'+mode,captureFrames=True)
        finally:done.set();thread.join(12)
        qa.save('oracles/hit-'+mode+'-timeline.json',timeline);qa.save('sequences/w223-hit-'+mode+'.json',result)
        assert result.get('returncode')==0,'Cancelled native shot; do not replay'
        after=qa.command(['data get entity @e[tag=w223_hit_target,limit=1] Health',f'destiny debug weapon-presentation-status {P}'],'WeaponPresentation')
        qa.save('oracles/hit-'+mode+'-after.json',{'text':after});batch.capture('w223-hit-'+mode+'-expired')
    batch.fixture(['kill @e[tag=w223_hit_target]'],'hit-owned-target-cleanup')
