# W69 — Ammit AR2 개별 재장전

## 목적

특성 수만 늘리기보다 무기를 직접 다루는 시각적 완성도를 보강한다. 기존 Beloved/Duke에 이어 Ammit AR2에 개별1인칭 모션을 연결한다.

- 총을 들어 측면을 보여주기 → 하부 탄창 당김 → 삽입 → 강한 체결 움직임 → HIP 복귀.
- 199개 원래 큐브와 면/UV/texture 보존, 동시199큐브로 사용자 상한256 이내.
- 실제 승인된 reload identity만 progress float1로21샘플을 선택한다. 저장/copy/OPpreview의 수치로 유령 reload를 만들지 않는다.
- 실제 captured reload duration에 비례하므로 기존 시간 보정도 같은 phase를 따른다. 발사/재장전 비용·기본시간·Primary 무한예비탄·취소·보충 deadline은 바꾸지 않는다.
- 1인칭 좌/우 + native/twohand 보상. 다른 context와 비활성 graph는 기존 item graph 그대로.
- 기존 소리와 HUD가 사용하는 실제 reload state에 연결하며 별도 시계나 장식용 탄약 상태는 만들지 않는다.

## 출처와 한계

[영상/모델 근거](../../art/weapons/w69/reference-notes.md) · [원본 검사](../../art/weapons/w69/references/original-model-audit.md).
원본에는 분리된 정적 Magazine mesh가 있지만 rig/action이 없다. 원형 액체 창은 고정하며 하부 탄창만 분할한다.
영상의 몸체 기울임/손 접촉은 확인했으나 전체 탄창 이동 경로는 가려져 있다. 회전/위치/구간은 근사 모션이다. 원작 animation rip이나 정확한 궤적 재현으로 주장하지 않는다.
110발 특성이 적용된 역사적 영상으로 기본 탄창·현재 장전시간·early credit을 추론하지 않는다.

[생성기](../../scripts/generate_reload_models_w69.py) · [에셋 manifest](../../art/weapons/w69/manifest.json) · [검사 프로젝트](../../art/blockbench/weapons/w69/ammit_reload_inspection.bbmodel).
`--verify`는 출력을 재구성해 byte를 비교하며 쓰지 않는다. 기존 source 모델과 texture는 입력 전용이다.

## 검증

[QA 기록](../qa/2026-10-24/w69/README.md)에서 강제 빌드·실제 서버 state/Polymer wire·26.3 parser·geometry/UV·생성팩·앱 보존을 구분한다.
W62 격리1회 진단 이후 추가 Minecraft client는 시작하지 않았다. Blockbench render는 실제 게임 화면이 아니며 손/IK, 실제 시야 내 노출·클리핑·실청취는 미검증이다.
전체 목표는 계속 진행 중이다. 다른 무기 개별 장전, 손/IK, 연속 ADS, 원작 보충 이후 tail, 실제 화면/입력/소리 검증은 남는다.

### 최종 결과

강제 Gate1/2/3 각546required GameTest·510JUnit 통과. 최종Gate2/3동일JAR 확인, 기존540GT/502JUnit 유지+6GT/+8JUnit.
395현재소스pin·888clientresource·18server-only·258mainclass, 원래1725sourceasset/1595clientasset·542무기/황금총·165Ogg불변.
Blockbench 검사 프로젝트는 정적 그룹이며 별도 애니메이션 리그가 아니다. 원래3개 unsaved 프로젝트의 compileSHA·활성문서·edit모드·카메라를 확인해 복원했다.
