# H15 궁극기 VFX 구현·편집 계약

2026-10-22. [로드맵1~3](18_헌터_고도화_로드맵.md)의 궁극기 전용 시각 효과다.
게임플레이 피해·사거리·쿨타임·궁극기 탄수는 바꾸지 않는다.

## 1. 표시 방식과 자산

| 효과 | BetterModel ID | 소스 삼각형 | 렌더본 | 클립 / 수명 |
|---|---|---:|---:|---|
| 지팡이 전격 궤적 | `destiny_super_arc_sweep_h15` | 1080 | 3 | spawn0.6초 / 12틱 |
| 골든 건 총구 | `destiny_super_solar_muzzle_h15` | 1152 | 3 | spawn0.45초 / 9틱 |
| 골든 건 착탄 | `destiny_super_solar_impact_h15` | 1152 | 3 | spawn0.7초 / 14틱 |
| 그림자 사격 닻 | `destiny_super_void_anchor_h15` | 832 | 3 | loop1.2초 / 능력 설정160틱 |

메시 전용 모델이다. 12방향·5링 코어, 겹친 테이퍼 곡선, 분기 끝과 작은 불티를 분리했다.
각 모델의 렌더본3개가 독립적으로 회전/축소되며, 기존 H14 수류탄·근접 모델을 대체하지 않는다.
소스는 `art/blockbench/vfx/destiny_super_*_h15.bbmodel`, JAR 번들은 `destiny/vfx/`다.
`HunterVfxAssets`는 구형4종과 신형4종을 모두 설치하되 기존 운영자 파일은 덮어쓰지 않는다.

화염 궤적과 공허 연결선은 **각각 Polymer item_display1개**다. BetterModel을 포기한 전체 구현이
아니라 비균일 길이 스케일이 필요한 선에만 사용하는 보조 경로다.

- 아이템: `destiny:fx/{solar_trail,void_link}_h15`
- 모델: `models/fx/`, 텍스처: `textures/item/fx/`
- 편집 원본: `art/blockbench/vfx/{solar_trail,void_link}_h15.bbmodel`
- 각각48큐브/288면/최대576삼각형. 단위 길이1블록, 로컬 −Z가 전방.
- 폭과 길이 배율을 분리해 먼 표적일수록 과도하게 굵어지는 문제를 피한다.
- 태양 선은 최대10틱, 공허 선은12틱 TTL을10틱마다 갱신한다.

## 2. 능력 훅

`HunterSuper` → `SuperVfx` → `HunterVfx` 또는 Polymer 빔으로 연결된다.

1. **Arc:** 허용된 primary에서 지팡이 공격 클립과 전방 전격을 생성한다. 실제 명중 대상 중 최대2개에
   기존 Arc 타격 모델을 표시한다. BetterModel 변환을 보정하기 위해 전격 모델 yaw에180도를 더한다.
   플레이어의 조준과 부채꼴 피해 판정은 바꾸지 않는다.
2. **Solar:** 허용된 primary의 기존 hitscan 결과를 사용한다. 총구·착탄 모델과 고정 양끝 화염 선을
   생성한다. 실제 적 명중일 때 적중 화면 펄스를 요청한다. 세 번째 발사 후에도 마지막 원샷은 시각적으로 끝낸다.
3. **Void:** 전용 `destiny:shadow_arrow`를 기존 서버 계산 투사체로 발사한다. 착탄 위치에 닻을 생성하고
   기존 범위 내 적 전체에 적용하던 약화·억제·끌기 판정은 유지한다. 시각 연결선만 가까운 적 최대3마리로 제한한다.
   같은 소유자·닻·대상 조합은 홀더를 재사용하며 **매 서버틱** 대상의 몸통 위치로 끝점을 갱신한다.
   범위 이탈/사망/차원 변경 대상은 다음 틱에 선을 제거한다. 닻 종료는 해당 닻의 선만 지운다.

발동 시 기존의 큰 눈높이 파티클 구름은 작은 발밑 먼지16개로 바꿨다.
1인칭을 가리는 연출을 줄이고 장비·모델·[화면 펄스](21_궁극기_화면_펄스.md)를 주 피드백으로 쓴다.

## 3. 수명·상한과 실제 비용

- `HunterVfx`: 기존/신규 모델이 **공유하는** 소유자4·전체24트래커 상한.
- `SuperVfx`: 별도로 소유자4·전체24빔 홀더 상한. 둘의 합계 상한은 **소유자8·전체48**이다.
- BetterModel 모델당3렌더본, 빔당1 item_display. 48은 디스플레이 엔티티 수나 드로콜 수가 아니다.
- 모델 뷰어는5틱마다48블록 내 갱신, 빔 viewRange0.75. 다인 거리 경계 동작은 후속4번에서 검증한다.
- 유한 좌표/양수 TTL/길이96블록 이하 검사. 비정상 입력은 홀더를 생성하지 않는다.
- 사망·차원 이동·접속 종료·능력 정리·서버 종료 시 관련 트래커/홀더/펄스를 정리한다.
- 렌더러 실패는 경고 후 시각 자원을 해제하며 능력 피해 판정을 중단하지 않는다.

실제 생성 팩은 BetterModel 메시 삼각형당 **3개의 변환 모델 파트**를 출력했다.

| 효과 | 출력 파트 | bone item JSON 합계 바이트 |
|---|---:|---:|
| ArcSweep | 3240 | 888299 |
| SolarMuzzle | 3456 | 948826 |
| SolarImpact | 3456 | 948032 |
| VoidAnchor | 2496 | 691524 |

[실제 ZIP 측정](../qa/2026-10-22/super-h15-generated-pack-budget.json)은 압축/비압축 비용과
공유 primitive를 구분한다. 이 수치는 FPS·GPU 드로콜 실측이 아니다. 최대 동시 부하는 후속4번이다.

## 4. 편집·재생성

Blockbench MCP에서 새 프로젝트를 만들고 반환된 UUID로 프로젝트를 선택했다.
native Mesh/Cube·Texture·Group·Undo·Animation·codec로 제작/내보내기를 수행했다.
사용자 탭이나 다른 작업자의 현재 선택 프로젝트를 대상으로 수정하지 않는다.

```sh
rtk proxy python3 scripts/export_hunter_super_vfx.py
rtk proxy python3 scripts/export_hunter_beams.py
```

MCP `http://localhost:3000/bb-mcp`가 필요하다. 메시 저작 코드는
`scripts/build_hunter_super_vfx.js`, 삼각형/본 예산은 `art/blockbench/vfx/manifest-super-h15.json`이다.
이 명령은 런타임 번들을 다시 쓰므로 실제 서버를 멈춘 뒤 실행한다.
설치된 운영자 파일은 자동 갱신하지 않으며 새 모델 ID나 운영자의 명시적 교체가 필요하다.

## 5. 검증과 한계

- 최종 전체 GameTest71/71·JUnit28/28. 신규 VFX GameTest6개는 실제 BetterModel renderer/Polymer holder,
  정상틱 TTL, 대상 이동 시 재사용/범위 이탈,3대상 시각 상한, 소유자 격리/상한/잘못된 값, 차원 변경을 검사한다.
- Copper Golem Vision26.3, JVM2, 정상20TPS에서 전방 궤적·총구/착탄·화염 선·움직이는 공허 선을 확인했다.
  [실제 화면](../qa/2026-10-22/super_h15_overview.jpg) · [조건·해시·한계](../qa/2026-10-22/super-h15-validation.json).
- 모델 표면은 불투명/상수 tint와 Minecraft 음영이다. 가산 합성·선택적 블룸·볼류메트릭·동적 조명은 없다.
- Destiny 시각 자료의 색/실루엣을 참고한 새 메시다. 원작 메시 추출이나 정확한 토폴로지·시간 곡선 재현이 아니다.
- 빠른 화살의 근접 비행 방향, 실제 GCB 전송/멀티플레이, 밤·동굴·부하, Vulkan/타 해상도/청음은 미검증이다.
