import qa,batch,scenarios,json,time,re
P=batch.P
qa.save('preflight.json',qa.client('control/state'))
for outgoing,incoming,label in [('austringer','beloved','w225-w91'),('ammit_ar2','the_recluse','w225-w113'),('ace_of_spades','ammit_ar2','w225-generic')]:
 print('START '+label,flush=True)
 scenarios.equip(outgoing)
 batch.fixture([f'item replace entity {P} hotbar.6 from entity {P} weapon.mainhand',f'item replace entity {P} weapon.mainhand with minecraft:air',f'destiny weapon load {incoming} {P}',f'item replace entity {P} hotbar.7 from entity {P} weapon.mainhand',f'item replace entity {P} weapon.mainhand from entity {P} hotbar.6'],label+'-setup')
 time.sleep(1.5)
 before=batch.status(label+'-before');assert 'weapon='+outgoing+' ' in before,before
 for direction,slot in [('forward',7),('return',6)]:
  # Authorized server fixture replaces actual inventory stack; not a hotbar key or native input claim.
  qa.command([f'item replace entity {P} weapon.mainhand from entity {P} hotbar.{slot}'])
  samples=[]
  for i in range(18):
   text=batch.status(label+'-'+direction+'-'+str(i).zfill(2));capture=qa.capture(label+'-'+direction+'-'+str(i).zfill(2));samples.append({'at':time.time(),'text':text,'frame':capture})
   time.sleep(.03)
  qa.save('oracles/'+label+'-'+direction+'-timeline.json',samples)
  final=batch.status(label+'-'+direction+'-final');expected=incoming if slot==7 else outgoing;assert 'weapon='+expected+' ' in final,final
 print('DONE '+label,flush=True)
qa.save('postflight.json',qa.client('control/state'))
