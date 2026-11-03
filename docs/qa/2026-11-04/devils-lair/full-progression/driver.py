import time,urllib.request,json,re,subprocess
from pathlib import Path
r=Path('/tmp/destiny-devils-qa-20261103');o=Path('/tmp/devils-fullrun4');o.mkdir(exist_ok=True)
tok=(r/'.vision-token').read_text().strip()
def shot(name):
    try:(o/(name+'.png')).write_bytes(urllib.request.urlopen('http://127.0.0.1:8102/screenshot',timeout=15).read())
    except Exception as e:print('shot fail',name,e,flush=True)
kinds=['dreg','vandal','shank','marauder','captain','thrall','acolyte','knight','wizard','servitor','brig','walker','walker_part','sepiks']
exits={'RY_CLEAR':'287.5 76 331.5','RF_CLEAR':'825.5 76 324.5','BL_CLEAR':'1319.5 77 367.5'}
def cmd(name,lines):(r/'commands'/(name+'.txt')).write_text('\n'.join(lines)+'\n')
n=0
def q(lines):
    global n;n+=1;cmd(f'full-{n:04d}',lines)
q(['effect give DevilsQA minecraft:resistance 3000 4 true','effect give DevilsQA minecraft:saturation 3000 1 true','destiny devils start DevilsQA'])
base=len((r/'server.log').read_text(errors='replace'));t0=time.monotonic();seen=[];last=None;device_done=False;moved=set();phase_t=t0
while time.monotonic()-t0<2700:
    time.sleep(3)
    log=(r/'server.log').read_text(errors='replace')[base:]
    if '참가 중이 아닙니다' in log or 'Checkpoint reset' in log and False:print('NOT PARTICIPATING');break
    ph=re.findall(r'RUNNING / ([A-Z0-9_]+) / ([0-9]+/[0-9]+)',log)
    phase=ph[-1][0] if ph else None
    if 'COMPLETE' in phase if phase else False:
        pass
    if phase!=last:
        el=round(time.monotonic()-t0,1);seen.append({'phase':phase,'t':el,'count':ph[-1][1] if ph else None});print(el,phase,flush=True)
        last=phase;phase_t=time.monotonic();time.sleep(1.5);shot(f'{len(seen):02d}-{phase}')
    lines=['execute as DevilsQA run destiny devils status','effect give DevilsQA minecraft:instant_health 1 3 true']
    if phase and phase not in ('BRIEFING','SP_INTRO','RF_HACK') and not phase.endswith('_CLEAR'):
        lines+=['execute at DevilsQA as @e[type=destiny:devils_'+k+',distance=..300] run damage @s 400 minecraft:player_attack by DevilsQA' for k in kinds]
    if phase in exits and phase not in moved and time.monotonic()-phase_t>3:
        moved.add(phase);lines.append('execute as DevilsQA at @s run tp @s '+exits[phase])
    if phase=='RF_DEVICE' and time.monotonic()-phase_t>4:
        lines.append('execute as DevilsQA at @s run tp @s 811.5 77 302.5')
        q(lines);time.sleep(2)
        out=subprocess.run(['node','/tmp/destiny-devils-qa-20261103/native-sequence.mjs',json.dumps([{"keys":["sneak"],"ticks":60},{"keys":[],"ticks":5}]),str(o/f'device-{n}.json')],capture_output=True,text=True,timeout=40)
        print('device',out.stdout.strip(),out.stderr.strip()[-300:],flush=True);continue
    q(lines)
    if phase in ('COMPLETE',):
        time.sleep(8);shot('final-complete');break
    if 'Session closed' in log or 'CLOSED' == phase:break
(o/'phases.json').write_text(json.dumps(seen,indent=1))
(o/'server.log').write_text((r/'server.log').read_text(errors='replace'))
print('done',json.dumps(seen),flush=True)
