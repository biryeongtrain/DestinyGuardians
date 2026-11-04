#!/usr/bin/env python3
"""Read archived forced gates; require two consecutive complete contract-bound runs."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "docs/qa/2026-10-25/w103"


def suites(folder):
    counts = dict(tests=0, failures=0, errors=0, skipped=0)
    ids = set()
    for path in folder.glob("TEST-*.xml"):
        doc = E.parse(path).getroot()
        for key in counts: counts[key] += int(doc.attrib[key])
        for t in doc.findall("testcase"): ids.add((t.attrib["classname"], t.attrib["name"]))
    return counts, ids


contract = json.loads((QA / "integration.json").read_text())
expectedJUnit = contract["expectedJUnit"]
expectedGT = contract["expectedGameTests"]
newIds = {tuple(v) for v in contract["newJUnitIdentities"]}

old, old_ids = suites(ROOT / "docs/qa/2026-10-25/w102/gate-3-xml")
assert old["tests"] == len(old_ids) == 725
rows = []
for log in sorted(QA.glob("gate-[0-9]*.log"), key=lambda p: int(p.stem.split("-")[1])):
    n = int(log.stem.split("-")[1]); text = log.read_text(); counts, ids = suites(QA / f"gate-{n}-xml")
    passed = re.search(r"All (\d+) required tests passed", text)
    complete = re.search(r"(\d+) GAME TESTS COMPLETE", text)
    exit_data = json.loads((QA / f"gate-{n}-exit.json").read_text())
    rows.append(dict(gate=n, returncode=exit_data["returncode"], junit=counts,
                     previousJUnitIdentitiesPreserved=len(old_ids & ids), newJUnit=len(ids - old_ids),
                     requiredPassed=int(passed[1]) if passed else None,
                     gameTestsTotal=int(complete[1]) if complete else None,
                     forcedAllTasks="20 actionable tasks: 20 executed" in text,
                     allXmlFresh=bool(exit_data["xmlFreshness"]) and all(exit_data["xmlFreshness"].values()),
                     jarSha256=(QA / f"gate-{n}-jar.sha256").read_text().strip()))
last = rows[-2:]
assert len(last) == 2
for row in last:
    assert row["returncode"] == 0 and row["forcedAllTasks"] and row["allXmlFresh"], row
    assert row["junit"] == dict(tests=expectedJUnit, failures=0, errors=0, skipped=0), row
    assert row["previousJUnitIdentitiesPreserved"] == 725 and row["newJUnit"] == len(newIds), row
    assert row["requiredPassed"] == row["gameTestsTotal"] == expectedGT, row
for row in last:
    _, identities = suites(QA / f"gate-{row['gate']}-xml")
    assert identities == old_ids | newIds, row
assert last[0]["jarSha256"] == last[1]["jarSha256"]
out = dict(gates=rows, finalPassingGates=[r["gate"] for r in last], jarSha256=last[-1]["jarSha256"],
           previousGameTests=831, newGameTests=expectedGT-831, previousJUnit=725, newJUnit=len(newIds),
           evidenceBoundary="Fresh forced logs/XML: base Demolitionist baseline chunk and paid grenade refill. Existing test identities retained. No live D2 ability/stat scalar fidelity or native rendering/audio acceptance.")
(QA / "gate-summary.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out))
