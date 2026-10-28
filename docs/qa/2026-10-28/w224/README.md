# W224 발사·장전 시 무기 재장착처럼 보이는 현상 조사

2026-10-28. 사용자 질문에 대한 해결안 조사만 수행했다. 제품 코드·팩·리그 변경, 빌드 및 Vision 실화면 검증은 수행하지 않았다. W223 수락 상태를 변경하지 않는다.

## 확인한 사실

- 대상은 Minecraft 26.3, 서버사이드 Polymer 무기다. 로컬 실제 `minecraft-client.jar`의 `javap -p -c` 결과를 읽었다. 예전 `ItemInHandRenderer` 이름으로 동작을 추정하지 않았다.
- `FirstPersonHandsAndItems.shouldInstantlyReplaceVisibleItem`: 컴포넌트 비교로 즉시 교체 가능한 경우 외에도 **새 아이템 모델 루트의 `hand_animation_on_swap=false`이면 표시 스택을 즉시 교체**한다. 컴포넌트 변경 자체가 항상 손 내림을 일으킨다는 설명은 틀리다.
- 현재 `w201-first-person-hands.json`에 등록된 297개 모델 루트를 실제 파싱했다. 누락0, 297개 모두 위 설정 false다. 단순히 이 설정을 추가하는 것만으로 해결했다고 할 수 없다.290개는 `swap_animation_scale` 생략으로 기본1,7개는0이다. 개별 경로·현재 해시는 `root-properties.json` 참조.
- 별도 경로: `Minecraft.startUseItem`은 사용 성공 결과에서 `LocalPlayer.itemUsed`를 호출한다. 이는 `FirstPersonHandsAndItems.itemUsed`로 연결되어 손 높이를0으로 초기화한다. 이 초기화는 위 교체 억제 옵션과 별개다.
- `FirstPersonHandsAndItemsRenderer`는 내림 변위를 `swapAnimationScale * (1 - lerp(oldHeight,height))`로 계산한다. 따라서 모델 루트의 `swap_animation_scale=0`은 이 손 내림 변위를 없앨 수 있다. 이 사실은 실제26.3 바이트코드로 확인했으며, 사용자가 본 현상의 원인을 실화면에서 확정했다는 뜻은 아니다.
- `WeaponCombatItem.getPolymerItem`은 양손 설정에 따라 crossbow/stick을 선택한다. 발사·장전 모델 라우팅 때문에 이 둘을 매번 바꾸는 코드가 아니다. `modifyBasePolymerItemStack`은 양손에charged projectiles, 한손에NONE consumable을 투영한다. 입력 의미를 보존해야 한다.
- `getPolymerItemModel`은 live reload/insert/swap/aim/bow/scope 루트를 고른다. `WeaponFirstPersonHands.project`가 그 결과를 손 모델 루트로 감싼다. `WeaponItems.save`는 실제 탄약 상태와lore를, `WeaponReloadPresentation`은 CMD float1을 갱신한다. 서버 탄약 저장을 제거하거나 위조해서 문제를 숨기지 않는다.

## 권장 수정 순서

1. 대표 양손총과 한손총에서 연사·장전 시작/끝·ADS 왕복을 캡처하고, 기본 손 내림과 모델 자체의 순간 점프를 구분한다. 컴포넌트·모델 ID와 발생 시점도 함께 기록한다.
2. 무기 표시 루트에 `hand_animation_on_swap=false`와 `swap_animation_scale=0` 정책을 일관 적용하는 방안을 우선 검증한다. 서버 전투·탄약 로직, 61 pose와 원본 손 리그는 보존한다. 발사 반동과 장전 자체 모션만 남기는 방향이다.
3. **실제 무기 교체도 기본 내림이 줄어든다.** 일괄 적용 전 이 영향을 검수한다. 기존 `WeaponSwapPresentation`의 자체 STOW/READY는 현재 Austringer/Beloved/Ammit/Recluse 네 무기 조합에 한정된다. 다른 무기까지 기존 교체 연출이 보존된다고 가정하지 않는다. 필요하면 실제 교체 전용 표시 루트·자체 모션 또는 동작 중 억제 루트와 복귀 시점을 설계한다.
4. 그래도 튀면 idle/reload/ADS 경계의 첫·끝 pose, 팔 표시, 변환 좌표를 맞춘다. 장기적으로 무기별 고정 ITEM_MODEL 아래 CMD 상태 분기를 통합하면 경계 관리를 단순화할 수 있지만, 루트 통합만으로 사용 성공 시 손 내림이 사라지지는 않는다.

## 검증 범위와 한계

소스와 실제 26.3 클라이언트 바이트코드 확인, 297개 루트 파싱만 수행했다. 사용자가 본 화면의 단일 원인 확정이나 수정 완료 보고가 아니다. `swap_animation_scale=0`은 교체·사용 내림에 대한 옵션이며, 서버 약20Hz에서 정적 모델 pose가 바뀌는 단계감이나 진짜 연속 보간을 해결하지 않는다. BetterModel 엔티티 보간과도 별개다.

리그·장전 pose를 변경하는 후속 배치에는 기존 Blender 확인 → 61 pose → 1차 Vision → 담당 agent 피드백 → 2차 Vision 순서를 적용한다. 표시 메타데이터만 수정하면 리그를 변경했다고 기록하지 않고, 대표 동작과 진짜 hotbar 교체를 실화면 검수한다.

## 코드 근거

- `scripts/build_first_person_hands_w201.py`의 루트 래핑 정책.
- `src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java`.
- 같은 패키지의 `WeaponFirstPersonHands.java`, `WeaponItems.java`, `WeaponReloadPresentation.java`, `WeaponSwapPresentation.java`, `WeaponOutboundPresentation.java`.
- 로컬 client JAR: `/Users/qf/.gradle/caches/fabric-loom/26.3/minecraft-client.jar`.
- client 클래스: `net.minecraft.client.player.FirstPersonHandsAndItems`, `net.minecraft.client.renderer.FirstPersonHandsAndItemsRenderer`, `net.minecraft.client.renderer.item.ItemModelResolver`, `ClientItem$Properties`, `net.minecraft.client.Minecraft`, `net.minecraft.client.player.LocalPlayer`.

읽기 전용 sidecar 감사도 캐리어 고정·탄약/CMD 변경·297개 루트 설정을 독립 확인했다. 실제 ITEM_MODEL은 canonical 값을 유지하고, 수신자에게 보낼 모델 경로를 Polymer와 outbound presentation에서 선택한다. 이는 실제 인벤토리 무기를 매번 새 객체로 교체한다는 뜻이 아니다.
