# W246 — 타워 낙하 복귀와 PvP 보호

1. 기존 설정은 Y<-60에서 복귀했다. 스폰 높이75 기준 Y<=60에서 안전 스폰으로 복귀하도록 manifest와 재생성 설정을 함께 변경했다. 낙하 속도·낙하거리를 초기화하는 기존 teleport 경로를 재사용한다.
2. 타워는 이미 PVP=false 및 플레이어 ALLOW_DAMAGE=false였다. AttackEntityCallback으로 플레이어 공격을 먼저 거부하고, Combat.damage도 쿨다운·공격자 기록을 바꾸기 전에 거부하도록 보강했다. Creative/OP에게도 공격 예외를 주지 않는다. 다른 차원의 전투 설정은 유지한다.
3. 기존 tower GameTest에 경계 바로 위/정확한 경계/그 아래의 복귀, 생존·속도 초기화와 survival/creative 공격 차단·커스텀 피해 무변경 검증을 추가했다. 서버를 정상 저장·종료한 뒤 격리 QA에서 실행한다.

4. main compileJava/compileGametestJava와 격리 일반 dev 서버에서 정확한 수동 GameTest4개가 모두 통과했다. Y60.01은 유지, Y60과50은 안전 스폰으로 복귀하고 health20·속도0을 확인했다. 플레이어 공격 callback·바닐라 피해·커스텀 피해 차단, 전송 cleanup/게임 모드 보존·막힌 스폰 보정 금지 회귀도 통과했다.
5. 외부 검사 스크립트가 처음 성공 문구를 `All 1 required tests passed`로 잘못 예상했다. 실제 서버의 `All required tests passed`를 확인하고 수집기만 수정했다. 이미 성공한 낙하 테스트를 반복 실행하지 않고 나머지3개를 실행했다. 제품 테스트 실패는 없었다.
6. 화면/모델 변경이 없는 서버 규칙 배치이므로 새 Vision 실화면 세션은 실행하지 않았다. 서버 authoritative GameTest 결과를 실화면/실제OS입력 검증으로 표기하지 않는다. QA는 정상 저장·종료하고 운영 서버를 기존 online-mode=true 설정으로 다시 연다.

7. 운영 runServer가25565에서 재기동했고 타워 준비·기존재질0변경/0건너뜀·리소스팩생성이 완료됐다. online-mode=true, andlist OP4를 유지한다. 새 리소스팩 아트 추가는 없다. 이번 관련 파일만 커밋하며 기존 Combat.java의 탄약 집계 변경 등은 별도로 남긴다.
