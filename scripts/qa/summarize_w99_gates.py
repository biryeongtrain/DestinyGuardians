#!/usr/bin/env python3
"""Read archived forced gates; require two consecutive complete 822GT/704JUnit runs."""
from pathlib import Path
import json
import re
import xml.etree.ElementTree as E

ROOT = Path(__file__).resolve().parents[2]
QA = ROOT / "docs/qa/2026-10-25/w99"


def suites(folder):
    counts = dict(tests=0, failures=0, errors=0, skipped=0)
    ids = set()
    for path in folder.glob("TEST-*.xml"):
        doc = E.parse(path).getroot()
        for key in counts: counts[key] += int(doc.attrib[key])
        for t in doc.findall("testcase"): ids.add((t.attrib["classname"], t.attrib["name"]))
    return counts, ids


old, old_ids = suites(ROOT / "docs/qa/2026-10-25/w98/gate-2-xml")
assert old["tests"] == len(old_ids) == 704
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
    assert row["junit"] == dict(tests=704, failures=0, errors=0, skipped=0), row
    assert row["previousJUnitIdentitiesPreserved"] == 704 and row["newJUnit"] == 0, row
    assert row["requiredPassed"] == row["gameTestsTotal"] == 822, row
assert last[0]["jarSha256"] == last[1]["jarSha256"]
out = dict(gates=rows, finalPassingGates=[r["gate"] for r in last], jarSha256=last[-1]["jarSha256"],
           previousGameTests=820, newGameTests=2, previousJUnit=704, newJUnit=0,
           evidenceBoundary="Archived fresh forced logs/XML. Exact W89/W96 layer-oracle migration separately audited. No broad native or audio acceptance.")
(QA / "gate-summary.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out))
