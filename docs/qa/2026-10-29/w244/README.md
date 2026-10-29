# W244 — 바닐라 이동속도 줌과 좌클릭 ADS 토글

1. 사용자 요청: 동적 FOV projection을 제거하고 고배율일수록 실제 이동속도를 낮춘다. Shift ADS를 좌클릭 토글로 교체한다.
2. 기존 서버 정상 종료. 고정 슬롯1을 dirty/untracked 포함 현재 통합본으로 갱신했다. 수식·단위검사는 독립 작업자에게 배정, master는 입력·실제 속성·cleanup·팩 정책과 Vision을 맡는다.
3. 바닐라26.3 AbstractClientPlayer.getFieldOfViewModifier를 실제 병합 jar로 확인했다. 일반 보행의 속도 FOV 배수는 (속도/abilities.walkingSpeed + 1)/2이며 FOV Effects 옵션으로 보간된다. 양수 이동속도만으로는 약2배 이상의 실제 확대를 보장할 수 없다. DDC의 사거리/줌 데이터는 수정하지 않는다.
4. Shift+좌클릭 근접 능력, 궁극기 좌클릭, 검/월도 공격은 유지한다. Shift 자체는 일반 웅크리기·직업능력 입력이며 더 이상 ADS 입력이 아니다. 장전/무기교체/스킬/사망/월드전환에서 토글과 소유 속성을 해제한다. 검증 전 상태다.

5. 관련 JUnit27/27 및 새 GameTest 컴파일 통과. 기존 DDC ADS 이동값은 그대로 두고, 배율·진입 progress를 별도 순수 수식으로 적용한 뒤 Moving Target 감속 완화를 한 번만 적용한다. live에서는 과거 SNEAKING_SPEED 중화 속성을 설치하지 않는다.
6. 전체 JUnit/build를 진행한다. 이후 같은 격리 Danmo4GB 세션에서 W244 packet/cleanup GameTest4개와 W241 정확도 회귀5개, native 좌클릭·저배율/고배율·release/swap/reload를 취합한다. 기존 W44/W75 등의 Shift ADS·FOV 소유권을 전제로 한 과거 GameTest 전체를 통과했다고 주장하지 않는다.

7. 최종 전체 JUnit2,153/2,153, 실패/오류/skip0. assemble/jar 완료. `build`가 check에 연결된 과거 GameTest1,396개까지 시작해 Shift/FOV 전제 테스트 등에서 실패가 발생했다. 이 실행은 마스터가 SIGINT로 중단(exit130)했으며 build 성공으로 보고하지 않는다. 중단 전 로그는 `/private/tmp/destiny-w244/unintended-full-gametest.log`에 보존한다. W244 전용 실제 packet/ownership 검사와 W241 정확도 회귀는 격리 일반 dev서버에서 따로 실행한다.

8. 격리 일반dev서버의 실제 GameTest W2444/4, W2415/5 통과. 첫 console helper ACK 문자열은 실제 `Running4test(s)`와 달라 timeout이었으나 서버 로그는4개 모두 완료·통과를 확인했다. 팩85,111,066bytes, projection.glsl override0, config dynamic-fov-shader=false.
9. native QA 준비 첫 fill은 미로딩 청크에서 거부됐으나 이어진 teleport로 낙사했다. 입력 테스트 실행은 controllability gate에서 거부됐고 발사/ADS 성공으로 세지 않는다. 이후 청크강제로드25개, 바닥4225블록과 벽·표식, 안전스폰을 생성했다. CU/테스트 전용 화면복구로 리스폰을 진행한다.

10. CU에서 Java QA 앱을 선택하지 못해 UI 클릭을 실행하지 않았다. 격리 QA 월드에서만 immediate_respawn을 일시 활성화하고 테스트 접속을 종료·재접속하여 바닐라 자동 리스폰으로 복구했다. 복구 후 생존·기본 체력·예상 world·native eligibility를 확인했다. 첫 실패 launch 로그와 gate 거부 결과는 외부 QA 폴더에 보존했다. 사용자 일반 프로필/운영 서버 gamerule에는 적용하지 않았다.
11. Danmo4GB native 검증 완료: 좌클릭 ON 이후 neutral 상태에서도 ADS1 유지, 다시 클릭하면 ADS0과 기본속도0.1 복구. 동일20클라이언트틱 전진(+5틱 관성 정리)의 이동거리: 기본4.3134 / Ace2.3091 / Izanagi0.7157블록. 실제 속성: Ace0.05357143(53.6%), Izanagi0.01666667(16.7%). 수치만 아닌 실제 native 이동·서버속성·PNG를 함께 확인했다.
12. 실제 Izanagi 우클릭 사격은4→3발을 지불했고 서버 명령을 fixture로 사용한 장전 후4/4·예비19·ADS0·속도0.1 복구를 확인했다. Vision v1은 Q 키를 지원하지 않아 실제 Q키 검증은 주장하지 않는다. 실제30틱 좌클릭 hold가 바닥을 가리켜도 ADS1을 유지했고 다시 클릭 OFF, Shift단독15틱은 ADS0이었다. 정리 상태: leaseActive=false / heldKeys=[] / pendingSteps=0 / nativeInput 전부false.
13. `vision/contacts.png`와 원본 PNG6개를 직접 검수한다. native 줌으로 세계 표식이 확대되며 HUD 바·탄약 패널과 손/무기 모양이 유지됐다. 스코프 오버레이도 정상 표시됐다. 테스트 구조물의 녹색 beacon beam이 중앙에 남아 있는 점은 fixture이며 제품 VFX가 아니다. Windows 실기 재검증은 수행하지 않았다. 클라이언트 FOV Effects100%에서 검증했으며 이 옵션을 낮추면 줌도 약해진다.
14. 기존 Shift ADS/FOV 소유권 기반 과거 GameTest1,396개 전체는 이번 배치 수락 결과가 아니다. 전용4개와 정확도 회귀5개만 실제 완료·통과로 기록한다. 기존 전체 JUnit은2,153개 통과했다. 사용자의 새 입력 정책에 따라 과거 입력 가정이 달라졌으며 옛 QA를 새 정책 통과 증거로 사용하지 않는다.

15. 실제 PNG 검수 완료. QA client/server 및 이번 bounded awake coordinator 정상 종료, temporary immediate_respawn=false와 자체 추가한 강제로드25청크를 해제했다. 별도48시간 caffeinate PID79904는 유지했다. 슬롯1 worker는 종료하고 재사용 상태로 보존했다.

16. 운영 `runServer`를 TTY 세션으로 재시작했다. Minecraft Done·BetterModel 로드·Polymer 새 팩 생성 완료 및25565 listen을 확인했다. online-mode=true, andlist OP4, pause-when-empty-seconds=60 유지. 운영 새 팩에서도 projection.glsl override0, dynamic-fov-shader=false를 확인했다. 접속 주소192.168.35.237:25565. 이번 관련 변경만 선별 커밋하며 기존 dirty/untracked 작업은 보존한다.
