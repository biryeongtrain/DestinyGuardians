# W64 — Duke Mk.44 실린더 재장전

## 이번 구현

Duke Mk.44의 실제 1인칭 장전 영상을 참고해 **총구 올리기 → 왼쪽 실린더 열림 → 보충 대기 → 내려 닫기 → 원래 자세 복귀**를 추가했다.
원작 리그를 추출한 것이 아니라 정적 무기 모델에 맞춰 작성한 근사 모션이다.

- 기존 232개 큐브·면·UV·텍스처는 그대로: 몸체211 + 실린더21.
- 연결 요크2개만 추가: 동시 **234큐브**, 사용자 한도256 이내.
- 실제 서버 재장전 진행도 float1을 21샘플에 연결. Outlaw 가속도 같은 실제 phase를 따른다.
- native/twohand 보상과 양손 컨텍스트 지원. 왼손은 바닐라 반사 변환을 따른다.
- 실제 승인된 ItemStack identity에만 wrapper 적용. 저장한 progress/복사본/미리보기로 활성화할 수 없다.
- 완료·교체·스킬·궁극기·사망·cleanup 시 원래 wire 모델로 복귀한다.
- 3인칭·GUI·드롭·비활성 fallback은 원래 item graph. Beloved W47도 그대로 유지.
- 새 효과음 없음. W63의 시간 맞춤·소스별 취소를 그대로 이용한다.

## 원작 근거와 차이

[영상·모델 출처와 관찰](../../art/weapons/w64/reference-notes.md) ·
[선택 Duke 프레임](../../art/weapons/w64/references/duke-selected-contact.jpg) ·
[기계 판독 참조 manifest](../../art/weapons/w64/references/manifest.json).

Rin 영상의 Duke25.4–28.4초를 조사했다. 메인도 선택 프레임을 직접 확인했다.
큰 실린더 하우징이 화면 왼쪽에 **연결된 채** 열리고 총구가 올라간다.
하우징 전체 분리·교환 또는 개별 탄 삽입은 이 자료로 확정하지 않는다.
Austringer도 조사했지만 내부 탄약 유닛의 세부 동작을 Duke에 추정 이식하지 않았다.

피벗 `[8,10.2,5.17]`, 실린더 Z80°, 몸체 약62/65°와 정규화 구간은 **작성한 값**이다.
샘플 수·보간·요크 형상도 원작 추출값이 아니다. 손/IK/로더/탄 개별 배출은 없다.
원작의 빠른 손동작을 모델만으로 완전히 재현한 것은 아니다.

### 아직 남은 탄약 보충과 복귀 구간의 분리

원작 영상의 탄약은 **27.10초 7/107 →27.20초 9/105**로 바뀌지만 손·복귀는 그 뒤에도 이어진다.
현 서버는 기존 W46/W62 정책대로 재장전 deadline에 탄약을 지급하고 모션을 해제한다.
따라서 **원작처럼 보충 뒤 별도 복귀 tail을 유지하는 시스템은 이번에 구현하지 않았다.**
기존 취소/탄약/사격 타이밍을 근거 없이 바꾸지 않았으며 후속 과제로 분리한다.
영상의 부분 장전·역사적 수치·Outlaw 미확인 상태를 현재59/33tick의 실측 근거로 쓰지 않는다.

## 에셋과 편집

- [생성기](../../scripts/generate_reload_models_w64.py): `--verify`는 읽기 전용.
- [파트·피벗·87에셋 manifest](../../art/weapons/w64/manifest.json).
- [현재 구현 pin](../../art/weapons/w64/implementation.json).
- [Blockbench 검사 프로젝트](../../art/blockbench/weapons/w64/duke_reload_inspection.bbmodel).
- [모델 단계 모음](../qa/2026-10-24/w64/blockbench-pose-contact.jpg).

Blockbench MCP에서 새 검사 프로젝트를 만들고 원본 큐브/UV와 실린더 분할을 확인했다.
별도 offscreen view로 열린 상태와 생성 display의 6단계를 렌더했다. 사용자 카메라는 바꾸지 않았다.
검사 bbmodel은 원본 좌표계의 정적 그룹이며 재생 애니메이션 파일이 아니다.
네이티브 project codec이 소수 좌표를 반올림하므로 **production 생성 입력으로 쓰지 않는다.**
게임 에셋은 원본 JSON의 정확한 좌표/UV에서 생성한다.

## 검증과 실행 경계

**동일 JAR로 전체 강제 빌드2회: 각각503 GameTest /455 JUnit, 실패·오류·skip0.**
기존496GT/446JUnit 유지, 신규7GT/9JUnit.

- 실제 reload 승인·정규화 진행도·wire wrapper·HUD·완료 및 취소/사망/교체/소유자 분리.
- 실제 NBT 저장/복사한 progress가 유령 장전이나 wrapper를 만들지 않음.
- 26.3 ItemModels codec/Cuboid parser로87에셋 확인.
- 독립 원본 SHA·232큐브/UV 보존·234예산·양손/native/twohand·고정 피벗 강체 회전.
- 원래1451개 asset bytes 보존. 현재792개 client resource와 JAR/생성팩 확인.
- 생성기 읽기 전용/복제 트리/네트워크·쓰기 금지 양성, 입력변경/누락/출력변경 부정3개 거절.

[QA 결과와 한계](../qa/2026-10-24/w64/README.md).
GameTest/codec/Blockbench는 Minecraft 실제 화면·마우스/키 입력·실청취의 증거가 아니다.
W62에서 승인된 격리 진단1회는 이미 소비했다. 이번 추가 Vision/일반 QA 기동·배포는 없다.
현재 모션 지원은 **Beloved와 Duke 두 종류**이며 다른 무기 장전·손/IK·원작 tail·실게임 검증은 남는다.
