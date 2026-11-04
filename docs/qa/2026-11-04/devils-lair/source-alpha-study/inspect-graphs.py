import bpy,json
from pathlib import Path
bpy.ops.wm.open_mainfile(filepath='/tmp/devils-drive-marauder-dual/evaluated-qa.blend')
rows=[]
for m in bpy.data.materials:
 if not m.use_nodes:continue
 tree=m.node_tree;nodes=[]
 for n in tree.nodes:
  if n.type in ['MIX_SHADER','ADD_SHADER','OUTPUT_MATERIAL','BSDF_TRANSPARENT','BSDF_PRINCIPLED','GROUP']:
   nodes.append(dict(name=n.name,type=n.type,inputs=[dict(name=s.name,fromNode=s.links[0].from_node.name,fromSocket=s.links[0].from_socket.name) if s.is_linked else dict(name=s.name,value=str(getattr(s,'default_value',''))) for s in n.inputs if s.type=='SHADER' or s.name in ['Fac','Surface','Alpha']]))
 rows.append(dict(material=m.name,nodes=nodes))
Path('/tmp/devils-source-alpha/graphs.json').write_text(json.dumps(rows,indent=2))
