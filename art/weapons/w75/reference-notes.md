# W75 — ADS 지상 이동 배율 출처와 적용 경계

## 출처

직접 읽은 원문은 커뮤니티 **Destiny Data Compendium**의 공개 Game Mechanics / Weapon Perks CSV export다. 공식 원작 엔진 소스나 이번 작업의 실측이 아니다.
[원문 URL·SHA와 수치](references/movement-source.json), [추출 결과](references/extraction.json), [수집 기록](../../../docs/qa/2026-10-24/w75/source-transport.json).
전체 원문 CSV는 ignored `run/private-sources/w75`에 보관하고 배포팩에 넣지 않는다.

- 일반 ADS **0.75**, Sidearm **0.85**: Game Mechanics 원문 문장.
- 정밀 핸드캐논: Weapon Perks의 `10% Decreased ADS Movement Speed Penalty`와 [Bungie 2024-12-12 TWID](https://www.bungie.net/7/en/News/Article/twid-12-12-24)의 2025년 1월 변경 예고를 대조했다. **0.775 = 1−(1−0.75)×(1−0.10)**은 상대 penalty 감소로 해석한 도출값이며 독립 실측값이 아니다.
- 57종 중 일반50, Sidearm6, 정밀HC1(Seventh Seraph Officer Revolver). 검/월도6종은 일반ADS 대상이 아니므로 제외한다. Moving Target 등 다른 perk는 구현하지 않았다.

## Minecraft 적응

바닐라 Shift ADS는 기본 sneak input0.3이다. 26.3은 sneak 스케일 뒤 square-input normalization을 수행하므로 sneak만0.75로 바꾸면 대각선이1로 포화된다. 따라서 같은 서버 tick에 transient modifier 두 개를 설치한다.

1. SNEAKING_SPEED `ADD_MULTIPLIED_TOTAL`: `1/0.3−1`로 기본 입력1을 만든다.
2. MOVEMENT_SPEED `ADD_MULTIPLIED_TOTAL`: 원문 scalar−1. 지상 가속/최종 정상 속도에서 전후와 대각선에 같은 상대 배율을 준다.

기존 관성은 즉시 재조정하지 않는다. 조준 승인 시부터 적용하며 ADS 진행도별 속도 ramp는 이번에 만들지 않았다. **원작 m/s·Mobility·가속을 복제한 모터가 아니다.**

외부 base/permanent/다른 modifier는 바꾸지 않는다. 예약ID가 이미 있으면 양쪽 모두 설치하지 않고, 설치한 object 중 하나가 교체되면 남은 자기 object만 제거한다. 같은 값의 새 object도 외부 소유로 인정한다. ADS 해제 후 재시도한다. 재장전/스킬/수납/level/owner/관전/궁극기/카메라 및 clearAll에서 복구한다.

## 중요한 미구현/차이

[정확26.3 native 소비 감사](../../../docs/qa/2026-10-24/w75/native-consumer-audit.json)는 **bytecode/source 검토**이지 실행 입력 증거가 아니다.

- 일반 공중 가속은 `Player.getFlyingSpeed`의0.02(질주0.026)를 사용하며 MOVEMENT_SPEED 배율을 우회한다. 공중에는 sneak 중립화가 남지만 **ADS 공중 steering 배율은 구현하지 않았다**. 비행/활강/물·용암/수영/사다리/탑승/기어가기는 pair를 해제한다.
- MOVEMENT_SPEED가 바닐라 FOV-effect에도 영향을 주므로 client 설정에 따라 기존 ADS 줌과 합성될 수 있다. 기본 조건의 추가 factor는 .875/.925/.8875. 임의 보상식을 넣지 않았고 대표 화면은 확보했지만 client FOV-effect 설정별 정확한 합성 정도는 미검증이다.
- 외부 sneak 감속이0.3 아래면 중립화 후에도1에 못 미칠 수 있다. 외부 속도/질주 modifier와 점프 impulse는 보존한다.
- 원작 절대m/s, Hunter Mobility, 좌우0.85, heavy ready0.85, Lightweight sprint, 이동 특성, 원작 가속은 아직 없다.

새 client geometry/texture/audio 없음. 최종 headless gate 후 새 사용자 요청으로 별도 폴더/포트의 Vision Client 실게임 검증도 했다. 대표3종 지상 전진/대각선과 native F 수납의 결과는 QA에 분리했다. 정상 QA 서버·플레이어·앱·옵션은 건드리지 않는다. 전체 무기/HUD 목표는 계속 진행 중이다.
