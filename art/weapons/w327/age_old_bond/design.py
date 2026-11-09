"""W327 V4 authored source-proportioned model. Generate with group3_v3.bake_fidelity; two-face alpha triangles require its atlas. Native QA pending."""
import json,copy
from pathlib import Path
DOC=json.loads((Path(__file__).parent/"v4/model.json").read_text())
ELEMENTS=sum(DOC["parts"].values(),[])
ROLES=json.loads((Path(__file__).parent/"v4/geometry.json").read_text())["roles"]
def elements():return copy.deepcopy(ELEMENTS)
