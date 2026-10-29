# W253 기본 우클릭 연속 사격과 리핑 요청 목록

상태: 구현·관련 검증·운영 서버 재개 완료.

1. W252 이후 코드 기준선 보관. 무기 자체 automatic 플래그와 접근성 연속 사격 설정이 분리돼 있으며 WeaponAccessibility 기본값이 false라 단발·점사 기본 우클릭 유지 발사가 꺼져 있었음을 확인.
2. 기존 검증된 WeaponRuntime held input/짧은 heartbeat/WeaponCycle 점사 경로를 재사용하고, 플레이어 기본 설정을 true로 변경. 새 플레이어와 저장된 명시 설정이 없는 기존 플레이어에 적용. 명시적으로 off를 저장한 플레이어는 설정을 존중하며 `/destiny settings full_auto on`으로 켤 수 있다.
3. cadence/점사 크기/탄당 비용/충전 시간/퍽은 변경하지 않는다. 활·검·해제 기폭 유탄의 조작 의미는 보존. 기존 W113 검사는 새 기본값과 명시 opt-out, 설정하지 않은 파동소총 반복을 검사하도록 갱신.
4. 운영 runServer의 stdin이 닫혀 콘솔 stop을 전송할 수 없어, 소유 PID81405와 run/server cwd를 검증한 뒤 SIGTERM으로 종료를 요청했다. 프로세스 종료143 및 포트 해제를 확인했다. 콘솔 save/stop ACK는 확보하지 못했으므로 정상 콘솔 저장 종료로 보고하지 않는다. 다음 운영 실행은 콘솔 relay로 소유권·stdin을 유지한다.

5. WeaponAutoFireW113Test 7개 + FullAutoFiringW191Test 2개 = 관련 단위9/9 PASS, compileGametestJava·assemble PASS. 필터 `*WeaponCycleTest`는 실제 W46 클래스명과 달라 별도 cycle 검사로 세지 않는다. W113 실제 Runtime GameTest 10/10 PASS: 기본 on, 개인 off/on, 단발 양쪽 carrier, 중복패킷·짧은 lease만료, 기본 파동소총 반복과 틱별 점사/탄약 일치, 융합 재충전, setting 변경, 수동/자동장전 경계, 교체·관전자 취소. 전체2198개 게이트는 W252에서 기록한 기존 자산4실패가 있고 이번 변경은 기본설정에 한정되어 반복하지 않았다.

6. Danmo4GB/OpenGL+Vision26.3에서 실제 native use 40틱 유지 후16틱 중립을 실행했다. Austringer 11→6(5발), Blast Furnace 36→20(4점사×4회=16발). 이후20틱 추가 중립에서도 탄약은 그대로 유지됐다. 실제 framebuffer에서 무기·HUD 탄수와 점사 중25발 표시도 확인했다. 이 검증은 native input 및 실제 서버 탄약 결과이며 OS 마우스 이벤트나 오디오 청취 검증이 아니다.
7. 첫 setup의 `execute as ... destiny settings full_auto`는 플레이어 전용 노드의 콘솔 parse 제한으로 ACK 실패했다. 실제 플레이어 명령은 앞선 GameTest에서 검증했다. 해당 setup 명령을 제거하고 기본 설정 상태 그대로 사격했다. 첫 native sequence는 완료·중립이었지만 관측 JSON의 생략 가능한 error 필드를 직접 참조한 검증 스크립트가 KeyError로 종료했다. 원본 evidence는 attempt-1 폴더에 보존하고 `.get`으로 관측기만 수정해 두 무기를 재검수했다. 실패를 제품 성공/실패로 오인하지 않는다.
8. 최종 leaseActive=false, heldKeys=[], pendingSteps=0, native movement 중립. QA client 종료 -2, QA server save-all flush ACK와 stop 종료0 확인. 자료 목록은 model-request.md에 통합했고 worker는 main/SSD/기존 worktree를 변경하지 않고 종료했다.

9. 온라인 운영 runServer 재개: 25565 연결, Done·BetterModel 초기화·Polymer 리소스팩 생성 성공 확인. online-mode=true, andlist OP4 유지. 이번 서버 콘솔 relay는 /private/tmp/destiny-w253/production/server.sock, 실행 session28785로 유지해 이후 콘솔 save/stop이 가능하다. QA용 bounded awake coordinator만 종료했고 기존 사용자48h PID79904는 보존. 기존 미커밋 파일은 보존하고 W253 관련12개 경로만 커밋한다.
