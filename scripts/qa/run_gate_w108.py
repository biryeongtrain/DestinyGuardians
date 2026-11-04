#!/usr/bin/env python3
"""One forced central gate; preserves first failures and fresh reports without rerun loops."""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "docs/qa/2026-10-25/w108"
n = int(sys.argv[1])
log = QA / f"gate-{n}.log"
if log.exists(): raise SystemExit("Refusing to overwrite a gate")
env = dict(os.environ, JAVA_HOME="/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home")
started = time.time()
with log.open("w") as stream:
    result = subprocess.run(["./gradlew", "test", "build", "--rerun-tasks", "--offline", "--no-daemon", "--console=plain"],
                            cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
xml = ROOT / "build/test-results/test"
if xml.exists(): shutil.copytree(xml, QA / f"gate-{n}-xml")
jar = ROOT / "build/libs/destiny-guardians-0.1.0+26.3.jar"
if jar.exists(): (QA / f"gate-{n}-jar.sha256").write_text(hashlib.sha256(jar.read_bytes()).hexdigest() + "\n")
summary = dict(gate=n, returncode=result.returncode, startedAt=started, finishedAt=time.time(),
               xmlFreshness={p.name: p.stat().st_mtime >= started for p in xml.glob("TEST-*.xml")} if xml.exists() else {})
(QA / f"gate-{n}-exit.json").write_text(json.dumps(summary, indent=2) + "\n")
print(json.dumps(dict(gate=n, returncode=result.returncode, log=str(log))))
sys.exit(result.returncode)
