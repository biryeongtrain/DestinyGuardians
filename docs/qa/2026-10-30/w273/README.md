# W273 시련의 장 전투·탄약·표시, 장전 복귀, GCB 4.2

## 사용자 요구와 완료 조건

- 총기 피해 넉백 제거. 이동/회피의 의도된 속도는 유지.
- 아군/적군 구분과 시작 대치 위치 보정.
- 장전 완료 후 기본 자세 복귀. 원본 Blender → 61 pose 확인 → 1차 Vision → 담당자 피드백 → 2차 Vision.
- GCB 4.2 접속 패킷 호환. 구버전도 버전을 보내면 설치 인식.
- 매 부활 특수탄 지급: 사용자 답변으로 추적소총30발, 나머지2발 확정. 특수탄 보유 사망 시 양 팀이 수집할 수 있는 블록 드랍.
- 유효한 적 피해/처치에 소량 궁극기 에너지 지급.

## 단계 1: 소유권·기준선

4개 기존 worktree 슬롯을 재사용했다. 전체 과거 자산 스캔이 길어 `reuse_worktree_batch.py`는 preflight scan 단계에서 소유 프로세스를 중단했다. recovery 디렉터리 생성·파일 갱신·HEAD 이동 이전이다. 이번 배치는 각 슬롯의 독립 `w273-delta/`에 현재 main의 소유 파일만 복사하고 SHA256 기준선을 기록했다. 기존 슬롯 루트와 이전 delta는 보존하며, worker는 구 루트에서 빌드하지 않는다. 통합 때 기준선 drift를 검사한다. 소유 목록은 `ownership.json`.

## 단계 2: GCB 프로토콜 조사

`eiqq/GCB-mod` v4.2.0, commit `f18db83bfe9abff98c57baf96a8bd141a1fa4a69` 확인. 접속 시 버전 뒤 `FEATURE:SKIN`, `FEATURE:PERSPECTIVE`를 전송한다. 기존 GCB-server는 등록되지 않은 header의 constructor에 `.apply()`를 호출하므로 NPE가 발생한다. UTF/channel은 기존 `minecraft:gcb` 그대로다.

FEATURE capability 저장과 알 수 없는 확장 패킷 무시를 구현한다. 잘못된 key/perspective 값은 설치 인식·키 상태를 바꾸지 않도록 무시한다. 예외 처리는 decode의 잘못된 인자에 한정하며 apply 오류를 숨기지 않는다.

## 검증 진행

진행 중. 아직 최종 GameTest·Vision 통과로 간주하지 않는다. Windows의 기존 장전 음원 미청취 문제(W272)는 이 변경으로 해결됐다고 주장하지 않는다.

- GCB-server 수정 버전은 `1.2.1+26.3`. 최종 Destiny JAR의 include도 이 버전으로 갱신한다. GCB 서버 unit13개(4.2 신규3개 포함) 모두 통과.
- 운영서버는 21:05 list 결과0명 확인 후 통합 빌드 전 정상 stop했다. 검증 후4GB 설정으로 다시 열 예정.

## 통합·검증 결과 (master)

- 작업자 3명이 사용량 한도로 중단되어 남은 통합은 master가 직접 마무리했다. 전투(넉백 제거·궁극기 보상)·탄약·장전 복귀·팀 표시는 delta를 기준 해시 확인 후 반영.
- 대치 위치: 원본 입장 이동이 수십 블록이라 `HunterModelAssets.inPlaceIntro`로 root의 수평 이동을 착지점에 고정(수직·포즈·타이밍 유지), 모델명 `guardian_hunter_w273_r1`로 갱신, `PlayerAnimations.playIntroInPlace` 추가.
- 탄약: 부활마다 추적소총 30발·그 외 특수탄 2발, 특수탄 보유 사망 시 양 팀이 줍는 공용 블록.
- 통과: compileJava/compileGametestJava, GameTest(전투1, 장전 복귀8, 탄약 2). GCB 서버 단위 13.
- 단위테스트 5건 실패는 이번 변경과 무관한 무기 모델·HunterSuper 자산 해시 비교(이전부터 불일치).
- 미검증: 팀 색 표시·대치 구도의 실제 화면(Vision), 장전 복귀 모션 Vision 2회, GCB 4.2 실제 클라이언트 접속, 팀 GameTest 미작성, 탄약 블록 마지막 Heavy 테스트.
