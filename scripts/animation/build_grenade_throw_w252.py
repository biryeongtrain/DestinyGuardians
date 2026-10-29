"""Retarget already evaluated SSD throw FK; no SSD writes or user Blender scene edits.
Evaluate source.blend with sample_throw_w252.py before running this adapter.
"""
import argparse,json,sys,math
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20

def main():
 a=argparse.ArgumentParser();a.add_argument('samples',type=Path);args=a.parse_args()
 data=json.loads(args.samples.read_text());clip=next(c for c in data['clips'] if '80A8A67C' in c['action'])
 names={'leftShoulder':'D1232BA2','leftElbow':'897A1504','leftWrist':'8C83CB67','rightShoulder':'17025F50','rightElbow':'A3781DCD','rightWrist':'DE9D6BEA'}
 frames=[{k:[round(f['joints'][n][i][3],7) for i in range(3)] for k,n in names.items()} for f in clip['frames']]
 out={'source':data['source'],'sourceSha256':data['sha256'],'action':clip['action'],'sourceFps':30,'sourceFrames':30,'poseCount':61,'durationTicks':20,'releaseTick':6,'releaseProvenance':'visual retarget calibration; no exported event frame','sourceAxes':'X forward Z up; object scale intentionally excluded','frames':frames}
 p=ROOT/'src/main/resources/destiny/animation/grenade_throw_w252.json';p.write_text(json.dumps(out,separators=(',',':'))+'\n')
 model=json.loads((ROOT/'art/blockbench/animations/guardian_hunter_h20.bbmodel').read_text());bind=h19.fk(model,h15.zero());samples=[]
 for i,f in enumerate(frames):
  pose=h15.zero()
  for side,group in [('left','pla_left_arm'),('right','pra_right_arm')]:
   def delta(name):
    v=[f[side+name][j]-f[side+'Shoulder'][j] for j in range(3)];return [-v[1]*16,v[2]*16,-v[0]*16]
   shoulder=h19.point(bind[group],[0,0,0]);target=h19.add(shoulder,delta('Wrist'))
   h19.solve_arm(model,pose,side,target,delta('Elbow'))
  samples.append((i/60*(29/30),pose))
 animation=h20.new_clip(model,'h15_grenade',samples)
 p=ROOT/'src/main/resources/destiny/animation/grenade_w252.animation.json';p.write_text(json.dumps({'animations':[animation]},separators=(',',':'))+'\n')
 print('W252 throw source retargeted',len(frames),'poses')
if __name__=='__main__':main()
