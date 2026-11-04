# W191 Pugilist

- 기준: DDC **Weapon Perks 170행**, 이름 셀을 `Pugilist`와 정확히 일치시킨 오프라인 HTML. 기본 특성 `691659142`만 사용한다. 강화 `536173722` 및 ↑11%/↑22%는 제외한다.
- 무기 처치: 전체 authored 근접 능력 쿨다운의 **10%**, 융합 소총·월도·산탄총·저격총은 **20%**. Minecraft 환산은 `ceil(fullCooldownTicks × percent / 100)`, 남은 쿨다운을 0까지 줄인다. 현재 등록된 같은 클래스의 `MELEE` 능력만 허용한다. 실시간 Destiny 능력 등급/스탯별 재생량을 재현했다는 뜻은 아니다.
- 실제 근접 피해 후 **+35 Handling, 3초 = 60틱**. 입력 수락만으로 발동하지 않는다. 무기를 내리거나 편집하면 버프·대기 근접 토큰이 취소된다. 이미 지불한 발사체는 여전히 소유한 원본 무기만 참조한다. 사체는 원본 세션 전체에서, 접촉은 수락한 근접 토큰/대상별로 중복 제거한다.
- 고정 공식 manifest **245114.26.10.13.2000-1-bnet.66137**: Ammit AR2 소켓4 `560115158`, Mindbender’s Ambition (Adept) 소켓3 `1732284294`, Dimensional Hypotrochoid 소켓4 `1092097342`. 카탈로그 65종을 검사해 이 3개만 승인한다. 소켓 범주 `4241085061`, 실제 randomized pool, `currentlyCanRoll=true`, 기본 Trait 조건을 적용한다.
- 합법 구현 동반 퍽: Ammit은 Triple Tap / Stats for All / Surplus, Mindbender Adept는 Swashbuckler, Dimensional은 Stats for All / Threat Detector. Ammit의 Adrenaline Junkie와 Mindbender의 Snapshot·Threat Detector는 같은 소켓이므로 조합하지 않는다. 전체 공식 풀은 JSON의 socketProof에 보존한다. Well-Rounded·Steady Hands 등 미구현 퍽 효과를 새로 만들지 않는다.
- 원시 Handling/ADS 곡선은 기존 W43 매핑과 W46 `weapon_formulas.json`의 역사적 d2foundry oracle `dcd0c7d302b056ffbb532edcb711d724a17ca8c1`에서 추출했다. 공식 기본 Handling에 Pugilist와 합법 활성 동반 보너스를 합산, 0..100 제한, 원시 초 곡선, 합법 Threat Detector 핸들링 배율, 마지막 1회 ceil 순서다. TD ADS 배율은 없다. 이 3개에는 합법 Snapshot이 없다. 기존 W58/W44 기본 시간과 추출 시 대조한다. 현재 Destiny 애니메이션을 새로 실측한 값이 아니다.
- 재생성: `rtk proxy python3 scripts/build_pugilist_w191.py`, 읽기 검증: 끝에 `--verify`. 원시 DDC 행 HTML·입력 SHA-256·공식 소켓 증거를 런타임 리소스와 `source.json`에 보존한다. 네트워크 갱신이나 런타임 해시 gate는 없다.
- master 연결: 지불 후 `capture` → 실제 처치 `killed`; 근접 수락 `meleeAccepted` → 실제 피해 `meleeConfirmed`. `handlingBonus(p)`는 활성 시 35, 미발동·만료·소켓 해제 시 0을 반환하는 순수 조회다. 최종 handling/ADS 계산을 이 구현으로 감싸고 outgoing stow 시간을 읽은 뒤 `stowing`을 호출한다. 매틱 `update`, 실제 편집 `edited`, 소유권 변경 `changed`, 퇴장/생명주기 `cleanup`/`clear`가 필요하다. 공유 registry/runtime/HUD 파일은 이 작업 소유가 아니다.
- 검사 범위: 신규 타이머·정확한 만료·중복 콜백·stow epoch·시간 역행을 `PugilistCycleW191Test`로 작성했다. 오프라인 targeted Gradle 시도는 GCB-server 아티팩트 캐시 부재로 구성 단계에서 중단되어 컴파일/테스트가 실행되지 않았다. 재생성 `--verify`는 통과했다. 단순 숫자 mirror 테스트·전체 suite·게임/Vision/UI는 수행하지 않는다. 통합 컴파일·targeted 테스트·실제 피해 dispatch 연결은 master 확인 사항이다.

- Master 통합 보정: 처치 dedup은 source 세션 전체의 영구 UUID 집합 대신 개별 paid token의 corpse identity ledger를 공유한다. 발사체가 끝나면 ledger도 회수되며 세션이 평생 처치 기록을 보관하지 않는다. 실제 근접 에너지 회복 시 기존 CombatHud를 즉시 갱신한다. 타이머 테스트는4개이며 원본 worker의 cross-token ledger 테스트는 이 정책에 맞춰 제거했다.
