import json,numpy as np
from PIL import Image
from scipy.spatial import cKDTree
d=json.load(open('/Users/qf/Downloads/Dreg-Light-Handoff/Dreg-Light/dreg_combat.bbmodel'))
A=np.asarray(Image.open('/tmp/dreg_handoff_atlas.png').convert('RGBA'))
t=json.load(open('/tmp/dreg_src_tris.json'))['tris']
P=np.array([x[:3] for x in t]);N=np.array([x[3:6] for x in t]);mats=sorted({x[6] for x in t});MI=np.array([mats.index(x[6]) for x in t])
S=30/2.3374
exec(open('/tmp/dreg_clothmask3d.py').read().split('tx=list(texels())')[0].split('def texels():')[1].join(['def texels():','']) if False else '')
src=open('/tmp/dreg_clothmask3d.py').read()
start=src.index('def texels():');end=src.index('tx=list(texels())')
exec(src[start:end])
tx=list(texels());ij=np.array([(a,b) for a,b,_,_ in tx]);pb=np.array([p for _,_,p,_ in tx]);nb=np.array([n for _,_,_,n in tx],float)
q=np.stack([pb[:,0]/S,-pb[:,2]/S,pb[:,1]/S],1);qn=np.stack([nb[:,0],-nb[:,2],nb[:,1]],1)
dk,ik=cKDTree(P).query(q,k=8)
w=np.exp(-dk/0.01)*(1+ (np.einsum('ij,ikj->ik',qn,N[ik])>0.2))
lab=np.zeros(len(tx),int)
votes=np.zeros((len(tx),len(mats)))
for k in range(8): np.add.at(votes,(np.arange(len(tx)),MI[ik[:,k]]),w[:,k])
lab=votes.argmax(1)
M=np.full(A.shape[:2],255,np.uint8);M[ij[:,1],ij[:,0]]=lab
Image.fromarray(M).save('/Users/qf/IdeaProjects/DestinyGuardians/scripts/campaign/data/dreg_material_map.png')
json.dump(mats,open('/Users/qf/IdeaProjects/DestinyGuardians/scripts/campaign/data/dreg_material_map.json','w'))
print(mats,np.bincount(lab,minlength=len(mats)))
