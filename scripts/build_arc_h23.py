#!/usr/bin/env python3
"""H23 Arc Staff: single summon silhouette, then a separate roaming cycle.
Only new H23 outputs; no installed/historical assets are overwritten.
"""
import copy, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
ROOT=Path(__file__).resolve().parents[1]
MODEL="guardian_hunter_h23_r2"
SOURCE=ROOT/"art/blockbench/animations/guardian_hunter_h22.bbmodel"
ART=ROOT/f"art/blockbench/animations/{MODEL}.bbmodel"
PACK=ROOT/"src/main/resources/destiny/animation/hunter_h23.animation.json"
START="h15_super_arc_start"
MOVE="h15_super_arc_move"

def summon(model):
    # Front -Z. Wide bent knees, one hand beside the temple holding a transverse
    # staff behind the shoulders, free hand reaching forward. Actual equipment IK.
    p=h15.pose(phip_hip=[10,10,0],pw_waist=[4,-10,0],pc_chest=[8,-18,-5],
        h_ph_head=[-5,18,4],prl_right_leg=[36,-16,29],prfl_right_foreleg=[-65,0,0],
        pll_left_leg=[20,22,-33],plfl_left_foreleg=[-42,0,0],cape_cape=[20,0,7])
    h19.solve_arm(model,p,"right",[5.5,23,2],[1,0,1])
    h19.solve_arm(model,p,"left",[-6.5,19,-7.5],[-1,-1,0])
    # Native staff local Y runs through the hand. +75deg Z is nearly horizontal;
    # the tip slope recalls the supplied Arcstrider reference, not a bow pose.
    h20.aim_right(model,p,h15.rot([0,0,75]))
    return p

def compose(source):
    model=copy.deepcopy(source);model["name"]=model["model_identifier"]=MODEL
    clips={c["name"]:c for c in model["animations"]}
    ready,_=h19.sample(clips["h15_super_arc"],0)
    neutral=h15.zero(); hero=summon(model)
    coil=h20.mix(neutral,hero,.55)
    # Show the exact hero silhouette once, then recover completely before input unlock.
    start=h20.new_clip(model,START,[(0,neutral),(.10,coil),(.20,hero),(.45,hero),
        (.60,h20.mix(hero,ready,.45)),(.75,ready),(.85,ready)],
        scales=[(0,.001),(.10,.15),(.20,1),(.85,1)])
    frames=[]
    for i in range(25):
        t=i/40;phase=t/.6*2*math.pi;p=copy.deepcopy(ready)
        # Existing two-handed upper stance stays fixed; legs no longer slide while roaming.
        p["prl_right_leg"]=[30*math.sin(phase),-8,5]
        p["prfl_right_foreleg"]=[-max(0,math.sin(phase))*38,0,0]
        p["pll_left_leg"]=[-30*math.sin(phase),12,-5]
        p["plfl_left_foreleg"]=[-max(0,-math.sin(phase))*38,0,0]
        p["cape_cape"]=[14+4*math.cos(phase*2),0,3*math.sin(phase)]
        frames.append((t,p))
    move=h20.new_clip(model,MOVE,frames,True)
    model["animations"]=[start if c["name"]==START else c for c in model["animations"]]+[move]
    return model

def validate(model,source):
    before={c["name"]:c for c in source["animations"]};after={c["name"]:c for c in model["animations"]}
    assert len([n for n in after if n.startswith("h15_")])==20 and set(after)==set(before)|{MOVE}
    for name in before:
        if name!=START:assert after[name]==before[name],name
    for field in source:
        if field not in ("name","model_identifier","animations"):assert model[field]==source[field]
    assert after[START]["length"]==.85 and after[START]["loop"]=="once"
    assert h19.sample(after[START],.20)==h19.sample(after[START],.45)
    assert h19.sample(after[START],.85)==h19.sample(after["h15_super_arc"],0)
    assert h19.sample(after[MOVE],0)==h19.sample(after[MOVE],.60)
    # Right wrist exactly holds the transverse staff. No support-hand constraint at summon:
    # the reference explicitly has a free forward hand.
    p,y=h19.sample(after[START],.3);m=h19.fk(model,p,y)
    axis=h19.vector(m["pri_right_item"],[0,1,0])
    assert abs(axis[0])>.9 and abs(axis[2])<1e-6,axis
    assert h19.point(m["pli_left_item"],[0,0,0])[2]<-7
    assert h19.point(m["prfl_right_foreleg"],[0,-6,0])[0]>4
    assert h19.point(m["plfl_left_foreleg"],[0,-6,0])[0]<-4
    assert p["prfl_right_foreleg"][0]<-60 and p["plfl_left_foreleg"][0]<-40
    print("PASS H23: 20 clips; 18 unchanged; one summon/hold/recovery .85s; transverse staff; roaming loop")

def main():
    assert sys.argv[1:] in ([],["--verify"])
    source=json.loads(SOURCE.read_text());model=compose(source);validate(model,source)
    pack={"model":MODEL,"animations":[c for c in model["animations"] if c["name"].startswith("h15_")]}
    for path,obj in ((ART,model),(PACK,pack)):
        data=(json.dumps(obj,indent=2)+"\n").encode()
        if sys.argv[1:]:assert path.read_bytes()==data,path
        else:path.write_bytes(data)
        print(path.relative_to(ROOT))
if __name__=="__main__":main()
