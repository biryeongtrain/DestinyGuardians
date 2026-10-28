from pathlib import Path
import json,re,sys
root=Path(sys.argv[1]);ids=['nezarec_s_whisper'];rows=[]
for id in ids:
 row={'weapon':id,'sequences':{}}
 for mode in ['fire','reload','ads']:
  d=json.loads((root/'sequences'/('w223-'+id+'-'+mode+'.json')).read_text())
  assert d['returncode']==0,(id,mode,d)
  data=json.loads(d['stdout']);assert not data.get('error') and not data.get('monitorError'),(id,mode)
  released=data['released']
  assert not released['leaseActive'] and not released['heldKeys'] and not released['pendingSteps'],(id,mode)
  assert data['captured'] and data['captures'],(id,mode,'no pixels')
  row['sequences'][mode]={'captures':len(data['captures']),'released':True,'nativeInput':released.get('nativeInput')}
 state=json.loads((root/'oracles'/('w223-'+id+'-reload-finished.json')).read_text())['text']
 assert 'reloading=false' in state,(id,state)
 matches=re.findall(r'ammo=(\d+)/(\d+)',state);assert matches and int(matches[-1][0])>0,(id,state)
 row['finishedAmmo']=matches[-1]
 hip=json.loads((root/'brackets'/('w223-'+id+'-hip.json')).read_text())['serverBefore']
 after_shot=json.loads((root/'oracles'/('w223-'+id+'-after-shot.json')).read_text())['text']
 before_rounds=int(re.findall(r'ammo=(\d+)/(\d+)',hip)[-1][0])
 after_rounds=int(re.findall(r'ammo=(\d+)/(\d+)',after_shot)[-1][0])
 window=json.loads((root/'oracles'/('w223-'+id+'-fire-window.json')).read_text())
 paid_fire=[json.loads(line.split('[W107 use trace] ',1)[1]) for line in (root/'server.log').read_text(errors='replace').splitlines() if '[W107 use trace] ' in line]
 paid_fire=[e for e in paid_fire if e.get('event')=='runtime.paid' and e.get('weapon')==id and window['startWallMs']<=e['wallMs']<=window['endWallMs']]
 assert paid_fire,(id,'no authoritative paid native fire')
 row['paidNativeFireEvents']=paid_fire
 row['ammoDeltaAtAfterSnapshot']=before_rounds-after_rounds
 timeline=json.loads((root/'oracles'/('w223-'+id+'-reload-timeline.json')).read_text())
 values=[]
 for sample in timeline:
  text=sample.get('text','')
  prefix='weapon_insert_w223_' if id in ['long_arm'] else 'weapon_reload_w222_'
  if 'model=destiny:'+prefix+id not in text:continue
  for payload in re.findall(r'floats=\[([^]]*)\]',text):
   floats=[float(x.strip()) for x in payload.split(',') if x.strip()]
   index=4 if id in ['long_arm'] else 1
   if len(floats)>index and 0<=floats[index]<=(5.002 if index==4 else 1.002):values.append(floats[index])
 assert len(values)>=2,(id,'missing live dense runtime evidence')
 assert all(min(abs(v*60-round(v*60)),abs((v-.001)*60-round((v-.001)*60)))<.001 for v in values),(id,values)
 row['serverDenseProgressSamples']=values
 if id in ['long_arm']:
  assert any(v<1.01 for v in values) and any(1.99<=v<=3.01 for v in values),(id,'missing initial/loop evidence',values)
 rows.append(row)
interrupts=[]
for id in []:
 d=json.loads((root/'sequences'/('w223-'+id+'-interrupt.json')).read_text());assert d['returncode']==0
 data=json.loads(d['stdout']);assert not data.get('error') and not data.get('monitorError')
 released=data['released'];assert not released['leaseActive'] and not released['heldKeys'] and not released['pendingSteps']
 text=json.loads((root/'oracles'/('w223-'+id+'-interrupted.json')).read_text())['text']
 rounds=int(re.findall(r'ammo=(\d+)/(\d+)',text)[-1][0]);assert 'reloading=false' in text
 assert 0<=rounds<5,(id,rounds)
 window=json.loads((root/'oracles'/('w223-'+id+'-interrupt-window.json')).read_text())
 paid=[]
 for line in (root/'server.log').read_text(errors='replace').splitlines():
  if '[W107 use trace] ' not in line:continue
  event=json.loads(line.split('[W107 use trace] ',1)[1])
  if event.get('event')=='runtime.paid' and event.get('weapon')==id and window['startWallMs']<=event['wallMs']<=window['endWallMs']:paid.append(event)
 assert paid,(id,'no authoritative paid interrupt shot')
 interrupts.append({'weapon':id,'released':True,'afterRounds':rounds,'reloading':False,'paidShotEvents':paid})
post=json.loads((root/'postflight.json').read_text());assert not post['leaseActive'] and not post['heldKeys'] and not post['pendingSteps']
hitRows=[]
for mode in ['hit','protected','miss','kill']:
 d=json.loads((root/'sequences'/('w223-hit-'+mode+'.json')).read_text());assert d['returncode']==0
 data=json.loads(d['stdout']);assert not data.get('error') and not data.get('monitorError')
 released=data['released'];assert not released['leaseActive'] and not released['heldKeys'] and not released['pendingSteps']
 timeline=json.loads((root/'oracles'/('hit-'+mode+'-timeline.json')).read_text());texts=[v.get('text','') for v in timeline]
 cues=[text for text in texts if re.search(r'hitHud=\[[^]]*hit_confirmation_w223_',text)]
 if mode in ['hit','kill']:
  assert cues,(mode,'No authoritative live HUD cue')
  expected='gui/hud/'+('kill' if mode=='kill' else 'hit')+'_confirmation_w223'
  assert any(expected in text for text in cues),(mode,'Incorrect cue model')
 else:assert not cues,(mode,'False positive cue')
 after=json.loads((root/'oracles'/('hit-'+mode+'-after.json')).read_text())['text'];assert 'hitHud=[]' in after,(mode,'Cue did not expire')
 rounds=int(re.findall(r'ammo=(\d+)/(\d+)',after)[-1][0]);assert rounds==10,(mode,'Expected one paid shot from11-round fixture',rounds)
 health=re.findall(r'entity data: ([0-9.]+)f',after)
 if mode=='hit':assert health and 0<float(health[-1])<100,(mode,health)
 elif mode=='protected':assert health and float(health[-1])==100,(mode,health)
 else:assert 'No entity was found' in after,(mode,'Unexpected target left')
 hitRows.append({'mode':mode,'liveCueSamples':len(cues),'captures':len(data.get('captures',[])),'expired':True,'onePaidRound':True,'targetHealth':health[-1] if health else None,'after':after})
report={'hitConfirmationCases':hitRows,'sequences':7,'partialInterrupts':interrupts,'rows':rows,'neutralAfter':True,'limits':['Actual framebuffer review is a separate manual step.','Sampled captures do not certify continuous60fps or microphone listening.']}
(root/'native-validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
