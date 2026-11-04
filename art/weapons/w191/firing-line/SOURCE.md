# Firing Line — W191

- 수치: [DDC Weapon Perks 96행](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278), `td` 이름 `Firing Line` 정확 일치. 아군 2명 반경 15m → 기본 정밀 피해 +20%. 강화 전용 ↑+10 Handling 제외. 잔류 시간 없음.
- 고정 공식 manifest: `245114.26.10.13.2000-1-bnet.66137`. 전체 manifest 재조회 없음. `source.json`과 리소스 `source`에 원문 HTML 행·입력 SHA-256·기본 특성 정의/소켓 증거를 보존한다(전체 특성 정의는 source.json).
- 정확 소켓: Line in the Sand `946443267 / socket4 / pool3257645194`, Stormchaser `3652506829 / socket4 / pool4213354588`, Fixed Odds `2194955522 / socket4 / pool1686775256`. 기본 Trait `1771339417`, 분류 `4241085061`, 실제 randomized pool, `isFakePlugSet=false`, `currentlyCanRoll=true` 확인. 다른 재발행·강화 특성 확대 없음.
- Minecraft 환산: 15m=15블록, 유한한 3차원 중심 거리 제곱 ≤225. 자신 제외, 동일 레벨의 생존·연결·비관전자 플레이어만 센다. 같은 바닐라 팀 또는 양쪽 무소속만 아군. LOS·청크 로드·attachment 생성 없음.
- API: `WeaponFiringLine.Token.NONE`, `capture(ServerPlayer)`, `Token.precisionMultiplier()`. 발사 비용 지불 뒤 아군 조건을 스냅샷한다. 조회 때 원래 플레이어 인스턴스·레벨·실물 스택 소유/장비·선택 롤 검증. 원래 무기를 계속 소유/장비하면 stow 허용. 새 총으로 권한 대체 불가. 조건 미달 발사는 뒤늦게 활성화되지 않는다. 다음 발사는 새로 판정하므로 linger/tick/cleanup 상태가 없다.
- 통합 경계(master 소유): 공유 `WeaponPerks`에 세 롤 등록, `WeaponRuntime.DamageTraits`에 paid token 운반, `perkSplash()`에서는 NONE. `apply(...HitDamage...)`에서 `hits.precision`에만 배율을 먼저 곱한 후 합산 피해와 body/precision 숫자 비율 계산. 일반 피해 배율 곱셈에 넣지 않는다. 능력·몸통·폭발은 제외. 이 작업자는 공유 경로를 변경하지 않는다.
- 재생성: 워크트리에서 `rtk proxy python3 scripts/build_firing_line_w191.py --root .`. 로컬 입력만 사용한다. 출처 해시는 감사 자료이며 런타임 해시 gate가 아니다. 수치 복제 테스트·전체 suite·게임/Vision 검증 없음. 통합 컴파일/실제 적용 경로 검증은 master가 수행해야 한다.
- 수행 검사: 생성기 실행 및 JSON/출처 연결·입력 7개 SHA-256·세 소켓 증거·Python 문법·소유 파일 공백 확인 통과. 프로덕션 `withinRadius`/`sameTeam` 메서드 본문을 그대로 Java 25 JShell에서 실행하여 반경 경계 안/위·0/음수/NaN/무한대·동일/상이/무소속 팀 14개 분기 통과(검사 파일 추가 없음). 기존 `WeaponRuntime`의 합산 지점과 피해 숫자 분배 경로를 소스로 검토했다. Minecraft 의존 클래스 컴파일·실제 엔티티/소유권 실행 검증 및 공유 통합은 미수행.

- Master 통합 보정: 접속 authority는 `hasDisconnected`와 원본 플레이어·data/runtime/class identity로 확인한다. 연결된 embedded GameTest와 동일한 서버 경로를 사용하며 player-list 등록을 추가 조건으로 요구하지 않는다.
