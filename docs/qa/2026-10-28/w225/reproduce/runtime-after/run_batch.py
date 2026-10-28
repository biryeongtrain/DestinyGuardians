"""Historical run: final3 offhand switch attempts were INVALIDATED; see switch-input-correction.json. Use runtime-switch-fixture for rendered swap validation."""
import qa,batch,scenarios,json,time,threading
P=batch.P
qa.save('preflight.json',qa.client('control/state'))
batch.fixture(['difficulty peaceful','time set noon','gamerule minecraft:do_daylight_cycle false'],'safety')
for id in ['ammit_ar2','ace_of_spades','dust_rock_blues']:
 print('START '+id,flush=True)
 scenarios.shot_reload(id,'w225-'+id)
 scenarios.aim(id,'w225-'+id)
 print('DONE '+id,flush=True)
def switch(outgoing,incoming,label):
 scenarios.equip(incoming)
 batch.fixture([f'item replace entity {P} weapon.offhand from entity {P} weapon.mainhand',f'destiny weapon load {outgoing} {P}'],label+'-setup')
 time.sleep(1.5)
 batch.capture(label+'-before')
 done=threading.Event();samples=[]
 def monitor():
  while not done.is_set():
   try:samples.append({'at':time.time(),'text':qa.command([f'destiny debug weapon-presentation-status {P}'],'WeaponPresentation')})
   except Exception as e:samples.append({'error':type(e).__name__})
   done.wait(.07)
 thread=threading.Thread(target=monitor);thread.start()
 try:
  result=qa.client(steps=[{'keys':['swap_offhand'],'ticks':1,'yaw':0,'pitch':0},{'keys':[],'ticks':35},{'keys':['swap_offhand'],'ticks':1},{'keys':[],'ticks':35}],label=label,captureFrames=True)
 finally:
  done.set();thread.join(12);qa.save('oracles/'+label+'-timeline.json',samples)
 qa.save('sequences/'+label+'.json',result)
 if result.get('returncode')!=0:raise RuntimeError('Native switch cancelled; no replay')
 batch.capture(label+'-after')
 # This is native offhand swap, not native hotbar-key input.
 qa.save('oracles/'+label+'-input-kind.json',{'kind':'native swap_offhand; server fixtures only place starting weapons','outgoing':outgoing,'incoming':incoming})
for a,b,label in [('austringer','beloved','w225-w91-switch'),('ammit_ar2','the_recluse','w225-w113-switch'),('ace_of_spades','ammit_ar2','w225-generic-switch')]:
 print('START '+label,flush=True);switch(a,b,label);print('DONE '+label,flush=True)
qa.save('postflight.json',qa.client('control/state'))
