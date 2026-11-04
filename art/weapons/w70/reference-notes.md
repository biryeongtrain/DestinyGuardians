# W70 — ADS 전환의 출처와 작성 범위

## 확인한 원작 자료

- [xHOUNDISHx Ammit AR2 플레이](https://www.youtube.com/watch?v=w3CYQprLoc0), 2022-09-01. W69에서 받은 최초65초의 12초 HIP /14초 ADS 장면을 다시 대조했다.
- [출처·개인 캐시 SHA](references/gameplay.json), [W69 영상 provenance](../w69/references/gameplay-provenance.json).
- HIP에서 오른쪽에 있던 총의 조준기가 ADS에서 화면 중앙에 오는 구도만 참고했다. 카메라·화면비·배율·움직임이 다른 두 프레임으로 정확한 궤적/시간을 측정하지 않았다. 모든57종의 원작 조준 영상을 조사했다는 뜻이 아니다.
- 사용자 Drive 원본 모델의 출처/geometry는 W30·W69 기록을 계승하며 이번 단계에서 새 rip/animation/texture를 받거나 추출하지 않았다.

## 작성한 전환

기존 W30 HIP/ADS display를 선형 Euler/translation/scale로 연결한21개의 정적 pose이다. LFR2종만 기존 W45 scope display를 끝점으로 사용한다. 실제 WeaponAiming 진행도를20단계로 내림해 고른다. 실제 원작 애니메이션 곡선, 손 IK, 클라이언트 렌더프레임 보간이 아니다. 조준 속도/이탈/스냅샷 배율/입력은 기존 서버 정책을 유지했다.

26.3의 실제 ItemModels.bootstrap에서 지원 타입을 확인했다([javap](references/26.3-item-model-types.javap.txt)). 이 경로에는 동적 display transform 타입이 없어 정적 모델 샘플을 쓴다. 다른 클라이언트 모드/별도 엔티티 방식 전체의 가능성을 부정하는 근거는 아니다.

## 미리보기와 한계

[단계 비교](../../../docs/qa/2026-10-24/w70/ads-transition-contact.jpg)는 Blockbench 별도 inspection문서의 ItemTransform을 적용한 offscreen렌더이다. 무기 종류별 공통 alpha bbox를 사용해 프레임 사이 이동·크기를 보존했다. 실제 Minecraft의 손, 카메라 투영, FOV, 리소스팩 bake, 클리핑은 재현하지 않는다. 활은 정적 반쯤 당긴 동일 geometry로 ADS축만 비교했다. production에서는 actual bow draw/nock가 독립 축으로 작동한다.

기존3 unsaved문서의 compile SHA/활성문서/edit모드/카메라를 복원한 뒤 이번 inspection탭2개와 offscreen을 닫았다. 삭제 MCP가 disposal후 onContextMenu 오류를 반환해 Preview.all을 독립 확인했다([복원 기록](../../../docs/qa/2026-10-24/w70/blockbench-restoration.json)).

**Minecraft native 화면·입력·실청취·bake메모리/FPS는 미검증**이다. W62의 사용자 승인 격리진단1회 이후 새 클라이언트는 시작하지 않았다.
