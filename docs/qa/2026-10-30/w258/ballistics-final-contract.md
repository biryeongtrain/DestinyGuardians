# W43 head/body 후속 delta

기준은 fourth-full 당시 main 현재본 SHA256 118840982cf7690cec44b506472a8bdce34822049bda10347b875799ac36377f. main-baseline/slot-before 보존 후 slot1에 main 현재본을 복사했다. 이 파일의 actualHeadAndBodyDamageDifferAndOnlyConfirmedLossCreatesNumbers 하나만 수정했다.

실패 로그 위치는 -10025,4,5009340, tick0. 기존 상대좌표는 head player(2.5,1,4.5)/Husk(8.5,1,4.5), body player(2.5,1,8.5)/Husk(8.5,1.8,8.5)이다. 기존 AE100은 air term만 없앤다. 이 테스트는 exactAim을 호출하지 않고 equip 직후 hip 발사했다. ShotDispersion에서 hipTerm=(hip+bloom)*(1-ADS)*accuracy이므로 AE100으로 hip cone이 사라지지 않는다.

현재 Austringer adaptive, stability59, family hip2.3° → cone2.2172°. 표면까지 약5.7블록에서 수직 최대편차 약0.22069블록. 성인 Husk의 정확 조준선은 head top-quarter 경계와 약0.1575블록 차이여서 정상 hip RNG로 body 판정이 가능하다. WeaponRuntime.hitscan → WeaponAiming.direction → player RNG 두 표본 경로다. 실제 seed/표본과 개별 HP는 로그에 없어 해당 발사의 구체적 표본은 복원할 수 없다. 월드 위치만으로 RNG를 결정했다고 주장하지 않는다.

수정: 기존 exactAim(실제 ADS40틱+AE100, cone0 확인)을 두 owner에 적용한다. timeout25→70은 이미 존재하는 실제 ADS40틱 준비를 수용하기 위한 것이며 실패 대기만 늘린 수정이 아니다. 발사 전 실제 AABB ray 교차·head/body 경계로부터 >.1블록 margin·block LOS·falloff 이전·HP1000/absorption0/기존 feedback0을 독립 확인한다. 발사 후 한 발 소비/예비탄 보존도 추가했다.

기존 HP10.5/7, near 허용치 .001, feedback 각각1개, 숫자11/7, yellow/white 검증은 그대로다. 피해 assertion에 실제 loss 진단만 추가했다. 다른 테스트와 공통 helper는 바이트 동일. 제품/TestPlayers/main 변경 없음.

검증: Java tree-sitter 파싱, 테스트 method 목록 보존, 대상 method 외 바이트 동일, git apply --check --whitespace=error, main baseline 일치 확인. Gradle/build/runtime 실행 없음. 중앙 재실행 필요.
