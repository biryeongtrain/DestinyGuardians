#!/usr/bin/env python3
"""Read-only W51 source inventory integrity. Hashes do not prove current live-game rules or sound audition."""
from pathlib import Path
import hashlib, json, re, html
ROOT=Path(__file__).resolve().parents[2]
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def path(value):
    p=Path(value)
    return p if p.is_absolute() else ROOT/p
checked={}
def check(value,expected):
    p=path(value)
    assert sha(p)==expected, value
    checked[str(p)]=expected
audit=json.loads((ROOT/'docs/qa/2026-10-24/w51/reference-audit.json').read_text())
for e in audit['inputPins']+audit['outputPins']+[audit['fullInventory']]:
    check(e['path'],e['sha256'])
manifest=json.loads((ROOT/'art/weapons/w51/references/official-manifest.json').read_text())
for key in ['selectedItemDefinitions','selectedPlugDefinitions']:
    e=manifest[key];check(e['path'],e['sha256'])
sources=json.loads((ROOT/'art/weapons/w51/references/sources.json').read_text())['sources']
quotes=0
for e in sources:
    for stem in ['article','response']:
        if stem+'Path' in e: check(e[stem+'Path'],e[stem+'Sha256'])
    # Compare text from every string in the pinned full article, not its external HTML shell.
    article=json.loads(path(e['articlePath']).read_text())
    strings=[]
    def visit(x):
        if isinstance(x,str):strings.append(x)
        elif isinstance(x,list):
            for a in x:visit(a)
        elif isinstance(x,dict):
            for a in x.values():visit(a)
    visit(article)
    text=html.unescape(re.sub('<[^>]+>',' ',' '.join(strings)))
    text=' '.join(text.split())
    for quote in e['verifiedQuotes']:
        q=' '.join(html.unescape(quote).split())
        assert q in text,(e['id'],quote)
        quotes+=1
report=dict(stage='W51',files=len(checked),sha256=checked,officialArticles=len(sources),
            exactQuotes=quotes,liveGameVerified=False,audioAuditionVerified=False)
out=ROOT/'docs/qa/2026-10-24/w51/source-verification.json'
out.write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='sha256'}))
