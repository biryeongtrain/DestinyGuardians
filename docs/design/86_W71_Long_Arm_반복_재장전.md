# W71 — Long Arm 반복 재장전 시각화

## 실제 목표와 남은 차이

기존 Long Arm의 실제2발 삽입에 움직임이 없던 차이를 줄인다. 플레이 영상의 총 올림→기울어진 몸체 유지/반복 접촉→복귀를 실제 승인된 반복 reload 상태와 연결한다. **몸체 모션**이며 손/카트리지/레버 articulation은 아직 없다. 원작 animation clip/손 IK를 구현했다고 표현하지 않는다.

[출처·영상 차이](../../art/weapons/w71/reference-notes.md) · [QA](../qa/2026-10-24/w71/README.md) · [미리보기](../qa/2026-10-24/w71/long-arm-phases-contact.jpg).

## 실제 state와 phase

새 `WeaponInsertPresentation`은 Long Arm8293111만 지원한다. whole-magazine용 `WeaponReloadPresentation`에 가짜 단일전체시간을 넣지 않는다.

| Phase | CMD float4 | 실제 조건 |
|---|---|---|
| initial | 0..1 | 승인된 reload부터 첫20tick phase |
| loop | 2..3 | 실제 첫 삽입 성공 뒤, 다음13tick 반복 phase |
| return | 4..5 | 마지막 실제 삽입 후6tick 외형 복귀 |

- 각각21개 정적 sample,20TPS 실제 progress를 내림해 선택한다. 21tick 고정 애니메이션이나 render-frame 보간이 아니다.
- 첫initial끝=loop시작/끝=return시작으로 연결된다. 루프마다 HIP로 튀지 않는다.
- `WeaponCycle.finishReload`의 **실제 탄약 이동 성공**만 loop/return을 진행시킨다. getter/HUD/단순예상deadline으로 탄약/모션을 시작하지 않는다.
- 기존14발/첫20tick/이후13tick/2발씩·마지막한칸1발·무한Primary예비탄/유한탄창 정책을 보존한다. 발사 주기·Handling·음원도 변경하지 않는다.
- return은 visual tail일 뿐 `reloading/readyAt`를 늘리지 않는다. 실제 새 발사/재장전/ADS가 우선하며 즉시 중단한다. skill/slot/death/spectator/level/cleanup도 정리한다.

## 권한과 component

actual owner·level·exact ItemStack을검증한다. 실제start만 binding을만들며 copy/NBT/preview/저장 float4는권한이아니다. 늦은donor정리는recipient를건드리지않고반복이전은최초originalfloat를계승한다. saved/직전owner와live63sample이동등해캐시가남지않게작은offset을선택한다.
float4만일시사용하고원래값/부재길이를복원한다. float1wholemag/2bow/3ADS·higherfloat·grip/colors/strings/다른component를밀거나덮어쓰지않는다.
실제wire우선순위는 W71→실제wholemagreload→실제ADS→bow→scope→base. wrapper는first-person만바꾸고nonFP는원래graph그대로다. 원본ITEM_MODEL은identity로보존한다.

## 자산

[생성기](../../scripts/generate_insert_models_w71.py) · [manifest](../../art/weapons/w71/manifest.json) · [정적 inspection](../../art/blockbench/weapons/w71/long_arm_insert_inspection.bbmodel).
3phase×21pose×2grip=126parent/display모델+itemgraph1개. 새geometry/texture0, 원래256cube/UV보존·사용자상한유지. 현재패턴을다른shotgun등에일괄복제하지않는다. 원작손/장전방식마다추가참고가필요하다.

## 검증 경계

실제서버tick/승인입력/탄약/HUD/Polymerwire/취소와26.3codec/모델원본/phase끝점을나눠검사한다. GameTest/Blockbench는Minecraftnative키입력·화면·실청취·clientbake메모리/FPS증거가아니다. 전체무기/HUD목표는계속active다.
