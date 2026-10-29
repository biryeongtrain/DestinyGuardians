# W258 callback 예약 후속 수정

담당 15파일의 main 및 slot 해시가 첫 반환본과 일치함을 확인하고 그 버전을 백업했다. 4파일에 직접 중첩 scheduler 호출 25곳과 primedRocket continuation을 통한 간접 후속 예약이 있었다. 이 구조는 첫 W257 패치 이전에도 존재했다. crash stack은 GameTestInfo.tickInternal의 fastutil iterator에서 발생하지만 특정 테스트가 원인이라고 단정하지 않는다.

변경 파일: PerksW226GameTests.java, WeaponKillClipW61GameTests.java, ReloadCreditW65GameTests.java, WeaponRampageW66GameTests.java.

- PerksW226 Gutshot: 24→+24→+24를 setup에서 T24/T48/T72로 모두 등록.
- W61: primedRocket은 setup에서 T3 실제 처치/유한 reserve reload만 예약. 후속 emission T51와 impact T57, 마지막 buff tick T102와 impact T108은 각 테스트 setup에서 등록. Manual reload는 cadence+credit/recovery/expiry, shotgun은 first+2*interval+first, holster는 T3+70로 원래 deadline을 보존.
- W65 Outlaw: 실제 reload capture는 T119와 T152 그대로. 첫 phase 1/23/24/32/33, 다음 phase 24/41/42/58/59 관찰을 setup에서 절대 합산 tick으로 등록. runtime reload 객체만 배열로 보존.
- W66: emission cadence+3, impact cadence+11을 setup에서 등록. 동적 만료는 T3에서 실제 remaining으로 server deadline을 저장하고, setup에 미리 등록한 onEachTick이 그 tick과 +8에서 원래 행동/검증을 수행한다. callback 실행 중 새 예약은 없다.

모든 actor/target 생성, 입력, 피해 및 탄약 assertion의 실행 시점은 유지했다. 135개 GameTest와 기존 문자열 literal/검증 메시지 모두 보존. 15파일에서 직접 중첩 scheduler 호출 0곳을 정적 확인했고, drive/Fixture.at/primedRocket 호출 경로도 확인했다. TestCleanup.register는 별도 teardown deque이므로 native callback map을 추가하는 작업이 아니다.

통합 main에서 followup.patch의 git apply --check 성공. main 수정, 제품 수정, TestPlayers 수정, 공통 테스트 엔진/mixin 변경, build/run은 하지 않았다. 중앙 rerun 검증이 필요하다. 기존 JUnit asset 실패 4건은 건드리지 않았다.

followup.patch는 최초 W257 baseline이 아니라 이미 통합된 첫 반환본 대비 delta이다. manifest.json에 파일별 이전/이후 SHA-256과 검사 내역을 기록했다.
