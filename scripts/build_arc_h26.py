#!/usr/bin/env python3
"""H26 fast Arc flourish and strikes, H23 rig/18 other clips untouched."""
import copy, json, sys, math
from pathlib import Path
sys.dont_write_bytecode = True
import build_hunter_animation_h15 as h15
import build_hunter_animation_h19 as h19
import build_hunter_animation_h20 as h20
import build_arc_h23 as h23
ROOT = Path(__file__).resolve().parents[1]
MODEL = "guardian_hunter_h26_r2"
SOURCE = ROOT/"art/blockbench/animations/guardian_hunter_h23_r2.bbmodel"
ART = ROOT/f"art/blockbench/animations/{MODEL}.bbmodel"
PACK = ROOT/"src/main/resources/destiny/animation/hunter_h26.animation.json"
START = "h15_super_arc_start"
ATTACK = "h15_super_arc_attack"

def one_hand(model, base, wrist, angles, free):
    p = copy.deepcopy(base)
    h19.solve_arm(model,p,"right",wrist,[1,0,1])
    h19.solve_arm(model,p,"left",free,[-1,-1,0])
    h20.aim_right(model,p,h15.rot(angles))
    return p

def compose(source):
    model=copy.deepcopy(source);model["name"]=model["model_identifier"]=MODEL
    clips={c["name"]:c for c in source["animations"]}
    ready,_=h19.sample(clips["h15_super_arc"],0)
    hero=h23.summon(model)
    coil=one_hand(model,h20.stance(-38,-12,1.3),[4.5,22,0],[10,-15,-55],[-5,20,-4])
    follow=one_hand(model,h20.stance(32,-10,1.3),[4,20,-5],[0,12,125],[-5,19,-6])
    start=h20.new_clip(model,START,[(0,h15.zero()),(.05,coil),(.15,hero),(.20,hero),
        (.25,follow),(.35,h20.staff_pose(model,10,[3,19,-5],[0,5,82],-4)),(.45,ready),(.50,ready)],
        scales=[(0,.001),(.05,.35),(.10,1),(.50,1)])
    # 100ms wind-up, with most angular displacement in the final 50ms.
    coil=h20.staff_pose(model,-40,[4.6,18.5,-3.8],[15,-22,20],-12)
    drive=h20.staff_pose(model,-27,[4.9,20,-5],[8,-12,34],-13)
    contact=h20.staff_pose(model,28,[3.8,20.4,-8.1],[0,0,118],-10)
    follow=h20.staff_pose(model,42,[2.5,21,-4.8],[-10,22,142],-6)
    recover=h20.staff_pose(model,12,[2.7,17.7,-6],[-4,12,92],-2)
    frames=[(0,ready),(.025,coil),(.05,drive),(.10,contact),
        (.15,follow),(.20,h20.mix(follow,recover,.4)),(.25,recover),(.35,ready)]
    for _,p in frames:
        r=h19.fk(model,p)["pri_right_item"]
        h19.solve_arm(model,p,"left",h19.point(r,[0,6,0]),[-.8,-1,.2])
    attack=h20.new_clip(model,ATTACK,frames)
    h20.densify_staff_support(model,attack)
    model["animations"]=[start if c["name"]==START else attack if c["name"]==ATTACK else c
                         for c in model["animations"]]
    return model

def validate(model,source):
    before={c["name"]:c for c in source["animations"]};after={c["name"]:c for c in model["animations"]}
    assert set(after)==set(before)
    for name in before:
        if name not in (START,ATTACK):assert before[name]==after[name],name
    for field in source:
        if field not in ("name","model_identifier","animations"):assert source[field]==model[field],field
    assert after[START]["length"]==.50 and after[ATTACK]["length"]==.35
    for clip in (after[START],after[ATTACK]):
        end,y=h19.sample(clip,clip["length"]);ready,ry=h19.sample(after["h15_super_arc"],0)
        assert abs(y-ry)<1e-6
        for bone in ready:
            assert all(abs((a-b+180)%360-180)<1e-5 for a,b in zip(end[bone],ready[bone])),bone
        for a in clip["animators"].values():
            for channel in {k["channel"] for k in a["keyframes"]}:
                keys=[k for k in a["keyframes"] if k["channel"]==channel]
                assert len({k["time"] for k in keys})==len(keys)
                assert min(k["time"] for k in keys)==0 and max(k["time"] for k in keys)==clip["length"]
        for k in next(a for a in clip["animators"].values() if a["name"]=="player_root")["keyframes"]:
            if k["channel"]=="position":assert k["data_points"][0]["x"]==k["data_points"][0]["z"]==0
    worst=0
    for i in range(15):
        p,y=h19.sample(after[ATTACK],i*.025);m=h19.fk(model,p,y)
        gap=h19.norm(h19.sub(h19.point(m["pri_right_item"],[0,6,0]),h19.point(m["pli_left_item"],[0,0,0])))
        worst=max(worst,gap)
    assert worst<1e-5,worst
    print("PASS H26: 20 clips, 18 verbatim; .50s deploy / .10s contact / .35s recovery; FK gap",worst)

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
