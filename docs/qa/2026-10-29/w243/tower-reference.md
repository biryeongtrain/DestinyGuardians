# W243 탑 재질 보강 근거

사용자 지정: [Marc Thompson — Destiny 2: The Tower Social Space](https://www.artstation.com/artwork/VRWon), [동일 artist portfolio](https://marcthompson.artstation.com/projects/VRWon).

2026-10-29 master가 실제031/029/030 이미지를 확인했다. 주황 타프와 산화된 붉은 난간/장비, 따뜻한 백색 콘크리트, 어두운 데크, 청색 안내 표시가 큰 색 면으로 분리된다. 단순히 회색 바닥에 작은 소품만 추가하는 것으로는 이 대비가 나타나지 않는다.

- [031 — 상점의 주황 타프·기단·노출 관](https://cdna.artstation.com/p/assets/images/images/007/498/344/large/marc-thompson-image-031.jpg?1506539603)
- [029 — 상부 데크·계단·붉은 난간](https://cdnb.artstation.com/p/assets/images/images/007/498/339/large/marc-thompson-image-029.jpg?1506539597)
- [030 — 광장 canopy·콘크리트·보행 동선](https://cdna.artstation.com/p/assets/images/images/007/498/342/large/marc-thompson-image-030.jpg?1506539600)

보조 출처 [Eve Astra](https://ninehydras.artstation.com/projects/JqOba)는 worker가 실제 두 이미지를 검토했다. 별도 worker 기록 참조.

전달 GLB는87MB/754재질 중707재질에 baseColorTexture가 있다. 따라서 원본 전체 텍스처 누락이라고 결론 내리지 않는다. extras에 source shader blending/lighting이 복원되지 않았다고 명시돼 있고 주 diffuse 자체가 회색이며, voxelizer는 재질별 median을 한 블록으로 축약했다. 이번 보강은 원작 shader나 정확한 dye map 재현이 아닌, 원본 형상을 보존한 바닐라 표면 재질 해석이다.

원본1,151,116블록 중1,048,398블록이 smooth_stone이다. 주요 광장 및 가시 외벽의 노출 smooth_stone58,117셀을10종 fullblock으로 분리한다. 포장 이음선·중앙 밝은 보행축·백색 벽·금속 띠·적갈 canopy를 넓은 면 단위로 적용한다. 새 대형텍스처/커스텀모델을 추가하지 않아 클라이언트 팩 용량은 증가하지 않는다. 원본 파일과 collision, 계단/안전 스폰, 관리자 수정은 보존한다.

데이터: [tower-materials.json](tower-materials.json). 생성: scripts/tower/material_pass_w243.py. 영구 적용 결과는 README와 runtime 로그에 구분해 기록한다.
