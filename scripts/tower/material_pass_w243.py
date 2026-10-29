#!/usr/bin/env python3
"""W243 Courtyard 표면 재질 구획. 원본 형상과 내부 복셀은 보존한다.

원작 shader tint를 복원하는 변환기가 아닌, 출처 아트를 참고한 바닐라 재질 보강이다.
노출 smooth_stone만 full cube로 치환하므로 경로/충돌과 원본 데이터는 변하지 않는다.
"""
from __future__ import annotations
import argparse, collections, gzip, hashlib, json
from pathlib import Path
import numpy as np
from export_schematic import read_vox

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/main/resources/data/destiny/tower/courtyard.vox.gz"
OUTPUT = ROOT / "src/main/resources/data/destiny/tower/courtyard-materials-w243.json.gz"
AUDIT = ROOT / "docs/qa/2026-10-29/w243/tower-materials.json"
EXPECTED = "55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d"


def generate(source=SOURCE, output=OUTPUT, audit=AUDIT):
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != EXPECTED:
        raise ValueError("원본 복셀 변경: 새 미술 검토 없이 재생성하지 않습니다")
    xyz, indices, palette = read_vox(source)
    lo, hi = xyz.min(0)-1, xyz.max(0)+1
    grid = np.zeros(hi-lo+1, dtype=np.uint16)
    q = xyz-lo
    grid[tuple(q.T)] = indices+1
    top = grid[q[:,0],q[:,1]+1,q[:,2]] == 0
    side = np.zeros(len(xyz), dtype=bool)
    for dx,dz in ((1,0),(-1,0),(0,1),(0,-1)):
        side |= grid[q[:,0]+dx,q[:,1],q[:,2]+dz] == 0
    x,y,z = xyz.T
    # Courtyard와 가시적인 상부 외벽. 외곽 산/도시/미완성 지하 데이터는 제외한다.
    region = (x >= -15)&(x <= 125)&(z >= -125)&(z <= 22)&(y >= 65)&(y <= 113)
    selected = np.flatnonzero(region & (indices == palette.index("minecraft:smooth_stone")) & (top|side))
    blocks, cells, rules = [], [], collections.Counter()
    by_state = collections.Counter()
    for i in selected:
        px,py,pz = map(int, xyz[i])
        # 넓은 포장 패널: 랜덤 노이즈 대신 10x12 구획과 1블록 이음선.
        if -15 <= px <= 38 and -100 <= pz <= -10 and 86 <= py <= 91:
            if (pz+10)%20 <= 1:
                state,rule = "gray_concrete", "canopy-structural-rib"
            elif (pz+10)%40 <= 20:
                state,rule = "orange_terracotta", "canopy-ochre-panel"
            else:
                state,rule = "red_terracotta", "canopy-oxide-panel"
        elif top[i] and 69 <= py <= 77:
            if 66 <= px <= 75 and -85 <= pz <= 15:
                state,rule = "smooth_quartz", "axial-walkway"
            elif (px-6)%12 == 0 or (pz+4)%16 == 0:
                state,rule = "polished_andesite", "paving-joint"
            elif px >= 88 and pz <= -40:
                state,rule = "polished_deepslate", "service-deck"
            elif pz <= -88:
                state,rule = "cut_sandstone", "vendor-apron"
            else:
                state,rule = "smooth_sandstone", "warm-courtyard-paving"
        elif side[i]:
            # 건물 주면은 따뜻한 백색, 기단과 보는 어두운 금속으로 구분한다.
            if py <= 71 or py in (84,85,96,97):
                state,rule = "gray_concrete", "steel-plinth-and-bands"
            elif -112 <= pz <= -94 and 77 <= py <= 82 and 16 <= px <= 72:
                if (px-16)%18 <= 10:
                    state,rule = "red_terracotta", "vendor-oxide-fascia"
                else:
                    state,rule = "white_terracotta", "vendor-panel"
            elif py >= 104:
                state,rule = "smooth_quartz", "upper-coping"
            elif px in range(-5,3) or px in range(112,119):
                state,rule = "light_gray_concrete", "outer-structural-frame"
            else:
                state,rule = "white_terracotta", "warm-ivory-wall"
        else:
            state,rule = ("smooth_quartz", "roof-coping") if py >= 88 else ("light_gray_concrete", "terrace-edge")
        state = "minecraft:"+state
        if state not in blocks:
            blocks.append(state)
        cells.append([px,py,pz,blocks.index(state)])
        rules[rule] += 1
        by_state[state] += 1
    cells.sort(key=lambda c:(c[0]>>4,c[2]>>4,c[1],c[0],c[2]))
    if not 0 < len(cells) <= 100000 or len({tuple(c[:3]) for c in cells}) != len(cells):
        raise ValueError("invalid material pass size/duplicates")
    body = {"schema":1,"sourceVoxelSHA256":digest,"palette":blocks,"cells":cells}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("wb") as raw, gzip.GzipFile(fileobj=raw,mode="wb",mtime=0,filename="") as f:
        f.write(json.dumps(body,separators=(",",":")).encode())
    report = {"schema":1,"sourceVoxelSHA256":digest,"cells":len(cells),"gzipBytes":output.stat().st_size,
        "rules":dict(rules),"paletteCounts":dict(by_state),"bounds":[np.array(cells)[:,:3].min(0).tolist(),np.array(cells)[:,:3].max(0).tolist()],
        "references":["https://www.artstation.com/artwork/VRWon","https://ninehydras.artstation.com/projects/JqOba"],
        "method":"원본 노출 smooth_stone만 구역/고도/표면 방향별 full cube로 치환. 원작 PBR/tint 복원 아님.",
        "checks":{"sourceUnchanged":hashlib.sha256(source.read_bytes()).hexdigest()==digest,"uniqueCells":True,"sourceSmoothStoneOnly":True,"exposedOnly":True}}
    audit.parent.mkdir(parents=True,exist_ok=True)
    audit.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return body

if __name__ == "__main__":
    generate()
