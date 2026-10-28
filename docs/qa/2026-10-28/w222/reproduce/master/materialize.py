from pathlib import Path
import sys,json,hashlib,importlib,shutil
sys.dont_write_bytecode=True
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians')
q=repo/'docs/qa/2026-10-28/w222';sys.path.insert(0,str(repo/'scripts'))
ids=['biting_winds', 'whispering_slab', 'long_arm', 'nezarec_s_whisper'];rows=[]
for id in ids:
 mode='insert' if id=='long_arm' else 'reload'
 module=importlib.import_module('generate_'+mode+'_w222_'+id)
 outputs=module.generate()
 for p,b in outputs.items():
  assert p.is_absolute() and p.is_relative_to(repo)
  assert p.is_relative_to(repo/'src/main/resources/assets/destiny/models'/('weapon_'+mode+'_w222_'+id)) or p==repo/'src/main/resources/assets/destiny/items'/('weapon_'+mode+'_w222_'+id)/(id+'.json') or p==repo/'art/weapons/w222'/id/'manifest.json',p
  p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 rows.append({'weapon':id,'outputs':len(outputs),'files':{str(p.relative_to(repo)):hashlib.sha256(b).hexdigest() for p,b in outputs.items()}})
(q/('generated-'+(sys.argv[1] if len(sys.argv)>1 else 'pass1')+'.json')).write_text(json.dumps(rows,indent=2)+'\n')
print({r['weapon']:r['outputs'] for r in rows})
