import qa,batch,json,time,sys
P=batch.P

def equip(id,grip=None):
    qa.client('perspective?mode=first')
    cmds=[f'guardian class none {P}',f'clear {P}',f'guardian class hunter {P}',f'guardian subclass solar {P}',f'guardian reset {P}',f'destiny weapon standalone {P}',f'tp {P} 0 66 0 0 0',f'destiny weapon load {id} {P}']
    if grip:cmds.append(f'execute as {P} run destiny weapon grip {grip}')
    batch.fixture(cmds,'equip-'+id+('-'+grip if grip else ''))
    time.sleep(1.5)

def shot_reload(id,label):
    equip(id)
    batch.capture(label+'-hip')
    # Native use pays shots. Empty-use reload uses the existing use path, not a synthetic Q key.
    fire_start=int(time.time()*1000)
    result=qa.client(steps=[{'keys':['use'],'ticks':28 if id in ('biting_winds','whispering_slab') else 5,'yaw':0,'pitch':0},{'keys':[],'ticks':10}],label=label+'-fire',captureFrames=True)
    qa.save('sequences/'+label+'-fire.json',result)
    if result.get('returncode')!=0:raise RuntimeError('Input cancelled; no blind replay')
    qa.save('oracles/'+label+'-fire-window.json',dict(startWallMs=fire_start,endWallMs=int(time.time()*1000)))
    batch.status(label+'-after-shot')
    batch.fixture([f'item modify entity {P} weapon.mainhand {{"type":"minecraft:set_custom_data","tag":"{{destiny_weapon_rounds:0,destiny_weapon_reserve:150}}"}}'],label+'-empty-magazine-fixture')
    time.sleep(1.5)
    import threading
    done=threading.Event();samples=[]
    def monitor():
        while not done.is_set():
            try:samples.append({'at':time.time(),'text':qa.command([f'destiny debug weapon-presentation-status {P}'],'WeaponPresentation')})
            except Exception as e:samples.append({'error':str(e)})
            done.wait(.15)
    thread=threading.Thread(target=monitor);thread.start()
    try:
        result=qa.client(steps=[{'keys':['use'],'ticks':2,'yaw':0,'pitch':0},{'keys':[],'ticks':90}]+([{'keys':[],'ticks':90}] if id in ('long_arm','first_in_last_out','dust_rock_blues','hammerhead','retrofit_escapade','ikelos_smg_v1_0_1','ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth') else []),label=label+'-reload',captureFrames=True)
    finally:
        done.set();thread.join(12);qa.save('oracles/'+label+'-reload-timeline.json',samples)
    qa.save('sequences/'+label+'-reload.json',result)
    if result.get('returncode')!=0:raise RuntimeError('Input cancelled; no blind replay')
    batch.capture(label+'-after-reload')
    batch.status(label+'-reload-finished')

def aim(id,label):
    equip(id)
    result=qa.client(steps=[{'keys':['sneak'],'ticks':32,'yaw':0,'pitch':0},{'keys':[],'ticks':10}],label=label+'-ads',captureFrames=True)
    qa.save('sequences/'+label+'-ads.json',result)
    if result.get('returncode')!=0:raise RuntimeError('Input cancelled; no blind replay')

if __name__=='__main__':
    mode,id,label=sys.argv[1:4]
    if mode=='fire':shot_reload(id,label)
    elif mode=='aim':aim(id,label)
    elif mode=='hip':equip(id);batch.capture(label)

def interrupt(id,label):
    equip(id)
    batch.fixture([f'item modify entity {P} weapon.mainhand {{"type":"minecraft:set_custom_data","tag":"{{destiny_weapon_rounds:0,destiny_weapon_reserve:150}}"}}'],label+'-interrupt-fixture')
    time.sleep(1)
    start_ms=int(time.time()*1000)
    result=qa.client(steps=[{'keys':['use'],'ticks':2,'yaw':0,'pitch':0},{'keys':[],'ticks':35},{'keys':['use'],'ticks':2},{'keys':[],'ticks':10}],label=label+'-interrupt',captureFrames=True)
    qa.save('oracles/'+label+'-interrupt-window.json',dict(startWallMs=start_ms,endWallMs=int(time.time()*1000)))
    qa.save('sequences/'+label+'-interrupt.json',result)
    if result.get('returncode')!=0:raise RuntimeError('Input cancelled; no blind replay')
    batch.status(label+'-interrupted')
