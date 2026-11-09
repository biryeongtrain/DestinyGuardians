from pathlib import Path
import json
D=json.loads(Path(__file__).with_name('design.json').read_text())
STYLE='material'
T=16
ATLAS=1024
MATERIALS=D['materials']
def elements():return D['elements']
def is_magazine(n):return n.startswith('mag/')
