#!/usr/bin/env python3
"""Finite source/JAR/gate compatibility audit; no builds, runtime mutation or network."""
from pathlib import Path
import hashlib, importlib.util, json, re, xml.etree.ElementTree as ET, zipfile
ROOT = Path(__file__).resolve().parents[2]
Q = ROOT / "docs/qa/2026-10-25/w108"
def sha(b): return hashlib.sha256(b).hexdigest()
def load(p): return json.loads((ROOT / p).read_text())
def require(ok, label):
    if not ok: raise AssertionError(label)
def delta(a,b):
    return dict(modified=sorted(p for p in a.keys() & b.keys() if a[p]!=b[p]),
                added=sorted(b.keys()-a.keys()),removed=sorted(a.keys()-b.keys()))
def entries(p):
    with zipfile.ZipFile(p) as z:return {n:z.read(n) for n in z.namelist() if not n.endswith("/")}
def tests(folder):
    counts={k:0 for k in ("tests","failures","errors","skipped")};ids=set()
    for p in folder.glob("TEST-*.xml"):
        root=ET.parse(p).getroot()
        for k in counts:counts[k]+=int(root.get(k,"0"))
        for c in root.findall("testcase"):ids.add((c.get("classname"),c.get("name")))
    require(len(ids)==counts["tests"],"Unique JUnit identities")
    return counts,ids

def main():
    baseline=load(Q/"before-source.json")
    current={str(p.relative_to(ROOT)):sha(p.read_bytes()) for p in (ROOT/"src").rglob("*") if p.is_file()}
    change=delta(baseline,current)
    modified={"src/main/java/kim/biryeong/destiny/"+p for p in ["debug/DebugCommands.java","hud/WeaponPerkHud.java","weapon/WeaponDragonfly.java","weapon/WeaponPerkCommands.java","weapon/WeaponPerks.java","weapon/WeaponRuntime.java"]}|{"src/gametest/resources/fabric.mod.json","src/test/java/kim/biryeong/destiny/sound/FireVariantsW98Test.java"}
    added={"src/main/java/kim/biryeong/destiny/weapon/"+p+".java" for p in ["FeedingFrenzyCycle","FeedingFrenzyProfile","WeaponFeedingFrenzy"]}|{"src/gametest/java/kim/biryeong/destiny/test/"+p+".java" for p in ["FeedingFrenzyW108GameTests","FeedingFrenzyLifecycleW108GameTests"]}|{"src/test/java/kim/biryeong/destiny/weapon/"+p+".java" for p in ["FeedingFrenzyCycleTest","FeedingFrenzyProfileTest"]}|{"src/test/java/kim/biryeong/destiny/hud/FeedingFrenzyHudW108AssetTest.java","src/main/resources/destiny/weapons/w108-feeding-frenzy.json","src/main/resources/assets/destiny/items/gui/hud/perk_feeding_frenzy_w108.json","src/main/resources/assets/destiny/models/gui/hud/perk_feeding_frenzy_w108.json","src/main/resources/assets/destiny/textures/item/hud/perk_feeding_frenzy_w108.png"}
    require(change==dict(modified=sorted(modified),added=sorted(added),removed=[]),"Exact finite source delta")
    seals=load(Q/"previous-seal.json")
    require(all((ROOT/p).is_file() and sha((ROOT/p).read_bytes())==h for p,h in seals.items()),"Prior sealed W107 payload intact")
    old=entries(ROOT/"docs/qa/2026-10-25/w107/product.jar");new=entries(ROOT/"build/libs/destiny-guardians-0.1.0+26.3.jar")
    jar_delta=delta({p:sha(v) for p,v in old.items()},{p:sha(v) for p,v in new.items()})
    expected_modified={"kim/biryeong/destiny/debug/DebugCommands$1.class","kim/biryeong/destiny/debug/DebugCommands.class","kim/biryeong/destiny/hud/WeaponPerkHud.class"}|{"kim/biryeong/destiny/weapon/"+p+".class" for p in ["WeaponDragonfly$1","WeaponDragonfly$Token","WeaponDragonfly","WeaponPerkCommands","WeaponPerks","WeaponRuntime$FlightSnapshot","WeaponRuntime$GlaiveStatus","WeaponRuntime$HitDamage","WeaponRuntime$Shot","WeaponRuntime$SwordStatus","WeaponRuntime"]}
    expected_added={p.removeprefix("src/main/resources/") for p in added if p.startswith("src/main/resources/")}|{"kim/biryeong/destiny/weapon/"+p+".class" for p in ["FeedingFrenzyCycle","FeedingFrenzyProfile","FeedingFrenzyProfile$Curve","FeedingFrenzyProfile$Data","FeedingFrenzyProfile$Perk","FeedingFrenzyProfile$Policies","FeedingFrenzyProfile$Reload","FeedingFrenzyProfile$Row","FeedingFrenzyProfile$Tier","WeaponFeedingFrenzy","WeaponFeedingFrenzy$Session","WeaponFeedingFrenzy$Token"]}
    require(jar_delta==dict(modified=sorted(expected_modified),added=sorted(expected_added),removed=[]),"Exact finite JAR delta")
    def manifest(b):return dict(line.split(": ",1) for line in b.decode().splitlines() if ": " in line)
    require(manifest(old["META-INF/MANIFEST.MF"])==manifest(new["META-INF/MANIFEST.MF"]),"Only manifest whitespace, identical build fields")
    spec=importlib.util.spec_from_file_location("w107_audit",ROOT/"scripts/qa/audit_use_trace_w107.py");module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    line_only=[]
    for p in ["debug/DebugCommands$1","weapon/WeaponDragonfly$1","weapon/WeaponRuntime$FlightSnapshot","weapon/WeaponRuntime$GlaiveStatus","weapon/WeaponRuntime$HitDamage","weapon/WeaponRuntime$SwordStatus"]:
        name="kim/biryeong/destiny/"+p+".class";a,al=module.normalize_lines(old[name]);b,bl=module.normalize_lines(new[name])
        require(a==b,"Exact classfile bytes except line_number values: "+name);line_only.append(name)
    before_counts,before_ids=tests(ROOT/"docs/qa/2026-10-25/w107/gate-2-xml");require(before_counts["tests"]==760,"760 previous JUnit")
    gates=[];jar_sha=sha((ROOT/"build/libs/destiny-guardians-0.1.0+26.3.jar").read_bytes())
    for n in [3,4]:
        counts,ids=tests(Q/f"gate-{n}-xml");ex=load(Q/f"gate-{n}-exit.json");log=(Q/f"gate-{n}.log").read_text()
        require(counts==dict(tests=783,failures=0,errors=0,skipped=0),"Full JUnit counts")
        new_ids=ids-before_ids
        require(before_ids<=ids and len(new_ids)==23 and all(c in {"kim.biryeong.destiny.weapon.FeedingFrenzyCycleTest","kim.biryeong.destiny.weapon.FeedingFrenzyProfileTest","kim.biryeong.destiny.hud.FeedingFrenzyHudW108AssetTest"} for c,_ in new_ids),"Preserved old JUnit plus exact three new classes")
        require(ex["returncode"]==0 and all(ex["xmlFreshness"].values()) and "BUILD SUCCESSFUL" in log,"Fresh successful forced gate")
        require(re.findall(r"All (\d+) required tests passed",log)==["884"] and re.findall(r"(\d+) GAME TESTS COMPLETE",log)==["884"],"884 required/completed GameTests")
        require((Q/f"gate-{n}-jar.sha256").read_text().strip()==jar_sha,"Both gates identical final product")
        gates.append(dict(gate=n,junit=counts,gameTests=884,newJUnitIdentities=sorted(new_ids)))
    report=dict(stage="W108",status="PASS",sourceDelta=change,previousSealPaths=len(seals),previousSealIntact=True,jarSha256=jar_sha,jarDelta=jar_delta,lineNumberOnlyClasses=line_only,gates=gates,scope="Finite offline compatibility; not native input, rendering, hearing, multiplayer or performance acceptance")
    (Q/"product-audit.json").write_text(json.dumps(report,indent=2)+"\n");print(json.dumps({k:v for k,v in report.items() if k in ["stage","status","jarSha256","previousSealPaths"]}))
if __name__=="__main__":main()
