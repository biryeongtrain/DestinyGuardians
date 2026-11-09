from pathlib import Path
import json
D=json.loads(Path(__file__).with_name('design.json').read_text())
REVISION=3
STYLE='material'
T=20
ATLAS=1024
NO_OVERLAY=False
MATERIALS=D['materials']
def elements():return D['elements']
def model2world(name,p):
 m=D['source_mapping'];u=(p[2]-m['z0'])/m['q'];v=(m['y0']-p[1])/m['q'];return ((p[0]-8)/m['sx'],m['centre'][1]+(u-m['res'][0]/2)/m['ppm'],m['centre'][2]+(m['res'][1]/2-v)/m['ppm'])
def is_magazine(name):return name.startswith('mag_')
def special(e,fn,s,t):return None
def material(name,fn):return next(e['role'] for e in D['elements'] if e['name']==name)
