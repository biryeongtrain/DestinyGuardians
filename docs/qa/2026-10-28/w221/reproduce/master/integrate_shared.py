from pathlib import Path
import hashlib,json,shutil
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w221';s=Path('/private/tmp/destiny-w221-source')
sel=json.loads((s/'selection.json').read_text());ids=sel['ids'];shells=ids[:3];reloads=ids[3:];rows=[]
assert json.loads((q/'seed.json').read_text())['ready']
for group in sel['groups']:
 p=r/'art/weapons/w221/rigs'/(group+'.json');p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/(group+'.json'),p)
for name in ['source-review.json','source-handling-evidence.json']:shutil.copy2(s/name,q/name)
shutil.copytree(s/'sheets',q/'source-sheets')
def edit(rel,old,new):
 p=r/rel;t=p.read_text();assert t.count(old)==1,(rel,old,t.count(old));before=hashlib.sha256(p.read_bytes()).hexdigest();p.write_text(t.replace(old,new));rows.append({'path':rel,'before':before,'after':hashlib.sha256(p.read_bytes()).hexdigest()})
edit('scripts/first_person_framing_w205.py',"*(ROOT/'art/weapons/w220').glob('*/profile.json')", "*(ROOT/'art/weapons/w220').glob('*/profile.json'), *(ROOT/'art/weapons/w221').glob('*/profile.json')")
edit('scripts/rig_arms_w205.py',' return result,inputs'," for path in sorted((ROOT/'art/weapons/w221/rigs').glob('*.json')):\n  raw=path.read_bytes();d=json.loads(raw);inputs[str(path.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()\n  for weapon in "+repr(tuple(ids))+":\n   if weapon in d['weapons']:result[weapon]=d\n return result,inputs")
edit('scripts/rig_arms_w205.py','RELOAD_ACTIONS = {','RELOAD_ACTIONS = {\n'+''.join(' '+repr(w)+': ('+repr(sel['actions'][w])+',),\n' for w in ids))
old="if weapon in ('dust_rock_blues','first_in_last_out'):"
edit('scripts/rig_arms_w205.py',old,"if weapon in "+repr(tuple(['dust_rock_blues','first_in_last_out']+shells))+':')
old="if id in ('dust_rock_blues','first_in_last_out') and 4 in state:"
edit('scripts/build_first_person_hands_w201.py',old,"if id in "+repr(tuple(['dust_rock_blues','first_in_last_out']+shells))+" and 4 in state:")
java='src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java'
edit(java,'|| e.id().equals("seventh_seraph_officer_revolver")','|| e.id().equals("seventh_seraph_officer_revolver")') if False else None
edit(java,'|| e.id().equals("salvager_s_salvo")).isPresent()', '|| e.id().equals("salvager_s_salvo")'+''.join(' || e.id().equals("'+w+'")' for w in reloads)+').isPresent()')
edit(java,'|| entry.id().equals("deafening_whisper"));','|| entry.id().equals("deafening_whisper") || entry.id().equals("pyroclastic_flow"));')
edit(java,'String namespace = switch (entry.id()) {','String namespace = switch (entry.id()) {\n            case '+', '.join('"'+w+'"' for w in reloads)+' -> "weapon_reload_w221_" + entry.id() + "/";')
edit(java,'            case "seventh_seraph_officer_revolver" -> "weapon_reload_w181_" + entry.id() + "/";\n','')
java='src/main/java/kim/biryeong/destiny/weapon/WeaponInsertPresentation.java'
edit(java,'|| e.id().equals("dust_rock_blues"));','|| e.id().equals("dust_rock_blues") || e.id().equals("ikelos_sg_v1_0_1") || e.id().equals("parcel_of_stardust_fell_to_earth"));')
edit(java,'            case "mindbender_s_ambition_adept" -> Identifier.parse("destiny:weapon_insert_w179_mindbender_s_ambition_adept/mindbender_s_ambition_adept");','            case '+', '.join('"'+w+'"' for w in shells)+' -> Identifier.parse("destiny:weapon_insert_w221_" + entry.id() + "/" + entry.id());')
edit(java,'e.id().equals("first_in_last_out"))).isPresent()', 'e.id().equals("first_in_last_out")'+''.join(' || e.id().equals("'+w+'")' for w in shells)+')).isPresent()')
test='src/test/java/kim/biryeong/destiny/weapon/ReloadRoutingW114Test.java'
edit(test,'EXPECTED = Map.ofEntries(','EXPECTED = Map.ofEntries(\n            Map.entry("pyroclastic_flow", "weapon_reload_w221_pyroclastic_flow/pyroclastic_flow"),')
edit(test,'weapon_reload_w181_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver','weapon_reload_w221_seventh_seraph_officer_revolver/seventh_seraph_officer_revolver')
edit(test,'assertEquals(49, count);','assertEquals(50, count);')
edit(test,'fortyNineCanonicalReloadRoutesIncludeThreeGrenadeLaunchers','fiftyCanonicalReloadRoutesIncludePyroclasticFlow')
test='src/test/java/kim/biryeong/destiny/weapon/InsertRoutingW179Test.java'
edit(test,'fourExactRoutesKeepLegacyLongArmAndFilo','sixExactRoutesKeepLegacyLongArmAndDenseShotguns')
edit(test,'weapon_insert_w179_mindbender_s_ambition_adept/mindbender_s_ambition_adept','weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept')
edit(test,'var routes=Map.of("long_arm"','var routes=Map.of("ikelos_sg_v1_0_1","weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1",\n                "parcel_of_stardust_fell_to_earth","weapon_insert_w221_parcel_of_stardust_fell_to_earth/parcel_of_stardust_fell_to_earth",\n                "long_arm"')
edit('src/test/java/kim/biryeong/destiny/weapon/ReloadPresentationW212Test.java','"salvager_s_salvo");','"salvager_s_salvo",'+','.join('"'+w+'"' for w in reloads)+');')
method='    @Test void threeShotgunsUseDenseInitialLoopReturnBanks()throws Exception {\n        for(String id:List.of("ikelos_sg_v1_0_1","mindbender_s_ambition_adept","parcel_of_stardust_fell_to_earth")) {\n            var entry=WeaponCatalog.find(id).orElseThrow();\n            assertTrue(WeaponProfile.forEntry(entry).shellReload());\n            String key=WeaponInsertPresentation.model(entry).getPath();\n            ReloadPresentationW208Test.assertDenseDispatch(JsonParser.parseString(Files.readString(A.resolve("items/"+key+".json"))),4,183);\n            try(var files=Files.list(A.resolve("models/"+key.split("/")[0]))) {\n                for(var path:files.toList()) assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(path))),path.toString());\n            }\n        }\n    }\n'
edit('src/test/java/kim/biryeong/destiny/weapon/ReloadPresentationW212Test.java','    @Test void liveRoutesHaveAll61SamplesAndNativeArms()',method+'    @Test void liveRoutesHaveAll61SamplesAndNativeArms()')
routes=[('insert' if i<3 else 'reload')+'_w221_'+w+'/'+w for i,w in enumerate(ids)]
edit('src/test/java/kim/biryeong/destiny/weapon/FirstPersonHandsW201Test.java','for(String route:List.of(','for(String route:List.of('+','.join('"weapon_'+v+'"' for v in routes)+',')
edit('scripts/qa/test_source_bindings_w212.py',"'salvager_s_salvo'):","'salvager_s_salvo',"+','.join(repr(w) for w in ids)+'):' )
(q/'integration-shared.json').write_text(json.dumps(rows,indent=2)+'\n');print({'sharedEdits':len(rows),'freshRigGroups':3,'reloadRoutes':50,'insertRoutes':6})
