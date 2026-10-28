# W230 Props / HUD / VFX — R1 전달

쓰기 소유권: `/private/tmp/destiny-w230-art`만. main/worktree/sharedbuild/game/CU/SSD 쓰기 없음. live Blender에 연결하지 않고 별도 Blender 5.4.0 Alpha `--background --factory-startup --disable-autoexec`로 5개 원본을 읽었다. SSD 파티클 FBX는 같은 별도 프로세스에서 import했으며 원본을 저장하지 않았다.

## 통합

- `integration-manifest.json`: 정확114개 payload 파일 SHA256·크기·canonical bbox. `root` 아래 repository relative path 그대로 master가 선택 복사.
- `CANONICAL_CONTRACT.md`: handheld/field/anchor/scale의 최종 계약. 조기 계약의 staff 치수, aura wireframe, 검 높이 수치를 이 문서로 대체한다.
- 3D 기본10 + extra4(식립 지팡이, 식립 검, 손 검, maulwave) =14종 × normal/enemy × model/item/PNG =84파일.
- HUD10종 × texture/model/item =30파일. 원본 흰 silhouette이고 custom_model_data tint index0으로 런타임 색 지정.
- 모든 의존 JSON/PNG는 payload 내부에 있다. 기존 asset overwrite가 필요한 공용 파일이 없다. 소스 archive/Blender/raw SSD/런타임은 payload에 포함되지 않는다.

## 실제 확보 자료

Drive 승인 root: https://drive.google.com/drive/folders/14Ry-piQtH3j6MlfoVLfFfu98c4pcTJUb

2026-10-28 hunter/titan/warlock 하위폴더를 live HTTP 조회했고 정확9개 archive/render를 다운로드했다. `sources/download-index.json`에 sourceURL, fileID, SHA와 HTTP 메타데이터. archive5개 정상 bsdtar 추출.

| 원본 | 직접 확인 | 이번 사용 |
|---|---|---|
| Burning Maul / Flaming Maul.blend | 4mesh,4894tri, diffuse+FX texture | 넓은 둥근 망치 머리/긴 자루/하단 그립. 85요소 semantic 재설계, painted scroll relief와 불꽃은 authored finish |
| Well of Radiance.blend | 전체15634tri 중 Sword8476tri, source 원점과 실제 형상 | W229의 같은 Dawnblade 계열 semantic sword211요소 재사용. 직접 확인한 source Well sword와 별개로 원작 GPU장판은 복원하지 않음 |
| Arcstrider Staff.blend | 9196tri, diffuse/normal/MRC | 140요소 긴 연속 shaft/구간별 wrap/양끝 spearhead. **Gathering 전용 event-linked spear 원본이라고 주장하지 않음** |
| Storms Edge Machete.blend | 201tri, diffuse/normal/MRC | 68요소 곡선 칼날/offset guard/short serration. 원본 주제의 semantic 재설계 |
| Hunter Knife.blend | 1962tri, diffuse/normal/MRC | solar knife의 curved blade/두 finger loop와 hook 참고. 66요소 authored warm finish |

원본 triangle을 그대로 복제/voxelize하지 않았다. 긴 의미 있는 큐브와 실제 입체 edge, 검증된 26.3 adapter의 alpha-masked right-triangle cuboids로 단순 outline을 닫힌 입체로 만들었다. low count만으로 원작일치/품질/성능을 보증하지 않는다. 텍스처는 넓은 재질면과 painted wrap/scroll/energy seam로 정돈했고 원작 PBR 복원은 아니다.

SSD read-only: `/Volumes/qf-ssd/Titan-Fists-of-Havoc-2026-10-28/supers_effects/hunter_spectral_blades`. 대표3 FBX를 실제 import했다. 80D8B516은 작은 sphere480tri,80D8B52E/80D8B5C8은 torus1728tri로 확인했다. 이들을 실제 칼 본체라고 해석하지 않는다. source SHA/vertices는 sources/evidence/spectral-particle-meshes.json, 실제 projection은 evidence/spectral-source-shapes.png.

## 정확히 없는 자료 / 임시 제작

- Spectral Blades 실제 전용 칼 본체·고유 UV/skin. 현재 칼은 자체 임시 제작.
- Gathering Storm 전용 spear의 animation event-linked 원본 식별. 현재 Arcstrider Staff 참고 대체품.
- Ward of Dawn 원작 반투명 GPU shader/굴절/lighting. 현재 자체 cutout lattice dome이며 실제 보호 충돌은 runtime 별도.
- Well of Radiance 원작 GPU field simulation. 칼은 원본 확인+W229 파생, ground rings는 자체 임시 제작.
- Chaos Reach 원본 beam GPU effect, Nova Warp 충전/폭발 GPU effect, Thundercrash 비행 방전 시뮬레이션, Burning Maul heavy moving flame effect. 현재 한 geometry model 안에 bounded energy ribbons/branching bolts로 제작한 임시 표현.
- 이 소품 작업이 원작 모션40개를 새로 만들거나 모든 상태머신을 확보한 것은 아니다. 신규 애니메이션 중 일부 cast만 있고 attack/idle/종료가 원본에 없는 범위는 animation leader README를 유지해야 한다.

이 리스트 중 GPU effect shader 원본 없이도 현재 플레이 가능한 대체 표현은 가능하며 원본이 없다고 작업을 멈추지 않았다. Windows 추가 추출 요청은 위 전용 prop·event mapping에 한정 가능.

## 검증

- 자체 JSON 파싱/참조 의존성, finite geometry, UV 범위, native unrotated element bounds(-16..32), light emission0..15, 각 모델1000요소 미만 확인.
- normal/enemy는 geometry/UV/display 불변, PNG alpha exact byte 동일. RGB만 luminance를 보존하는 붉은 팔레트로 변경.
- HUD10개64x64, 비어있지 않은 흰 silhouette, W229 codec 동일. HUD는 공식 sprite 추출본이 아님.
- `evidence/w230-props-normal-enemy-contact-sheet.png`: 실제 exported JSON geometry를 오프라인 투영한 정면/사선/적군 사선. 실제 native screenshot 아님.
- `evidence/w230-hud-contact-sheet.png`: 실제 출력PNG.
- `evidence/source-shape-inspection.png`: 실제 Blender mesh 평가 좌표의 source projection. 원작 셰이더/게임 화면 아님.
- Native팩 로드, 피부손파지, 빛샘 시전 검의 동작 전환, maulwave 진행방향/스케일, field 수명/적군 spectator routing 및 최종성능은 master Vision R1/R2에서 확인해야 함. 본 worker 게임/중앙build 금지 준수.

## 단계 기록

1. art skill / Ace-Izanagi 연구를 읽고 큰 볼륨+UV 접근과1000상한 확인.
2. Drive live listing9다운로드5원본blend, SSD 대표파티클3개 read-only inspection.
3. 조기 path/anchor 계약 반환; field-only 장비 배제와 Well ground/sword 분리.
4. 3D12종+normal/enemy, HUD10개 생성, 실제 exported geometry offline review.
5. cage처럼 보이는 aura를 broken orbit/branching lightning으로 수정. 손 칼/지팡이를 실물 비율에 가깝게 재축소, 망치 head shoulder 보완.
6. master 요청에 따라 Well hand sword와 Maul heavy wave 추가.14종114payload.
7. native bounds/alpha/UV/reference/예산 검사와 manifest freeze. master R1 PNG 검수 피드백 대기. 이후 delta만 새 revision manifest로 전달.
