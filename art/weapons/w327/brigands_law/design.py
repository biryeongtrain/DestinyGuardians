from pathlib import Path
import json
D=json.loads(Path(__file__).with_name('design.json').read_text())
REVISION=3
STYLE='material'
T=24
ATLAS=1024
NO_OVERLAY=False
MATERIALS=D['materials']
def elements():return D['elements']
def model2world(name,p):return ((p[0]-8)/36.5,(p[2]-7.7)/36.5,(p[1]-8.9)/36.5)
def is_magazine(name):return name.startswith('mag_')
def special(e,fn,s,t):return None
def material(name,fn):return next(e['role'] for e in D['elements'] if e['name']==name)
