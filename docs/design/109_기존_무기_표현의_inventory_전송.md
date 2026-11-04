# W93 — 기존 무기 표현의 inventory 전송 수선

상태: 최종gate5/6각809GT/681JUnit·8452pins/7013assets·native135PNG/25원본검사로전송경계수락. 활nock상단사각형W93-N1은미해결. W92수락은 W91의 이자나기/교체 표현에 한정됐으며 이 단계는 나머지 exact-object 모델 경계를 대상으로 한다. [작업 큐](../qa/2026-10-25/w93/parallel-work-queue.json).

## 실제 결함과 목표

`WeaponCombatItem`의 기존 Reload(Beloved/Duke/Ammit), Insert(Long Arm), Aim(기존 지원 무기), Bow(Biting Winds/Whispering Slab)는 원본 객체의 live identity로 모델을 선택한다. menu/SetSlot 복사 뒤 이 정보가 사라지는 W91과 같은 구조다. scope 문자열 wrapper는 복사에도 남으므로 scope를 새롭게 만들거나 권한을 바꾸지 않는다. 기존 자산/원작 참고 출처/탄약/장전·Handling 시간/모델 우선순위를 유지한다.

## 수선 계약

W92의 trusted native synchronizer 경계를 재사용한다. canonical ITEM_MODEL/선택 슬롯/서버 listener/RemoteSlot/공유 supplier는 불변이다. Aim/Bow/Insert는 기존 binding의 정확 owner와 active조건을 순수 조회한다. legacy Reload는 identity set만으로 owner를 알 수 없으므로 실제 WeaponRuntime State의 owner/level/stack/cycle과 현재 eligibility를 추가 확인한다. setter·bind·clock advance는 없다.

admission은 아무 owned route를 OR하지 않는다. 실제 모델 getter와 같은 우선순위 `Swap > Insert > Izanagi > Reload > Aim(sniper scope 예외) > Bow`에서 **첫 활성 route의 owner**만 확인한다. exact original이 donor/recipient 두 inventory에 alias되고 donor의 높은 route와 recipient의 낮은 route가 동시에 남은 경우, 낮은 route 소유권으로 donor 모델을 보내면 안 된다. Aim→Bow composite도 실제 Bow binding의 owner를 함께 확인해 donor Bow를 own Aim으로 수락하지 않는다. 객체복사나 CMD selector는 여전히 권한이 아니다.

## 검증 범위

리드가 W92의 실제 native PLAY encoder/no-context decode fixture를 그대로 재사용해 legacy incremental/full 전송을 시험한다. 자식은 owner/alias/cleanup 및 직접 native use 재전송 경계를 독립 검토한다. 최상위가 공유 수정·등록·실패원본 보존·직렬 강제2회·source/JAR/팩/캐시 고정 후 단일 취합 Vision으로 원본 PNG를 확인한다. 정적 진단·서버 getter·codec 통과만으로 화면이나 원음 청취를 수락하지 않는다.

아래는 구현 당시 검증 계약이며 최종 결과는 QA에 분리했다. Polymer의 use 재전송처럼 synchronizer 밖의 경계도 적용 여부를 확인하며, 실제 gap은 별도 수선/시험하거나 미해결 한계로 명시한다. legacy 전체가 이미 완성됐다고 주장하지 않는다.


## 병렬 리뷰에서 발견한 추가 경계

- **R1 조건부 사용 교정 패킷**: Polymer 0.18.4+26.3은 CONSUME 직후 같은 client tick 안의 두 번째 use/interact에서 main/offhand SetSlot을 직접 만든다. 일반 단일 use나 매 heartbeat의 필연적 재전송은 아니다. native `ServerCommonPacketListenerImpl.send(Packet, ChannelFutureListener)`의 packet 인자만 수선한다. 실제 emitting listener가 `player.connection`이어야 하고, 기존 projectSlot의 exact selected source/menu/serverthread/context/profile/connection/stale rejection을 모두 유지한다. stateId/slot/container/callback/순서 불변, offhand/커서/비선택/모르는 menu는 그대로다. raw Connection, codec/constructor, nested bundle 전체를 고치지 않는다.
- **R2 지연 정리**: Reload/Bow의 production acquisition/retirement는 정확 owner를 사용한다. 실제 A Runtime.State가 원본을 B에게 넘긴 뒤 늦게 취소되어도 B가 새로 취득한 binding을 제거하지 않는다. 기존 ownerless overload는 과거 test API로 남아 있고 production 호출은 owner-aware다. 세대 전체를 보장하는 범용 callback 시스템은 아니다.
- **R3 최초 프레임 diff**: 저장된 reload selector가 기존 i/20 샘플과 같으면 새 binding에 안정적인 `.001` cosmetic offset을 둔다. 최초 장전의 native RemoteSlot diff를 보장하되 `.05` 모델 샘플 간격과 authoritative cycle/ammo clock은 바꾸지 않는다. retirement는 기존 -1이다.

## 통합 시험 정의

새 10GT: legacy actual incremental/full wire 6, 실제 A→B Runtime reload/bow handoff+late cleanup 2, 실제 CONSUME→두 번째 use→ClientTickEnd 및 emitting listener/header/callback/stale/raw control 2. W92 실제 PLAY encoder/프레임/context-free client decode fixture와 기존799GT/681JUnit은 그대로다. 양손/기본 grip, sniper half-scope 예외, composite bow와 donor 우선route, 원본 component/ammo/canonical model, persist/copy/cleanup deadline을 확인한다.

각 강제 gate의 실패도 삭제하지 않는다. gate1/2는 새 test 컴파일 문제, gate3/4는 새 fixture/oracle 가정 오류였고 제품 코드를 맞추기 위해 기존 assertion을 약화하지 않았다. 최종 gate와 native 수락은 [QA 결과](../qa/2026-10-25/w93/README.md)에 별도 기록한다. 이 문서의 코드 계약만으로 실화면·원음 청취·원작 동작과의 완전 일치를 주장하지 않는다.

W93-N1 후속: [L1/L2 검토](../qa/2026-10-25/w93/native-review-lead.md)상 눈 위치에서 시작하는 일반 활 trail dust가 유력하지만 미확정이다. native bow-nock polish 수락은 보류한다. 별도 W94에서 particle-only 격리 비교 후 수정 여부를 결정한다.
