# W258 run2 reload 후속 수정

현재 main을 파일별 baseline으로 보존하고 slot5 소유 세 테스트만 반환한다. 이미 통합된 scheduling 4파일은 포함하지 않는다. W63은 이전 extra-reload 전달본과 동일한 미통합 9행이며 개별 patch도 제공한다.

- RecluseReloadW100: WeaponCombatItem.modifyBasePolymerItemStack는 Ammit 양손에만 [grip, crouched]를 전송한다. WeaponCrouchPresentation.supports/update는 Ammit 양손과 실제 owner.isCrouching()을 사용한다. 기존 [grip] 전용 비교를 fixture의 Ammit ID/양손 여부와 실제 소유자 자세로 정확한 전체 flags 목록 비교로 고쳤다. floats/strings/colors, server stack 불변, 패킷 프레임 및 장전 시점 검증을 유지했다.
- DemolitionistW103: WeaponRuntime.available는 GrenadeThrow.active 중 false, ammunition은 empty이며 AmmoHud.update는 전체 ammo prefix HUD를 제거한다. GrenadeThrow의 접촉은6틱, 복귀는20틱이다. 시전 전0/2 glyph를 실제 생성하고, 기존 T5 무지급·T6 최초 projectile/refill 관찰·T8 실탄약2/0/총량 보존을 그대로 유지한다. T8에는 전체 ammo HUD 부재도 검사한다. setup에서 사전등록한 T21은 END_SERVER_TICK의 T20 복귀 뒤 비활성/탄약보존과 기존 정확한2/0 glyph assertion을 검사한다. maxTicks25 유지, nested scheduling 없음.
- ReloadAudioW63: 수평 eye만으로는 확률 분산 이후 precision을 보장하지 못한다. seed 고정 후 실제 WeaponAiming.direction 샘플의 Husk AABB 교차/WeaponPrecision.critical을 검사하고 같은 seed를 paid emission으로 재사용한다. 실제1발 소비/실제 사망/선택 Outlaw120틱 및 비선택 대조군 유지. 원본 Duke59, Outlaw33, credit fraction .71로 지급24/42와 전체 clip/recovery33/59는 서로 다르다. 시간 기대값과 T32/33/58/59 검증은 변경하지 않았다.

제품/common TestPlayers/main 변경, 빌드, 컴파일, 런타임 실행 없음. 세 파일의 GameTest 개수 동일. 중앙 재실행은 master 담당이며 통과를 주장하지 않는다.
