# 공격전 공용 계층 (악마의 소굴 → 엑소더스의 추락 준비)

공격전이 늘어나도 한 번만 고치면 되도록, 악마의 소굴(Devils Lair)에서 공격전 공통 동작을 `activity/strike`로 옮겼다.
악마의 소굴은 이 공용 계층 위의 얇은 어댑터다. 실행 상태는 공격전별 `StrikeHost`/`StrikeInstances`가 각자 가지며 전역 공유 상태는 없다.

## 공용 부품

| 부품 | 역할 | 공격전이 제공하는 것 |
|---|---|---|
| `StrikeCoordinator` / `Strikes` | 파인더·이탈·전투·능력이 "어느 공격전인지" 모르고 묻는 창구 | `Info`(이름·배너·인원), 위임 메서드 |
| `StrikeHost<R>` | 실행(run) 레지스트리, 시작 가능 검사, 틱 구동, 재접속, 복귀, 행동 허용 판단, 월드 보호 이벤트 | 인원 제한, 맵 로더, 월드 팩토리, `RunFactory`, 정리 훅 |
| `StrikeRun` | 한 화력팀의 한 번의 진행 | 세션 구현(디렉터·인카운터·연출) |
| `StrikeInstances` | 화력팀당 임시 월드(Fantasy)와 정리 큐 | 인원 제한, 청크 생성기 |
| `StrikeMaps<Z>` / `StrikeZone` | 구역별 NBT 템플릿·`markers.json`·앵커·후보·범위 | 구역 enum, 구역별 원점, 리소스 폴더명 |
| `StrikeWorldBuild<Z>` | 모든 구역의 청크 예열을 예산 안에서 순차 진행 | 구역 enum |
| `StrikeReturn` | 입장 전 위치·게임모드의 영속 저장과 복귀 | 첨부 id |
| `StrikeRoster`, `StrikeAdmission`, `StrikePausePolicy`, `StrikeBriefingGate`, `StrikeVoice*`, `StrikeScore`, `ScoreTimeline`, `ScorePlaylist`, `StrikeSubtitles` | 1단계에서 이미 이동 | |
| `StrikeCombatant` | 다중 히트박스·방패·랭크 등 전투 시스템이 모브 종류를 묻지 않게 하는 인터페이스 | 모브가 구현 |

## 새 공격전 추가 절차

1. 구역 enum을 만들고 `StrikeZone`을 구현한다(`resourceName()`은 템플릿 파일명이자 `markers.json` 키).
2. 추출한 맵을 `data/destiny/<strike_id>/zones/markers.json`(schema 1, 구역마다 `<ZONE>.IN` 앵커 필수)과
   `data/destiny/map_template/<strike_id>/<zone>.nbt`에 둔다. 템플릿 최소 좌표는 구역 원점과 일치해야 한다.
3. `StrikeMaps`로 맵을, `StrikeInstances`(+`NbtTemplateChunkGenerator` 어댑터)로 월드를 구성한다.
4. `StrikeRun` 구현(디렉터·인카운터 계획·연출)을 쓰고 `StrikeHost`를 만든다. `RunFactory`가 이를 생성한다.
5. 전용 `StrikeCoordinator`를 만들어 `strike/StrikeLineup.register()`에 등록한다. 파인더·이탈·전투 허용은 그대로 따라온다.
6. 적 모브는 `StrikeCombatant`를 구현한다. 대사·BGM·자막은 `StrikeVoiceCatalog`/`ScorePlaylist`/`StrikeSubtitles`를 쓴다.

## 아직 악마의 소굴 전용인 것 (엑소더스 제작 시 일반화 후보)

`DevilsPlan.Kind`(타락자/하이브 종류표), `DevilsDirector`(단계·증원 규칙), `DevilsActors`/`DevilsActorModel`/`DevilsMob`,
`DevilsRecovery`(다운·부활 연결), `DevilsSupplies`/`DevilsSupplyStations`, `DevilsSpatial`(스폰 탐색),
`DevilsAttemptStats`, `DevilsGuide`, `DevilsCombatSounds`, 연출(`DevilsPresentation`). 엑소더스는 타락자 + 벡스를 쓰므로
`Kind` 표와 모델 선택은 활동별 설정으로 분리해야 한다. 실제 맵·적 구성이 확정되면 필요한 것만 같은 방식으로 옮긴다.

## 검증 상태

- 컴파일(main/test/gametest)과 `strike.*`, `activity.*` 단위 테스트 통과.
- 동작은 기존과 동일하게 유지했다: `Strikes.allows`는 등록된 공격전이 하나일 때 이전 `DevilsLair.allows`와 같다.
  시작 가능 검사는 다른 공격전 참가 여부도 함께 본다.
- 전체 `runGameTest`는 작업 트리에 다른 작업의 미커밋 무기 변경이 섞여 있어 이 변경만의 통과로 보고하지 않는다.
