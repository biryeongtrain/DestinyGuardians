# W322 batch C 무기 특성

대상: 창세(Genesis), 분해성 파괴 장치(Disruption Break), 방어막 교란(Shield Disorient), 에너지 전송(Energy Transfer),
백열(Incandescent), 적응형 탄약(Adaptive Munitions), 서리 도둑(Rimestealer), 결정체 시체꽃(Crystalline Corpsebloom),
사격 전리품(Shoot to Loot), 방향 전환(Redirection), 원투 펀치(One-Two Punch), 맥박 모니터 205890336 별칭.

- 데이터: `src/main/resources/destiny/weapons/w322-batch-c.json`, 한국어 라벨 `w322-batch-c-ko.json`
  (Bungie ko manifest 245114.26.10.13.2000-1-bnet.66137). 재생성/검증: `rtk proxy python3 scripts/build_batch_c_w322.py [--verify]`.
- 수치: DDC Weapon Perks 탭 PvE 기본값(행 9/60/73/85/108/126/156/172/182/191/196/197, 원문은 JSON `ddcText`).
  `?`/빈값과 원작에 없는 Minecraft 환산은 JSON `localPolicies`에 명시한 로컬 정책이다.
- 공용 코드(combat 패키지): `CombatantShields`(방어막 원소·파괴 감지), `CombatantRank`, `DamageVulnerability`(속성별 독립 만료·곱연산 스택),
  `StasisStatus`(빙결), `StasisCrystals`(시공 수정 생성·파쇄), `FrostArmor`(서리 방어구). 다른 활동/능력도 재사용한다.
- 연결 지점: `WeaponRuntime` DamageTraits 끝 컴포넌트 `batchC`, `apply()` 전/후 1회씩, 히트스캔 선분, 폭발 중심, tick/stow/cleanup/clear;
  `WeaponPerks` 풀/ids/이름/edited; `WeaponPerkCommands.changed`; `MeleeWeaponTraits`(원투 펀치); `PlayerDamageMixin`(에너지 전송);
  `LivingEntityMixin`(서리 방어구 피해 감소); `AmmoEconomy.collectAlong`(사격 전리품); `PulseMonitorProfile`/`WeaponRecoveryHandling`(별칭).
- 미구현/한계: 힘의 보주 시스템 부재(사격 전리품의 보주 부분 비활성), 수호자(PvP) 방어막 미모델링, 시공/칼날 원소 피해 부재(수정 파쇄는 물리),
  파동 프레임 파면 자체는 수정을 직접 파쇄하지 않음(적 접촉·폭발·히트스캔만). 인게임 Vision 미검증.
