# 108. Inventory wire 모델 투영 — W92

상태: 최종 gate3/4 자동시험 통과 / native attempt2의 W91 대상 범위 **시각 수락** / 실제 다운로드 캐시 감사 통과. [QA](../qa/2026-10-25/w92/README.md).

## W91에서 드러난 결함

게임플레이와 모델 bank 검증은 통과했지만 실화면은 장전 중 원래 HIP, 교체 STOW 중 incoming 무기를 보였다. 실제 menu supplier/SetSlot constructor가 ItemStack을 복사해 exact-identity model binding이 사라졌다. FullContent는 menu에서 이미 복사된다. source/JAR/cache hash와 서버 model getter는 클라이언트가 선택한 모델을 증명하지 않는다.

## 수정

`WeaponContainerSynchronizerMixin`은 ServerPlayer native synchronizer가 SetSlot/Content를 생성하는 마지막 outbound 인자만 바꾼다. `WeaponOutboundPresentation`이 recipient의 실제 선택 inventory slot 원본을 검증해 Polymer vanilla carrier를 만들며, 그 뒤 packet은 안전하게 복사할 수 있다.

권한은 server thread·현재 menu·정확 inventory/selected slot·mainhand original identity·실제 W91 binding의 owner/level/runtime·connection/profile에서 온다. snapshot equality는 오래된 데이터 거부만 한다. 기존 `active(copy)`는 계속 false다. 서버 ITEM_MODEL/탄약/각종 component/slot/listener/RemoteSlot/공유 supplier/Handling 시간은 바뀌지 않는다. carried/cursor, donor, 대체복사, 다른 slot/menu는 투영하지 않는다.

범위는 W91 Swap/Izanagi만이다. 이전 identity-bound route들의 다른 경계는 별도 후속이며 이 패치가 모두 해결했다고 하지 않는다.

## 시험 구분

1. 신뢰 경계4GT: 유효 recipient/original, stale/wrong slot/menu/donor/replacement, missing context/level, 고정 payload와 cleanup.
2. wire4GT: 실제 native Connection/PacketEncoder/Fabric context, menu broadcast/full-content, framing 후 no-context client semantics decode. 일반/Honed61tick/유료발사/ADS, 양방향·양 carrier STOW→READY→종료, queued old frame 뒤 취소 상태 순서를 확인한다.
3. 기존 자동시험은 보존했다. gate1은 새 fixture의 HANDSHAKE→PLAY 전환 누락으로 새 wire4GT가 실패했다. gate2는 새 oracle의 Primary reserve/이자나기 pose 기대2건이 실패했다. 새 fixture/oracle만 기존 계약에 맞췄으며 제품·기존 assertion·타이밍·packet/model 검사는 바꾸거나 제거하지 않았다. [gate1 진단](../qa/2026-10-25/w92/master-gate1-diagnosis.md)과 [gate2 진단](../qa/2026-10-25/w92/master-gate2-diagnosis.md), 각 실패 원본을 보존한다.
4. 최종 강제 재검증 gate3와 gate4는 **각각 799GT + 681JUnit 통과, failure/error/skip 모두 0**이다. 기존791GT·681JUnit을 보존하고 W92의 신뢰 경계4GT와 wire4GT를 추가했다. [gate 집계](../qa/2026-10-25/w92/gate-summary.json)와 [QA 원본 링크](../qa/2026-10-25/w92/README.md)를 근거로 한다.
5. 바이트 검증도 framebuffer 검증은 아니다. native attempt1은 시작 차단으로 world join·PNG·캐시 수락 증거를 얻지 못했다. 사용자의 awake/unlocked 확인 후 **한 번의 제한된 attempt2가 정상 접속**했다. 실제46PNG/원본15개 직접검사로 일반·Honed 탄창/기울기·강화 총신 cue와 유료 발사 후 제거·기존3D ADS·Austringer↔Beloved outgoing STOW/incoming READY를 W91 대상 범위에서 수락했다. source/JAR/native팩/실제 캐시8442pin·7013asset 감사도 통과했다. [시각 리뷰](../qa/2026-10-25/w92/native/attempt-2/visual-review.json)와 [보관본 감사](../qa/2026-10-25/w92/runtime-native-archived-final.json)를 분리한다. native Q/CtrlQ/slot 미지원·청취 미실행은 별도다.

## 고정 산출물

gate3/4의 동일 고정 JAR은 `build/libs/destiny-guardians-0.1.0+26.3.jar`이며 SHA-256은 `4a8a55f92cc5e810468db7d25cc18a47f90afe4daf590ecf47ad8269733f53a1`이다. [gate3 해시](../qa/2026-10-25/w92/gate-3-jar.sha256)·[gate4 해시](../qa/2026-10-25/w92/gate-4-jar.sha256)·[headless 산출물 기록](../qa/2026-10-25/w92/runtime-headless-final.json)에 연결한다. 이 JAR 고정과 실제 시각·캐시 증거는 별도로 기록했다. 다른 legacy route·청취·다인·정확 원작 모션 완료는 주장하지 않는다.

## 한계

fixture는 disposable login-equivalent metadata이며 실제 socket 인증·압축·암호화·bundle reassembly·client inventory hash roundtrip을 인증하지 않는다. 유효 send-time snapshot을 이미 전송했다면 소급 제거할 수 없다. 이후 cleanup/current-state update가 순서대로 뒤따라야 하고, 그 snapshot에서 binding을 복원하지 않는다.

## 후속 W93

이문서는W92당시W91범위의역사적수락기록이다. 기존Reload/Insert/Aim/Bow및conditionaldirect-use전송은[W93](109_기존_무기_표현의_inventory_전송.md)에서별도수선·809GT/681JUnit강제2회·native135PNG로확인했다. W93-N1활nock시각결함은새미해결이다.
