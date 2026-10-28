import qa,batch,scenarios,json
qa.save('preflight.json',qa.client('control/state'))
batch.fixture(['difficulty peaceful','time set noon','gamerule minecraft:do_daylight_cycle false'],'safety')
for id in ['ammit_ar2','ace_of_spades']:
 print('START '+id,flush=True)
 scenarios.shot_reload(id,'w225-'+id)
 scenarios.aim(id,'w225-'+id)
 print('DONE '+id,flush=True)
qa.save('postflight.json',qa.client('control/state'))
