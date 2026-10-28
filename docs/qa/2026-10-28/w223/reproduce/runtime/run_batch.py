import qa,batch,scenarios,json
ids=['nezarec_s_whisper']
s=qa.client('control/state');qa.save('preflight.json',s)
assert s['eligible'] and not s['leaseActive'] and not s['heldKeys'] and not s['pendingSteps']
batch.fixture(['difficulty peaceful','time set noon','gamerule minecraft:do_daylight_cycle false','fill -24 64 -24 24 64 24 minecraft:stone'],'safety')
for id in ids:
 print('START '+id,flush=True)
 scenarios.shot_reload(id,'w223-'+id)
 if id in ['long_arm']:scenarios.interrupt(id,'w223-'+id)
 scenarios.aim(id,'w223-'+id)
 print('DONE '+id,flush=True)
import hit_scenarios
hit_scenarios.run()
qa.save('postflight.json',qa.client('control/state'))
