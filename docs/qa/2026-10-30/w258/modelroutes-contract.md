# W258 modelroutes 반환

- 소유한 Java 27개만 수정했다. 기존 GameTest 145개의 메서드명·등록 annotation·timeout·environment를 모두 보존했다. 비활성화나 수동 실행 스위치는 추가하지 않았다.
- 서버 `ITEM_MODEL`은 canonical 식별자다. Polymer wire는 authored 경로를 `weapon_hands_w201/`로 감싼다. main의 `WeaponGripGameTests.projected` / `wireFlags`를 사용해 이 두 계약을 분리했다. 서버 canonical 유지, 원시 carrier/충전 상태, CMD 독립 슬롯 검증은 유지한다.
- `MagazineReloadW114GameTests.expectedReloadRoute`에 현재 53개 authored 경로 표를 명시했다. W164~W189 테스트는 이 표를 공유하고, production `model()` 반환값을 기대값의 유일한 근거로 삼지 않는다. 허용 대상 43→53 확장은 W219~W222 신규 대상 10개를 명시한 결과이며, 나머지 catalog와 null 거부 검증도 남겼다.
- W114 selector 기대값은 현재 authored 61포즈에 맞춰 60구간으로 변경했다. 서버 시각·획득 offset·HUD 8단계·RemoteSlot 중복 억제·다른 수신자 거부·NBT 복사본·탄약 잔고 검증은 보존했다. Ammit 양손 wire의 추가 crouch flag도 정확히 비교한다.
- 6개 baseline 장전 종료 시각은 `w46-timing.json`에 따라 Blast Furnace/Recluse 43, Hammerhead 91, Beloved 62, Duke 59, Ammit 41틱으로 고정했다. `w65-reload-credit.json`의 Duke .71 / Hammerhead .65만 적용하므로 지급 시각은 각각 42/60틱이고 다른 4개는 종료 시각이다. production 시간 계산을 다시 호출해 자기 검증하지 않는다. Blast Furnace 36발 / Hammerhead 57발 baseline도 명시했다.
- Ace는 W157 source 경로를 유지하며 손 래퍼만 반영했다. First In Last Out은 W208 insert, Mindbender는 W221 insert를 명시했다. 기존 15/16틱 지급, 6틱 cosmetic return, 사격 중단, 실제 reserve 차감 및 sentinel 복원 검증은 유지한다.
- 취소·완료·저장 selector·복사본의 wire 검증은 단순히 reload 모델과 다르다는 비교 대신 정확한 idle 손 래퍼 일치를 요구한다. 새 경로와 다른 잘못된 모델도 통과시키지 않는다.

## 통합·검증

`baseline-to-result.patch`는 제공된 baseline에서 결과로의 변경이며 27개 경로를 한 번에 통합해야 한다. `hash-manifest.json`에 baseline/result/main 현재 SHA-256 및 145개 등록 메서드 목록을 담았다. 반환 시 main의 27개 해시는 모두 baseline과 일치했다.

main에 이미 완료된 `WeaponGripGameTests.projected(Identifier)`와 `wireFlags(ItemStack)`에 의존한다. 재사용 슬롯의 비소유 helper는 이전 버전이라 해당 메서드가 없으며, 소유권을 지키기 위해 수정하지 않았다. master는 현재 main에 이 패치를 통합해 검사하면 된다. `WeaponInsertW71GameTests`로 위임하는 기존 등록 테스트도 그대로 유지했다.

정적 검사: 53개 경로의 authored item/wrapper 및 61개 threshold 대조, insert 2개의 183개 threshold 확인, 등록/annotation 보존, Java 구분자 균형, 소유 경로 `git diff --check`, baseline `git apply --check` 통과. 컴파일/Gradle/GameTest 실행/Vision/CU는 지시에 따라 수행하지 않았다. 런타임 통과를 주장하지 않으며 중앙 실행은 master 담당이다. main/src/main 수정, commit/reset/stash/clean/push, 자식 agent 생성은 하지 않았다.
