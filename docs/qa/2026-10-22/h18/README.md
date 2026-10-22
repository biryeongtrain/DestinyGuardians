# H18 — 바닐라 궁극기 후방 카메라 검증

2026-10-22. **실험적 구현 / 자동·화면 검증 통과 / 실제 키·마우스 검증 미완료.**
전체 기능 인수 완료나 실전 조작감 통과로 표시하지 않는다.

## 단계별 결과

1. 외부 camera entity의 일반 이동/회전 gate를 실제26.3 코드에서 확인했다.
2. owner-only 가상 탑승의 native Rot 경로를 실제 클라이언트로 입증했다. 초기 `/look`→서버 yaw/pitch 일치는 네트워크 경로 증거이지 물리 마우스 시험이 아니다.
3. native server tick에 키 상태를 공급하고, 위치/ground packet 주장을 무시한다. 낙하 정산 누락을 검토로 발견해 native 충돌 이동량으로 보완했다.
4. 최종 `runGameTest build` 성공: **GameTest100/100, JUnit49/49**, 실패·오류·스킵0. [빌드 로그](final_build.log).
5. 최종 빌드 뒤 서버JVM3·임시 Vision 클라이언트를 새로 띄워 아래 PNG/상태를 촬영했다. 서버 dev class83개와 JAR entry의 byte 동일성을 검사했다.
6. Arc/Void 후방 시점·자기 limb, Void 발사 회복 중 카메라 유지와 이후 원래 시점, Solar 시점 유지를 확인했다.
7. Computer Use는 잠금 해제 후에도 Java 앱을 바인딩하지 못했다. **실제 WASD·점프·달리기·구르기·마우스 조준·좌클릭은 미검증**이다.
8. effects0/beams0/camera false, Arc·에너지0·스폰·낮/맑음 복원. 자체 서버 정상 종료, 자체 클라이언트만 종료,25565/8102/8103 비점유·원본 Vision Git clean 확인.

## 최종 화면 — 서버 콘솔로 장면 구성

26.3 / 서버 Loader0.20.1 / 클라이언트 Loader0.19.5 / Java25 / OpenGL.
정상20TPS 설정,1708×960,HUD 표시, native perspective는 계속 `first`.
네이티브 F5를 변경한 것이 아니라 별도 entity를 camera로 지정한 결과다.
임시 Vision은 읽기 전용 camera/vehicle 진단만 추가했다. GCB 클라이언트나 이동·공격 확장은 없다.

| 장면 | 실제 PNG | 관측 상태 |
|---|---|---|
| Arc 준비 | [지팡이·자기 모델·후방 시점](final_arc.png) | [remote camera / 가상 승객](final_arc_state.json) |
| Void 준비 | [활·후방 시점](final_void.png) | [remote camera](final_void_state.json) |
| Void 발사 회복 | [회복 중 자기 모델 유지](final_void_release.png) | [remote camera 유지](final_void_release_state.json) |
| 회복 종료 | [원래 시점](final_restored.png) | [self camera / vehicle -1](final_restored_state.json) |
| Solar 발동 | [황금총 기존 시점](final_solar.png) | [self camera / vehicle -1](final_solar_state.json) |

장면 간 실제 몸은100.5/−60/100.5로 유지됐다. Arc 서버 query에서29 Rot를 수신했고 body/ground/input/camera를 별도로 기록했다.
콘솔 `guardian action primary`는 실제 좌클릭 전송의 증거가 아니다. 실제 이동/공격/조작감 인수는 아래 선행 작업 뒤 재개한다.

## 자동 테스트의 범위

새 카메라 GameTest10개:
- Solar no-op, owner limb/실제 passenger 없음, 회전 wrap/clamp/nonfinite 거부.
- 위조 위치/ground/collision 무시, 멱등·owner-local stop, 비행 중 발동 거부/에너지 보존.
- **0속도에서 native doTick 한 번**으로 전진·횡이동·벽 충돌.
- 실제6블록 낙하·native landing·피해 발생. 위조 ground packet으로 피해를 제거할 수 없음.
- Void 실제 발사 후 gameplay 종료와 마지막 회복 수명 분리.
- 실제 서버틱 heartbeat 유지와40틱 grace/초과 시 안전 해제.

순수 CameraMath JUnit12개와 기존37개를 합쳐49개다. 자동 테스트는 서버 로직 증거이며 네트워크 예측·마우스/키보드 조작감·렌더링 증거가 아니다.
초기 실패도 [첫 실행](failed_tests_initial.log)·[floor fixture 진단](failed_tests_floor.log)에 보존했다.
tickCount는 doTick이 아닌 외부 world tick 소유라 잘못된 assertion을 제거했고, 재예약 Runnable 소실을 고쳤으며 착지 pad를 명시했다. 속도 주입으로 이동 테스트를 우회하지 않았다.
레이아웃 검사 통과, 구형 fixture 탐지 경고1개(26.3 등록 구조를 탐지하지 못함).

## Computer Use 장애와 다음 선행 작업

- 잠금 해제 후 앱 inventory는 읽혔지만 Java 게임 창은 없다.
- `getApp("java")`, `getApp("com.oracle.java.jdk")`: Invalid app.
- 실제 GraalVM 번들 경로: Running application not found: com.oracle.java.jdk.
- 다른 UI 자동화 기술이나 신규 입력 endpoint로 이번 조작 검증을 대체하지 않았다.
- 사용자 결정: **다음 게임플레이 기능 전에 [Vision Client 테스트 제어](../../../design/26_Vision_Client_테스트_제어.md)를 구현·검증**한다. 현재는 설계이며 원본 Vision에 구현하지 않았다.

## 남은 한계

F5 perspective 잠금 없음, 벽 근접 limb 가림 정책 미완료, 다인/지연/청크 경계 실제 카메라 미검증.
외부 서버 카메라/CameraViews 선점은 처리하나 모든 모드의 packet-only camera 소유권까지 알 수는 없다.
낙하 순간이동 제외는8블록 변위 heuristic이다. 오프라인 스킨 폴백 색 전환은 기존 BetterModel 한계다.

## 증거·배포 구분

- [검증 조건·JAR·소스·증거 해시](validation.json), [최종 서버](final_server.log), [최종 클라이언트](final_client.log).
- `arc_camera_initial.png`·`arc_camera_display.png`와 prototype/display 로그는 **이전 예비 JVM**이다. 최종 런타임의 근거로 재사용하지 않는다.
- 기존 `outputs/DestinyGuardians-Hunter-26.3.zip`은 **H17 그대로**다. 미완료 H18을 검증 완료 배포본으로 덮어쓰지 않았다.

최종 클라이언트 wrapper의 exit143/BUILD FAILED는 자체 SIGTERM 종료 결과이며 gameplay crash로 집계하지 않는다. 초기 클라이언트의 post-main shutdown watchdog도 별도 예비 종료 문제로 보존한다.
