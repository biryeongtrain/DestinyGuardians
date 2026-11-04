#!/usr/bin/env python3
"""Clone controls for offline W75 generator; actual input/output bytes are preserved."""
import argparse, hashlib, json, runpy, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = "scripts/extract_aim_movement_w75.py"

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def snapshot(root, paths):
    return {p: (sha(root/p), (root/p).stat().st_mtime_ns) for p in paths if (root/p).exists()}

def audit():
    module = runpy.run_path(str(ROOT / SCRIPT))
    paths = [SCRIPT, *module["INPUTS"], module["OUTPUT"], module["EVIDENCE"]]
    actual = snapshot(ROOT, paths)
    controls = []
    child = '''import runpy,sys
sys.dont_write_bytecode=True
def guard(event,args):
    if event=="open" and ((isinstance(args[1],str) and any(c in args[1] for c in "wax+")) or args[2]& (1|2|64|512|1024)):
        raise RuntimeError("write blocked")
    if event in ("os.mkdir","os.remove","os.rename","socket.connect","socket.bind"):
        raise RuntimeError("mutation/network blocked: "+event)
sys.addaudithook(guard)
sys.argv=[sys.argv[1],"--verify"]
runpy.run_path(sys.argv[0],run_name="__main__")
'''
    for scenario in ("positive", "corrupt-output", "missing-output", "ratio-drift", "catalog-scope-drift"):
        with tempfile.TemporaryDirectory(prefix="destiny-w75-generator-") as td:
            clone = Path(td)
            for p in paths:
                (clone/p).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(ROOT/p, clone/p)
            if scenario == "corrupt-output":
                p = clone/module["OUTPUT"]; p.write_bytes(p.read_bytes()+b" ")
            elif scenario == "missing-output":
                (clone/module["OUTPUT"]).unlink()
            elif scenario == "ratio-drift":
                p = clone/module["INPUTS"][1]; data = json.loads(p.read_text()); data["ordinaryAdsScalar"] = .7
                p.write_text(json.dumps(data))
            elif scenario == "catalog-scope-drift":
                p = clone/module["INPUTS"][0]; data = json.loads(p.read_text())
                next(e for e in data if e["id"]=="seventh_seraph_officer_revolver")["frame"] = "adaptive"
                p.write_text(json.dumps(data))
            before = snapshot(clone, paths)
            proc = subprocess.run([sys.executable, "-c", child, str(clone/SCRIPT)], capture_output=True, text=True)
            assert (proc.returncode == 0) == (scenario == "positive"), (scenario, proc.stdout, proc.stderr)
            assert snapshot(clone, paths) == before, scenario
            controls.append(dict(scenario=scenario, passed=True, readOnly=True, exitCode=proc.returncode))
    assert snapshot(ROOT, paths) == actual
    return dict(stage="W75", scenarioCount=len(controls), mutationAndNetworkBlockedDuringVerify=True,
                actualInputsOutputsUnchanged=True, scenarios=controls)

if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--out", type=Path); args = p.parse_args(); report = audit()
    if args.out: args.out.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report))
