# 군체 사망 효과음 비교 자료

스랄·시종·기사·마법사 각각 soft/hard dissolve의 8개 이벤트, 원본 WEM 36개입니다.
이 자료는 일반 군체의 사망 시 분해 효과음입니다. **헤드샷 전용 발동 여부는 미확정**입니다.
앞선 몰락자/기갑단 머리 파열 패키지에 군체는 포함하지 않았습니다.

INDEX.html에서 대표본과 전체 변형을 들을 수 있습니다. listen_first에는 이벤트별 대표 WAV/OGG가 있습니다.
audio/wav, audio/ogg는 원본 길이를 유지한 전체 변형이며 original에는 원본 WEM·BNK가 있습니다.
manifest.csv와 event-bindings.json에 이벤트/Media ID/WEM/패키지/patch를 기록했습니다.

## 확인한 것

- 원본 이벤트 이름의 FNV-1 해시가 SoundbankName과 일치합니다.
- 시퀀스의 SSequenceAudioEvent가 해당 사운드를 직접 가리킵니다.
- 각 뱅크 HIRC sourceID와 WEM package entry reference의 집합이 정확히 일치합니다.
- 36개 WAV/OGG 전체를 디코딩하고 비무음을 검사했습니다. 트림·피치·볼륨 변경이나 변형 합산은 하지 않았습니다.
- 스테레오 원본입니다. 원본 36개와 WAV/OGG는 같은 소리의 형식별 표현입니다.

## 확인하지 못한 것

일반 군체에서 별도 headshot/weakspot death 이벤트는 현재 이름 목록과 추가 이름 탐색에서 찾지 못했습니다.
이것이 게임에 그런 소리가 전혀 없다는 증거는 아닙니다. 피해 선택기 전체나 다른 이름의 공유 효과까지 완전히 해독하지 않았습니다.
원본 soft/hard 표기를 곧바로 몸통/헤드샷의 뜻으로 바꾸지 않았습니다.
추적한 피해 컴포넌트에는 disintegrate 해시와 함께 이 효과로 향하는 참조가 있어, 원소 분해 처치 등 다른 상황과 혼동하지 않도록 주의가 필요합니다.
기존 데이터의 thrall_taken_death_weakspot / taken_hive_trooper_death_weakspot / knight_taken_death_weakspot / taken_wizard_death_weakspot은 굴복자 변형입니다.
이를 일반 군체의 헤드샷 음원으로 대체하지 않았습니다.

실제 게임 A/B 청취, 정확한 피해 조건 전체, 최종 버스 믹스/감쇠, Minecraft 적용은 미검증입니다.
해당 소리를 확인하기 전에는 정밀 처치 전용으로 확정해 연결하지 마세요.
provenance에는 이름 탐색 결과, 원본 시퀀스와 역참조 조사 자료가 있습니다. 역참조 결과 자체는 범용 그래프 후보입니다.

설치 게임 빌드 25932352 / Charm 정식 3.5.0 소스 058e2ec1ec0912bed8687bd7329c3365aa81617d.
tools의 스크립트는 기존 작업 환경의 경로와 런타임을 참조하는 재현 자료입니다.
