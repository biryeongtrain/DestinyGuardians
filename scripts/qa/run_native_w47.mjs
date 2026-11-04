#!/usr/bin/env node
// Opt-in real-client QA. Server fixture setup is external and must be documented separately.
import { pathToFileURL } from 'node:url';
const visionProject = process.env.VISION_CLIENT_PROJECT ?? '/Users/qf/IdeaProjects/copper-golem-vision-client-26.3';
const { createControlClient } = await import(pathToFileURL(visionProject + '/mcp-bridge/control-client.mjs'));
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { setTimeout as delay } from 'node:timers/promises';

const scenarios = {
  w47_reload_melee: [{keys:['use'],ticks:1},{keys:[],ticks:8},{keys:['sneak'],ticks:1},{keys:['sneak','attack'],ticks:1},{keys:[],ticks:45}],
  w47_reload_super: [{keys:['use'],ticks:1},{keys:[],ticks:8},{keys:['sneak'],ticks:1},{keys:['sneak','swap_offhand'],ticks:1},{keys:[],ticks:45}],
  w46_burst_release: [{keys:["use"],ticks:15},{keys:[],ticks:25}],
  w46_shell_interrupt: [{keys:["use"],ticks:1},{keys:[],ticks:20},{keys:["use"],ticks:1},{keys:[],ticks:12}],
  scope_charge: [{keys:['sneak'],ticks:20},{keys:['sneak','use'],ticks:36},{keys:[],ticks:20}],
  scope_empty_reload: [{keys:['sneak'],ticks:20},{keys:['sneak','use'],ticks:1},{keys:[],ticks:75}],
  scope_toggle: [{keys:['sneak'],ticks:30},{keys:[],ticks:20},{keys:['sneak'],ticks:30},{keys:[],ticks:20}],
  ads_super: [{keys:['sneak'],ticks:16},{keys:['sneak','swap_offhand'],ticks:1},{keys:[],ticks:35}],
  ads_melee: [{keys:['sneak'],ticks:16},{keys:['sneak','attack'],ticks:1},{keys:[],ticks:35}],
  glaive_guard: [{keys:['sneak'],ticks:80},{keys:[],ticks:8}],
  glaive_guard_fire: [{keys:['sneak'],ticks:2},{keys:['sneak','use'],ticks:30},{keys:[],ticks:12}],
  glaive_combo: [{keys:['attack'],ticks:1},{keys:[],ticks:12},{keys:['attack'],ticks:1},{keys:[],ticks:12},{keys:['attack'],ticks:1},{keys:[],ticks:12}],
  use: [{keys:['use'],ticks:8},{keys:[],ticks:20}],
  charge: [{keys:['use'],ticks:32},{keys:[],ticks:12}],
  empty_reload: [{keys:['use'],ticks:1},{keys:[],ticks:75}],
  // No native Q in Vision v1: this alias only demonstrates an already-empty trigger reload.
  reload: [{keys:['use'],ticks:1},{keys:[],ticks:75}],
  ads: [{keys:['sneak'],ticks:40},{keys:[],ticks:15}],
  ads_fire: [{keys:['sneak'],ticks:16},{keys:['sneak','use'],ticks:8},{keys:[],ticks:20}],
  auto_recoil: [{keys:['use'],ticks:36},{keys:[],ticks:22}],
  attack: [{keys:['attack'],ticks:1},{keys:[],ticks:20}],
  move: [{keys:['forward','sprint'],ticks:20},{keys:[],ticks:8}],
  super: [{keys:['sneak'],ticks:16},{keys:['sneak','swap_offhand'],ticks:1},{keys:[],ticks:30}],
  super_attack: [{keys:['attack'],ticks:1},{keys:[],ticks:35}],
  grenade: [{keys:['swap_offhand'],ticks:1},{keys:[],ticks:60}],
  melee: [{keys:['sneak'],ticks:16},{keys:['sneak','attack'],ticks:1},{keys:[],ticks:45}],
};
const [name, directory] = process.argv.slice(2);
if (!Object.hasOwn(scenarios,name) || !directory) throw new Error('Usage: control-smoke.mjs use|charge|reload|attack|move|super|super_attack|grenade|melee OUTPUT_DIR (requires authorized QA world)');
const client = createControlClient();
const root = path.resolve(directory); await mkdir(root,{recursive:true});
const before = await client.state();
const observations = [];
const capture = async label => {
  const a = await client.state();
  const response = await fetch(`http://127.0.0.1:${process.env.VISION_PORT ?? '8100'}/screenshot`, {redirect:'error',signal:AbortSignal.timeout(5000)});
  if (!response.ok) throw new Error('Screenshot failed');
  const png = Buffer.from(await response.arrayBuffer());
  if (png.subarray(0,8).toString('hex')!=='89504e470d0a1a0a') throw new Error('Not a PNG');
  await writeFile(path.join(root,label+'.png'),png);
  const b = await client.state();
  return {file:label+'.png',wallTime:new Date().toISOString(),before:a,after:b};
};
const captures=[await capture('before')];
let running=true,result,error,monitorError;
const cancel = new AbortController();
const monitor=(async()=>{
  while(running) {
    const state=await client.state(); observations.push({wallTime:new Date().toISOString(),state});
    if(state.outcome==='running' && captures.length<(((name.startsWith('w46_')||name.startsWith('w47_'))||name.includes('reload'))?40:name.startsWith('scope_')?24:name==='charge'?19:9)) captures.push(await capture('sample-'+captures.length));
    await delay(75);
  }
})().catch(e=>{ monitorError=e.toJSON?.() ?? {error:'monitor_failed'}; cancel.abort(); });
try { result=await client.runSequence({instanceId:before.instanceId,steps:scenarios[name]},{signal:cancel.signal}); }
catch(e) { error=e.toJSON?.() ?? {error:'scenario_failed'}; }
finally { running=false; await monitor; }
await delay(150); // Allow next native neutral Input packet; not a server ACK.
const released=await client.state();
captures.push(await capture('after'));
const report={scenario:name,steps:scenarios[name],before,result,error,monitorError,released,observations,captures,
  inputEvidence:'Client-internal logical keys via native consumer, not OS/CU or server-direct abilities',
  captureTiming:'State brackets each screenshot; not exact tick/frame synchronization'};
await writeFile(path.join(root,'report.json'),JSON.stringify(report,null,2)+'\n');
if(error || monitorError || released.leaseActive || released.heldKeys.length) process.exitCode=1;
console.log(JSON.stringify({scenario:name,outcome:result?.after?.outcome,error,released:!released.leaseActive,output:root}));
