# 머리 파열 효과음 개발 인계

## 이벤트와 원본

| 용도 | Entity | 시퀀스 컴포넌트 | 사운드 | BNK |
|---|---|---|---|---|
| 드레그 에테르 분출 | 80E158DB | 80E1D5FF | 80D48A7F | 80D48A7E |
| 반달 에테르 분출 | 80E158DD | 80E1D600 | 80D48A7C | 80D48A7B |
| 대장 에테르 분출 | 80E15907 | 80E1D615 | 80D48A85 | 80D48A84 |
| 기갑단 헤드샷 사망 | 미추적 | 미추적 | 80D488C2 | 80D488C1 |

몰락자 시퀀스는 SSequenceAudioEvent로 사운드 태그를 직접 가리키며, 시작 시간은 모두 0입니다.
같은 시퀀스에 에테르 분출 파티클들도 붙어 있습니다. VFX 데이터 자체는 이번 음원 패키지의 범위 밖입니다.
EntityComponents와 시퀀스 사운드는 Charm의 형식으로 읽었습니다.
상위 피해 컴포넌트에서 이 Entity로 향하는 참조는 그래프 후보이며 피해 선택기 전체를 해독한 증거는 아닙니다.

이벤트 이름은 원본 SoundbankName 해시와 FNV-1로 일치합니다.
각 WEM의 package entry reference가 해당 BNK의 HIRC sourceID와 일치하며,
네 BNK의 모든 sourceID 집합과 전달한 WEM 집합이 정확히 일치하는지 검사했습니다.
파일 순서나 WEM 태그 정렬만으로 Media ID를 추정하지 않았습니다.

event-bindings.json에 각 뱅크의 객체 종류, 원본 WEM 목록과 Media ID를 기록했습니다.
네 뱅크 모두 CAkRanSeqCntr 하나를 포함합니다. 변형들을 동시에 전부 합산하지 마세요.
변형 선택과 엔진의 거리 감쇠·버스 볼륨 등은 별개입니다.

## 빠르게 사용

드레그 대표본: listen_first/fallen_dreg_headburst.ogg (원본 80D61CD6)
반달 대표본: listen_first/fallen_vandal_headburst.ogg (원본 80D61CD0)
대장 대표본: listen_first/fallen_captain_headburst.ogg (원본 80D61CDE)
기갑단 대표본: listen_first/cabal_headburst.ogg (원본 80D68EE7)

원본 분출음의 한 변형을 골라 정밀 처치 이벤트에 연결하는 포팅 예시입니다.
적 종류별로 이벤트를 나누고, 머리/약점 명중과 치명 피해가 함께 성립한 때 호출하세요.
몸통 처치나 단순 정밀 피격에서도 재생되지 않도록 대상 게임의 판정 코드를 연결해야 합니다.
게임 자체의 실제 발동 조건 전체를 복원했다는 의미는 아닙니다.

examples/sounds.json은 Minecraft 리소스팩 경로 연결 예시입니다.
OGG들을 assets/destiny_headburst/sounds/ 아래로 복사하고 예시를 해당 namespace의 sounds.json에 병합하면
`destiny_headburst:headburst.fallen_dreg` 등의 이벤트를 만들 수 있습니다.
여러 sounds 항목은 선택용 변형입니다. 원본 Wwise 랜덤 가중치나 재생 이력 제한까지 복제한 예시는 아닙니다.
추출 범위여서 pack.mcmeta, 서버 판정/재생 코드, 배포는 포함하지 않았습니다.
스테레오 원본을 그대로 유지했으므로 위치 음원으로 사용할 때는 필요에 따라 모노 파생본을 별도로 만드세요.

## 자료와 검증

- 설치 게임 빌드: 25932352.
- Charm 정식 3.5.0 소스: 058e2ec1ec0912bed8687bd7329c3365aa81617d.
- WEM은 설치된 패키지에서 다시 추출했고 package/patch는 manifest에 남겼습니다.
- 원본 WAV 전체 디코딩, 프레임 수·채널·샘플레이트·비무음 검사.
- Vorbis 변환 후 전체 디코딩, 프레임 수 허용 오차 및 비무음 검사.
- Media ID 매핑, HTML 파일 참조, ZIP CRC와 SHA-256 검사.

실제 게임 A/B 청취, 사망 음성·총격음·거리 감쇠·버스 볼륨까지 포함한 최종 믹스,
헤드샷 피해 선택기 전체, Minecraft 실행과 성능은 미검증입니다.

provenance/semantic-evidence.json에 혼동하기 쉬운 이벤트의 판별 결과도 남겼습니다.
pla_headshot은 자체 WEM 목록이 없고 외부 재생 대상이 남아 있어 실제 효과음으로 대체하지 않았습니다.
ar_impacts_player_precision과 d2_pvp_kill은 이번 전달의 머리 파열 효과음과 구분했습니다.
tools는 작업 환경의 라이브러리와 절대 경로를 참조하는 재현 자료이며 별도 설치형 도구는 아닙니다.
