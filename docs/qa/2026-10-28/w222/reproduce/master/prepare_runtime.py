from pathlib import Path
import json, shutil
s=Path(__file__).parent
oldids=['ikelos_sg_v1_0_1','mindbender_s_ambition_adept','parcel_of_stardust_fell_to_earth','pyroclastic_flow','seventh_seraph_officer_revolver']
ids=['biting_winds','whispering_slab','long_arm','nezarec_s_whisper']
for phase in ('pass1','pass2'):
    root=Path('/private/tmp/destiny-w222-'+phase+'-native');root.mkdir()
    old=Path('/private/tmp/destiny-w221-'+phase+'-native')
    for p in old.iterdir():
        if p.suffix not in ('.py','.gradle'):continue
        text=p.read_text().replace('w221','w222').replace('W221','W222')
        if p.name=='run_batch.py':
            text=text.replace(repr(oldids),repr(ids)).replace(repr(oldids[:3]),repr(['long_arm']))
        if p.name=='contact_sheets.py':text=text.replace(repr(oldids),repr(ids))
        if p.name=='scenarios.py':
            text=text.replace("{'keys':['use'],'ticks':5,'yaw':0,'pitch':0}","{'keys':['use'],'ticks':28 if id in ('biting_winds','whispering_slab') else 5,'yaw':0,'pitch':0}")
            text=text.replace("'first_in_last_out','dust_rock_blues'", "'long_arm','first_in_last_out','dust_rock_blues'")
            text=text.replace("{'keys':[],'ticks':30},{'keys':['use'],'ticks':2}","{'keys':[],'ticks':35},{'keys':['use'],'ticks':2}")
        (root/p.name).write_text(text)
    run=root/'client-run';run.mkdir()
    for name in ('options.txt',):
        p=old/'client-run'/name
        if p.exists():shutil.copy2(p,run/name)
server=Path('/private/tmp/destiny-w222-server');server.mkdir()
old=Path('/private/tmp/destiny-w221-server')
props=(old/'server.properties').read_text();props='\n'.join(x for x in props.splitlines() if not x.startswith('management-server-secret='))+'\n'
(server/'server.properties').write_text(props)
for name in ('eula.txt','ops.json','whitelist.json'):
    shutil.copy2(old/name,server/name)
for name in ('run_native_pass.py','post_reload_sheet.py','seal_pass2.py','build.py'):
    text=(Path('/private/tmp/destiny-w221-source')/name).read_text().replace('w221','w222').replace('W221','W222')
    (s/name).write_text(text)
print({'runtimesPrepared':2,'freshServer':str(server),'clientAccounts':'isolated WeaponW129QA','tokens':'generated only at launch, never saved'})
