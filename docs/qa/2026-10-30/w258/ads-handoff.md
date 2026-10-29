# W257 ADS/model/wire GameTest 수정 인계

slot4 소유 20개 테스트 파일만 수정. 기존 139개 GameTest 메서드 이름/개수와 실행 annotation을 유지했으며 삭제·disabled·manual 전환 없음. main 및 제품 코드, 공통 TestPlayers는 수정하지 않음. 중앙 빌드/컴파일/GameTest/서버/클라이언트 실행 없음.

## 현행 계약과 수정 이유

- **좌클릭 ADS**: main `input/InputRouter.onPunch`, `weapon/WeaponAiming.toggle/requested/tick`은 좌클릭 토글과 3틱 quiet-gap을 사용한다. 기존 Shift 조준 입력을 실제 입력 라우터 호출로 전환했다. 동일 틱 진행 중복 방지와 토글 반전 간격을 지키며 Snapshot의 진입/기본 이탈 속도, 9틱 발사 간격, 소유권 이전, 사망/레벨/스왑 cleanup 검증을 유지했다. handling/reload 중 클릭은 소비되고 완료 후 자동 진입하지 않으므로, 완료 전 차단·완료 후 비조준·새 클릭 후 진입을 각각 검증한다. Shift-only 음성 대조군, 실제 crouch 및 검/글레이브 Shift 가드는 별도로 유지했다.
- **native zoom / FOV**: `WeaponAimMovement.update`, `WeaponNativeZoom.movementScalar`는 MOVEMENT_SPEED 하나에 `(1-progress)+progress*(baseAdsScalar/max(1,zoom))`를 적용하며 SNEAKING_SPEED를 중화하지 않는다. 외부 shader FOV를 변경하거나 ADS 취소 근거로 사용하지 않는다. 독립 수식, 실제 native 속성 패킷, 변경/정지 샘플의 dirty 여부와 객체 동일성, 외부 modifier/permanence 보존, missing-attribute, lifecycle/global cleanup을 검증한다. 실제 cinematic/native camera/super 차단 검증은 유지했다.
- **flinch**: `WeaponAiming.damaged/suspend`에서 suspend는 조준·No Distractions를 해제하지만 일반 장착 총기의 hip flinch 자격까지 제거하지 않는다. 이 경우 무반응 대신 실제 HP 손실에 따른 정확한 hip 회전량/패킷을 검증한다. 외부 shader FOV만 있는 경우에는 완전 ADS와 획득한 특성 및 정확한 flinch를 유지해야 한다. Shift packet은 특성을 끊지 않으며 실제 off-click/같은 틱 재클릭 debounce/새 20틱 특성 간격을 검증한다.
- **모델 경로와 wire**: `WeaponCombatItem.getPolymerItemModel/getPolymerItemStack`, `WeaponFirstPersonHands`, `WeaponAimPresentation.model`이 근거다. authored W201 JSON의 명시된 경로만 손 모델로 투영하고, sight W148/149/150/151/153/159 및 sniper W70 라우트를 명시적 테스트 oracle로 검증한다. 서버 ITEM_MODEL은 canonical, 전송본은 해당 projected route여야 하며 Polymer round-trip, 바이트 decode, 원본 불변, recipient/정확한 객체 소유권, raw/stale/nonselected 음성 대조군을 유지했다. W161 flag1은 live two-hand Ammit만 전송하고 나머지는 flag0만 전송한다.
- **reload/insert/bow selector**: `WeaponReloadPresentation.intervals/model/update/clear`, `WeaponInsertPresentation.intervals/model/tick`, `WeaponRuntime.startReload/updateBow`가 근거다. Beloved W208, Duke W215, Ammit W207, Long Arm insert W222 및 해당 60구간 선택자를 검증한다. 활의 실제 nock에서는 W222 reload가 W50보다 우선하며 float1 reload와 float2 bow는 독립적으로 진행한다. 종료/취소 후 float1=-1 및 원래 bow/canonical route 복귀를 검증하고 원본의 다른 모든 CMD 필드 불변을 유지한다. 모델 샘플은 실제 deadline/remaining의 float 연산 및 collision offset을 검증한다.
- **탄약 경계**: W93의 각 무기 credit/회복 경계·유한 reserve·지연된 donor cleanup 검증을 유지한다. `ReloadCreditProfile` 및 `w65-reload-credit.json`에 Beloved는 없으므로 W68에서는 조기 credit 부재를 명시하고, 완료 직전 rounds/reserve 불변과 발사 차단, 정확한 완료 시 이전을 검증한다.
- **reticle**: `WeaponReticleHud.update`는 physical sight 무기의 finite ADS >= .95에서 두 hip HUD를 제거한다. .94까지 수축·bloom·중심/객체 동일성을 검증하고 .95/1/finite extreme에서 두 노드 제거와 재생성 부재를 추가 검증했다. 비해당 sniper/LFR, NaN/infinity 정규화 및 owner-local cleanup 검증을 유지했다.

## 통합과 검증 상태

- `gametest-ads.patch`: main-baseline 기준 전체 unified patch. `patches/`는 파일별 patch.
- `result-manifest.json`: 파일별 baseline/result/current-main SHA256, patch SHA256, 139개 test method 목록, read-only main 계약 근거 파일 SHA256 포함.
- `changed-files.txt`: 변경한 소유 경로 20개.
- package-static 공통 helper는 소유 `WeaponGripGameTests`에 있다. 이 파일을 같은 그룹으로 통합해야 한다. TestPlayers 변경 요청 없음.
- tree-sitter-java 정적 구문 검사 20/20 통과. baseline/result의 GameTest method 목록 및 개수 동일 확인. main의 소유 20개 파일 모두 입력 baseline SHA256과 일치 확인.
- 컴파일/type-check/실제 GameTest 통과를 주장하지 않으며 master 중앙 검증이 필요하다. 이 범위에서 제품 수정 필요사항은 발견하지 못했다.
- 기존 GameTest 이름은 실패 로그 추적을 위해 유지했으므로 일부 역사적 이름의 crouch/FOV/pair 표현은 현재 본문 계약과 다를 수 있다.

- 보존된 main-baseline에서 `git apply --check` 통과. 실제 apply는 실행하지 않았다. master 전달 제품 commit: `852b713f`.
