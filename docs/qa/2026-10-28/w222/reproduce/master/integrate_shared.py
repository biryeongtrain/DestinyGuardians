from pathlib import Path
import hashlib,json
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w222'
assert json.loads((q/'seed.json').read_text())['ready']
sel=json.loads((q/'selection.json').read_text());ids=sel['ids'];whole=[x for x in ids if x!='long_arm'];rows=[]
def edit(rel,old,new):
 p=r/rel;s=p.read_text();assert s.count(old)==1,(rel,old,s.count(old));before=hashlib.sha256(p.read_bytes()).hexdigest();p.write_text(s.replace(old,new));rows.append({'path':rel,'before':before,'after':hashlib.sha256(p.read_bytes()).hexdigest()})
edit('scripts/first_person_framing_w205.py',"*(ROOT/'art/weapons/w221').glob('*/profile.json')","*(ROOT/'art/weapons/w221').glob('*/profile.json'), *(ROOT/'art/weapons/w222').glob('*/profile.json')")
edit('scripts/rig_arms_w205.py',' return result,inputs'," for path in sorted((ROOT/'art/weapons/w222/rigs').glob('*.json')):\n  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()\n  for weapon in "+repr(tuple(ids))+":\n   if weapon in d['weapons']:result[weapon]=d\n return result,inputs")
edit('scripts/rig_arms_w205.py','RELOAD_ACTIONS = {','RELOAD_ACTIONS = {\n'+''.join(' '+repr(w)+': ('+repr(sel['actions'][w])+',),\n' for w in ids))
old="('dust_rock_blues', 'first_in_last_out', 'ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth')"
new=old[:-1]+", 'long_arm')"
edit('scripts/rig_arms_w205.py','if weapon in '+old+':','if weapon in '+new+':')
edit('scripts/build_first_person_hands_w201.py','if id in '+old+' and 4 in state:','if id in '+new+' and 4 in state:')
# A full-chain replay must retain mesh-specific bow riser and string anchors.
# Without this, source_palm_translations overwrites W50's real draw displacement.
edit('scripts/build_first_person_hands_w201.py',"        if config['family']=='bow':\n", "        bow_draw_displacement=0.0\n        if config['family']=='bow':\n")
edit('scripts/build_first_person_hands_w201.py',"                contact['position'][2]+={'biting_winds':4.8,'whispering_slab':3.4}[id]*frame/20", "                bow_draw_displacement={'biting_winds':4.8,'whispering_slab':3.4}[id]*frame/20\n                contact['position'][2]+=bow_draw_displacement")
edit('scripts/build_first_person_hands_w201.py',"            palms=rig_arms.source_palm_translations(rigs[id],state,progress,config,body_display,\n                {side:framing.contact(config,side) for side in ('right','left')},xyz,vec)","            mesh_contacts={side:framing.contact(config,side) for side in ('right','left')}\n            if config['family']=='bow':\n                mesh_contacts['left']['position'][1]-=config['framing'].get('supportHipLower',0)*amount\n                mesh_contacts['right']['position'][2]+=bow_draw_displacement\n            palms=rig_arms.source_palm_translations(rigs[id],state,progress,config,body_display,mesh_contacts,xyz,vec)")
java='src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java'
edit(java,'|| e.id().equals("seventh_seraph_officer_revolver")).isPresent()', '|| e.id().equals("seventh_seraph_officer_revolver")'+''.join(' || e.id().equals("'+w+'")' for w in whole)+').isPresent()')
edit(java,'|| entry.id().equals("pyroclastic_flow"));','|| entry.id().equals("pyroclastic_flow")'+''.join(' || entry.id().equals("'+w+'")' for w in whole)+');')
edit(java,'String namespace = switch (entry.id()) {','String namespace = switch (entry.id()) {\n            case '+', '.join('"'+w+'"' for w in whole)+' -> "weapon_reload_w222_" + entry.id() + "/";')
java='src/main/java/kim/biryeong/destiny/weapon/WeaponInsertPresentation.java'
edit(java,'destiny:weapon_insert_w71/long_arm','destiny:weapon_insert_w222_long_arm/long_arm')
edit(java,'e.id().equals("parcel_of_stardust_fell_to_earth"))).isPresent()', 'e.id().equals("parcel_of_stardust_fell_to_earth") || e.id().equals("long_arm"))).isPresent()')
test='src/test/java/kim/biryeong/destiny/weapon/ReloadRoutingW114Test.java'
edit(test,'EXPECTED = Map.ofEntries(','EXPECTED = Map.ofEntries(\n'+''.join('            Map.entry("'+w+'", "weapon_reload_w222_'+w+'/'+w+'"),\n' for w in whole))
edit(test,'assertEquals(50, count);','assertEquals(53, count);')
edit(test,'fiftyCanonicalReloadRoutesIncludePyroclasticFlow','fiftyThreeRoutesIncludeBowNockingAndGlaive')
edit('src/test/java/kim/biryeong/destiny/weapon/InsertRoutingW179Test.java','weapon_insert_w71/long_arm','weapon_insert_w222_long_arm/long_arm')
edit('src/test/java/kim/biryeong/destiny/weapon/InsertRoutingW179Test.java','sixExactRoutesKeepLegacyLongArmAndDenseShotguns','sixExactRoutesIncludeDenseLongArmAndShotguns')
edit('src/test/java/kim/biryeong/destiny/weapon/ReloadPresentationW212Test.java','"pyroclastic_flow","seventh_seraph_officer_revolver");','"pyroclastic_flow","seventh_seraph_officer_revolver",'+','.join('"'+w+'"' for w in whole)+');')
routes=[('insert' if w=='long_arm' else 'reload')+'_w222_'+w+'/'+w for w in ids]
edit('src/test/java/kim/biryeong/destiny/weapon/FirstPersonHandsW201Test.java','for(String route:List.of(','for(String route:List.of('+','.join('"weapon_'+v+'"' for v in routes)+',')
edit('scripts/qa/test_source_bindings_w212.py',"'pyroclastic_flow','seventh_seraph_officer_revolver'):","'pyroclastic_flow','seventh_seraph_officer_revolver',"+','.join(repr(w) for w in ids)+'):')
edit('scripts/qa/test_source_bindings_w212.py',"shell=weapon in ('ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth')","shell=weapon in ('ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth','long_arm')")
(q/'integration-shared.json').write_text(json.dumps(rows,indent=2)+'\n');print({'sharedEdits':len(rows),'reloadRoutes':53,'insertRoutes':6})
