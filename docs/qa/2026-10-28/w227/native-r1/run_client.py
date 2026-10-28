import json,os,pathlib,secrets,socket,subprocess,urllib.request,signal,sys
root=pathlib.Path("/private/tmp/destiny-w227-native").resolve(); path=root/"client-control.sock"
if path.exists():raise SystemExit("Existing relay: inspect first")
env=dict(os.environ,JAVA_HOME="/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home",VISION_CONTROL_TOKEN=secrets.token_urlsafe(48),VISION_PORT="8102")
project=pathlib.Path("/Users/qf/IdeaProjects/copper-golem-vision-client-26.3")
profile=sys.argv[1] if len(sys.argv)>1 else "default"
assert profile in ("default","small")
run=pathlib.Path("/private/tmp/destiny-w227-native/client-run")
log=(root/("client-w227-"+profile+".log")).open("x")
p=subprocess.Popen(["rtk","proxy","./gradlew","runClient","--offline","--no-daemon","--console=plain","-PvisionPort=8102","-PvisionServer=127.0.0.1:25611","-PvisionControl=true","-PvisionControlBackground=true","-PvisionControlServer=127.0.0.1:25611","-PqaRunDir="+str(run),"-PqaUsername=WeaponW129QA"],cwd=project,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
(root/"client-launcher.pid").write_text(str(p.pid))
s=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);s.bind(str(path));os.chmod(path,0o600);s.listen(1);s.settimeout(.5)
try:
 while p.poll() is None:
  conn=None
  try:
   conn,_=s.accept()
   data=b""
   while not data.endswith(b"\n") and len(data)<20000:data+=conn.recv(4096)
   d=json.loads(data)
   if d.get("stop"):
    os.killpg(p.pid,signal.SIGINT);conn.sendall(b'{"stopping":true}\n');continue
   if d.get("scenario") in ("w47_reload_melee","w47_reload_super","w46_burst_release","w46_shell_interrupt","scope_charge","scope_empty_reload","scope_toggle","ads_melee","ads_super","ads","ads_fire","auto_recoil","use","attack","move","charge","reload","super","grenade","melee","super_attack","empty_reload","glaive_guard","glaive_guard_fire","glaive_combo"):
    out=root/"native"/d.get("label",d["scenario"]);result=subprocess.run(["rtk","proxy","node","/Users/qf/IdeaProjects/DestinyGuardians/scripts/qa/run_native_w47.mjs",d["scenario"],str(out)],cwd=project,env=env,capture_output=True,text=True,timeout=35)
    answer=dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
   elif "steps" in d:
    code="""import {createControlClient} from './mcp-bridge/control-client.mjs';
import {writeFile,mkdir} from 'node:fs/promises';import {setTimeout as delay} from 'node:timers/promises';
let data='';for await(const c of process.stdin)data+=c;const input=JSON.parse(data),client=createControlClient();
const before=await client.state(),observations=[];let running=true,captured=false,monitorError=null;const captures=[];
const monitor=(async()=>{while(running){const state=await client.state();observations.push({at:Date.now(),state});
if(input.captureFrames&&state.outcome==='running'&&captures.length<60){const response=await fetch('http://127.0.0.1:8102/screenshot',{signal:AbortSignal.timeout(10000)});if(!response.ok)throw Error('Screenshot failed');await mkdir('/private/tmp/destiny-w227-native/frames',{recursive:true});await writeFile('/private/tmp/destiny-w227-native/frames/'+input.label+'-sample-'+String(captures.length).padStart(2,'0')+'.png',Buffer.from(await response.arrayBuffer()));captured=true;captures.push({file:input.label+'-sample-'+String(captures.length).padStart(2,'0')+'.png',before:state,after:await client.state()});}
await delay(30);}})().catch(e=>{monitorError=String(e)});
let result,error;try{result=await client.runSequence({instanceId:before.instanceId,steps:input.steps});}catch(e){error=e.toJSON?.()??String(e);}finally{running=false;await monitor;}
await delay(150);console.log(JSON.stringify({before,result,error,monitorError,captured,captures,observations,released:await client.state()},(k,v)=>k==='leaseId'?'REDACTED':v));if(error)process.exitCode=1;"""
    label=d.get("label","sample")
    if not label.replace("-", "").replace("_", "").isalnum():raise ValueError("Invalid label")
    result=subprocess.run(["rtk","proxy","node","--input-type=module","-e",code],input=json.dumps(dict(steps=d["steps"],label=label,captureFrames=d.get("captureFrames",False))),cwd=project,env=env,capture_output=True,text=True,timeout=40)

    answer=dict(returncode=result.returncode,stdout=result.stdout,stderr=result.stderr)
   else:
    route=d["route"]
    if not any(route.startswith(x) for x in ("state","control/state","screenshot","perspective?","look?","hud?","pause_on_lost_focus?","screen?")):raise ValueError("Unsupported observation route")
    req=urllib.request.Request("http://127.0.0.1:8102/"+route,headers={"Authorization":"Bearer "+env["VISION_CONTROL_TOKEN"]})
    raw=urllib.request.urlopen(req,timeout=20).read()
    if "out" in d:
     output=pathlib.Path(d["out"]).resolve()
     if root not in output.parents:raise ValueError("Output outside QA root")
     output.parent.mkdir(parents=True,exist_ok=True);output.write_bytes(raw);answer=dict(saved=str(output),bytes=len(raw))
    else:answer=json.loads(raw)
   conn.sendall(json.dumps(answer).encode()+b"\n")
  except socket.timeout:pass
  except Exception as e:
   try:conn.sendall(json.dumps(dict(error=type(e).__name__)).encode()+b"\n")
   except:pass
  finally:
   if conn is not None:conn.close()
finally:s.close();path.unlink(missing_ok=True);log.close()
print("Owned client wrapper exited",p.wait())
