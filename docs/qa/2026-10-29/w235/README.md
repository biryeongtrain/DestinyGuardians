# W235 접속·검 카메라·1인칭 모델 오류

## 진행 기록

1. 사용자 mclo.gs/0U2mtrD 로그와 Imgur 원본을 보존했다. 스페이드 에이스의 오른쪽 아래 팔·무기 모양/위치 문제로 범위를 확인했다.
2. 실행 서버 로그에서 floating 퇴장 직후 DistanceManager.removePlayer의 chunkPlayers null 예외와 후속 로그인 타임아웃을 확인했다. thread dump는 정상 tick 대기였으므로 전체 JVM deadlock으로 부르지 않는다. 콘솔 stop으로 정상 저장·종료했다.
3. 정확 Fabric networking6.3.10의 JOIN이 PlayerList.placeNewPlayer의 addNewPlayer 이전에 호출됨을 역컴파일로 확인했다. 타워 차원 이동을 다음 서버 tick으로 미뤄 양쪽 월드에 중복 등록되는 경로를 제거했다. 같은 플레이어 객체의 전역/월드 등록을 확인하고 stale queue·disconnect를 정리한다.
4. 검·궁극기의 서버 물리 소유 중 handleMovePlayer를 취소하여 남는 clientIsFloating 상태를 소유 기간에만 비우고, 실제 등록된 플레이어의 청크 추적을 갱신한다. 서버 allow-flight=false는 유지한다. 카메라 release는 닫히는 연결에 복귀 teleport를 보내지 않는다.
5. 실제 placeNewPlayer·connection.tick·disconnect로 로그인→타워→퇴장→재접속, 검 camera100틱+청크 경계 이동, 일반 floating 차단을 검사할 manual GameTest3개를 추가했다. 정확 native disconnect/Fabric cleanup을 거치는 최종 3개 검사는 모두 통과했다. 첫 r1 카메라 검사는 fixture가 listener.onDisconnect를 직접 호출해 Fabric DISCONNECT를 생략한 실패였으며 실제 disconnect로 수정했다. 일반 floating 차단도 계속 통과한다.
6. 재사용 슬롯4를 통합본221,326파일 기준으로 갱신(41파일 변경)하고 hidden shell 경고 수정을 위임했다. 별도 agent가 사용자 이미지·Ace 렌더 경로를 읽기 조사한다. 기존 슬롯은 보존한다.

2,284개 particle 경고는 숨김 탄피5종의 빈 부모에서 파생된다. 이 경고 수정과 팔·무기 형상 깨짐은 구분한다. 서버 회귀·Vision 결과는 아래 단계별로 기록하며, 사용자 Windows와 다른 팩 설정으로 검사한 결과는 해결 근거로 사용하지 않는다.

7. Java25 compileJava/compileGametestJava 및 전체 JUnit 2,091/2,091 통과. 원시 결과는 `/private/tmp/destiny-w235/build-r2.log`, `junit-r2.json`, `qa/server.log`에 보존했다. 초기 QA 설정의 tower 비활성/whitelist와 RenderScale umbrella fabric-api 누락은 별도 harness 오류로 기록하고 수정했다.
8. 기본 Vision 및 사용자와 같은 RenderScale1.4.0-alpha.6(scale0.5)/Iris1.11.6/Sodium0.9.2의 Mac OpenGL4.1에서 Ace hip/ADS 실제 PNG는 정상이다. 이 조합만으로 사용자 NVIDIA GL3.3 증상은 재현되지 않았다. pack shader 변경으로 해결됐다고 주장하지 않는다.

9. worker12파일을 시작/결과 SHA-256 CAS 검증 후 통합했다. master targeted7/7 통과. 새 생성팩 SHA-1 `0364059c98d6295575e7ab3470a130305c43693e`의 hidden5 바이트도 source와 일치하고, 실제 client reload에서 Missing texture 경고0이다.
10. PackForge1.4 기본 설정(UV clamp 포함)을 추가한 OpenGL Vision에서 Antiope-D hip, Ace hip/ADS/reload 실제 PNG 정상. 장전은 native use1회 후 서버 fixture reload 명령으로 시작했으며 Q 입력 검증이라고 부르지 않는다. 입력 종료 heldKeys=[]/leaseActive=false 확인.
11. 사용자 첨부 ZIP의 SHA-1은 기존 `bc35f51202d5ad2a1bba94158cc67a720b5f9e02`와 동일하다. Mac 로컬 Danmo는1.21.8판이므로 공식 Modrinth26.3판4.6_263c를 격리 준비한다. 사용자 Windows의 추가·업데이트된 모드는 공식팩과 구분한다.

12. Polymer client0.18.2 추가에서도 Ace hip 정상. native 우클릭 검 camera125틱 유지, 카메라 분리·생존·neutral 확인 후 실제 연결 종료가 예외 없이 끝났다. 이어 공식 Danmo62JAR(GCB4.0.0 포함)에서도 재접속/타워 정상, Ace hip/ADS 정상.
13. 공식 Danmo4.6_263c 변경 기록은 `Removed RenderScale (*Resource pack compatibility issue)`다. 공식팩에 exact RenderScale1.4.0-alpha.6(scale0.5)를 다시 넣어도 Mac에서 Ace hip/ADS는 정상이다. 해당 upstream 경고만으로 이번 문제의 단독 원인이라고 확정하지 않는다.

14. 최신 Windows PNG는 RenderScale100%, Sodium0.9.2/Iris1.11.6(shader OFF), NVIDIA RTX3080/OpenGL3.3에서 Ace와 Mindbender의 팔·무기가 검은 가는 삼각형으로 찢어지는 증상이다. 실서버팩과 QA팩의 비 BetterModel 파일을 비교해 **실서버에만 `shaders/include/projection.glsl`이 포함**됨을 찾았다. 실서버 `dynamic-fov-shader=true`, 기존 QA=false로 달랐다. 기존 Mac 음성 결과는 동일 셰이더 조건 검사가 아니었다.
15. 실서버와 원래 첨부ZIP의 projection은 동일한 minigame-lib 선택적 Dynamic FOV 구현이며, 기본 코어 렌더에 `Globals`를 추가한다. displayhud.glsl의 기존 주석에도 같은 블록 추가 시 OpenGL 팔 찌그러짐 경고가 있다. QA를 true로 재기동하여 실서버와 **19개 shader 파일 전부 바이트 동일**함을 확인하고 재현 검사를 시작했다. 이 시점은 가설 검증 중이며 GPU/모델 자체 원인으로 결론 내리지 않는다.

16. 위와 같이 일치시킨 dynamic-fov=true 조건도 Mac OpenGL4.1에서 Ace hip·native ADS(웅크리기35틱/해제5틱)의 실제 PNG는 정상이다. 입력은 completed, leaseActive=false/heldKeys=[]/native neutral로 해제했다. Mac 검사만으로 Windows 문제를 해결했다고 판단하지 않는다.
17. sidecar가 정확26.3 native pipeline/snippet·실제 defaultUniform binding·Iris guard를 확인했다. **현재26.3에는 Globals layout/binding이 있으므로 과거 displayhud 주석의 unbound 설명을 이번 결함 원인으로 채택하지 않는다.** [조사 결과](projection-investigation.md). 단일 mat4 멤버 rename도 CPU block binding을 깨뜨리지 않는다.
18. 사용자 Windows의 비교를 위해 실서버를 정상 저장·종료하고 선택적 `dynamic-fov-shader`만 true→false로 바꿔 재기동했다. 원본은 `/private/tmp/destiny-w235/live-shaderfx-before-fov-off.json`에 보존했다. 이는 **비교용 임시 완화**이며 아직 확정 수정이 아니다. 이 상태에서는 ADS 자세/HUD는 유지하지만 동적 FOV 배율은 적용하지 않는다. 사용자 새 팩 수락 후 결과가 필요하다.

19. 비교팩 생성 완료04:40:24. SHA-1 `bafad81469834464073a706fac4249c42a9cfdbc`, 183520674bytes. autohost는 HEAD405(미지원), 제한 GET200 및 ZIP magic을 확인했다. projection override 없음, true QA 대비 shader 차이는 해당 파일1개뿐이다. online-mode=true/allow-flight=false/andlist OP4/포트25565 유지. 실서버는 켜 두고 격리 client/server만 정상 종료했다. 사용자 Windows 결과는 대기 중이다.
