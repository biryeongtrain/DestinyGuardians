# master 검토 필요: 비가디언 발사가 GuardianRuntime 생성

- 기존 실패: second-run.log:1832 (최종 요약:4283), SubsistenceW167GameTests.ordinaryLiveWeaponOwnerDoesNotNeedAnAbilityRuntime.
- 실패 메시지: `Capture and ammo HUD cannot create ability runtime on tick 0`.
- 기준 테스트: 클래스 NONE 설정 후 런타임 부재 확인 → 실제 유료 처치 → Subsistence 탄약 반환 확인 → 런타임 부재 재확인. 마지막 assertion 실패. 이 worker는 assertion을 유지했다.
- 현재 main 소스에서 확인한 경로:
  - `src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:823`: emit에서 `WeaponFireMotion.emitted(player,entry,p,playFire,boltIndex)` 호출.
  - `src/main/java/kim/biryeong/destiny/weapon/WeaponFireMotion.java:46-49`: emitted의 가시성 조건이 `visible(player)` 호출.
  - 같은 파일:85-88: visible이 `!Guardians.runtime(p).gcbThirdPerson`을 읽는다.
  - `src/main/java/kim/biryeong/destiny/guardian/Guardians.java:32-33`: runtime은 computeIfAbsent로 새 GuardianRuntime을 생성한다.
- `WeaponFireMotion.pose/retire`도 같은 visible을 사용한다(71/80행). 읽기 성격의 경로가 런타임을 만들 수 있다.
- 제안: master 제품 소유 범위에서 runtimeIfPresent 기반 gcbThirdPerson 조회를 검토. 없으면 false 처리하여 일반 무기 사용자가 능력 런타임을 요구하지 않도록 할 수 있다. 이 worker는 제품 소스를 변경하지 않았다.
- 근거는 기존 run2 실패 및 현재 소스의 정적 경로. 수정 후 재현/통과를 확인한 것은 아니다. 중앙 run3에서 기존 assertion으로 확인해야 한다.
