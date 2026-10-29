# W240 — Dynamic FOV와 HUD/PROFILE 표시 충돌 수정

## 단계 기록

1. W239 활성화 후 Windows 스크린샷에서 HUD 수평 확대·무기/팔 축소를 확인했다. 사용자 보고는 실제 줌 동작은 있지만 나머지 표시가 깨진다는 것이다.
2. 원인 조사: 공통 projection override의 Globals UBO 추가와 DisplayHUD의 기존 Globals 충돌 주석을 대조 중이다. master가 실화면·수정을 담당하고 읽기전용 worker가 엔진 바인딩을 조사한다.
3. 기존 격리 QA 서버(127.0.0.1:25611)와 Danmo 4GB Vision(8102)를 재사용해 FOVON 팩을 재현 중이다. 첫 클라이언트가 서버 준비 전 접속해 연결 거부됐고, 서버 준비 후 소유 클라이언트를 재시작해 정상 접속했다. 실서버25565와 일반 사용자 프로필은 분리한다.

4. 엔진 조사 결과 entity/item 파이프라인에도 Globals가 선언되고 이름으로 연결됨을 확인했다. 선언 순서 때문에 UBO가 밀린다는 초기 가설은 확정 원인으로 채택하지 않는다. Mac의 FOVON 실제 PNG에서는 HUD/팔이 정상이고 ADS 모델/스코프 전환이 관찰됐다. Windows 증상은 현재 Mac에서 재현되지 않았다.
5. 실제 composite dependency는 외부 checkout이 아니라 `libs/minigame-lib` submodule임을 확인했다. 동일 baseline의 외부 checkout에 처음 만든 두 파일 변경을 bundled dependency로 옮기고 외부 checkout은 정확히 이전 바이트로 복구했다.
6. 선택한 호환성 수정: raw Projection UBO에서 화면비 scalar를 읽는 accessor를 추가하고, DisplayHUD와 PROFILE entity/item은 이를 사용한다. 월드 ProjMat 매크로·FOV 계산·기존 UBO·운반/시간·모델/애니메이션은 유지한다. FOV가 꺼져 있으면 native ProjMat 비율로 fallback한다. 정확한 Windows GPU 원인은 미확정이다.
7. 기존 실서버 팩에서 셰이더 네 파일만 교체한 후보 fixture의 FOV ON/OFF 각각250프로그램(OpenGL/Vulkan 컴파일·링크), 총500개가 통과했다. 실제 빌드 팩의 바이트 일치와 Mac 실화면 검수는 다음 단계다. source-only worker 검수도 통과했다.

현재 상태: Mac HUD/PROFILE 검수와 실서버 적용을 마쳤다. Windows 증상 해결 여부는 재확인이 필요하다.

8. 첫 수정 QA 재기동 때 실제 dependency 경로 정정이 필요해 재기동을 취소했다. `stop` 명령이 초기화 중 처리되어 한 차례 command error가 났고, 정상 기동 후 재전송해 종료했다. 이후 실제 bundled resource가 build/resources와 일치함을 확인하고 다시 기동했다. 실서버 빌드는 겹쳐 실행하지 않도록 시작 직후 중단했다.

9. 새로 생성한 QA 팩의 core4개와 선택된 모든 pack include의 SHA256이 컴파일 검사한 후보와 일치했다. 다시 동일250개를 반복 실행하지 않고 바이트 일치로 검사 대상을 확인했다.
10. Danmo 공식62JAR·4GB·Mac OpenGL에서 에이스/Ammit/이자나기의 native sneak ADS 왕복을 각각90client tick 실행했다. 31/32/33개 실제 프레임을 캡처했고 대표 ADS PNG를 직접 열어 HUD와 무기/팔 표시를 확인했다. 최종 lease=false, heldKeys=[], pendingSteps=0, nativeInput 중립 후 소유 QA client/server를 정상 종료했다. 이 검수는 HUD/PROFILE 회귀 검사이며 Mac의 Sodium terrain 줌 배율까지 수락한 증거로 쓰지 않는다.
11. 사용자 답변으로 증상 환경은 Windows OpenGL임을 확인했다. Mac OpenGL에서는 변경 전에도 같은 깨짐이 없었으므로 Windows GPU 문제를 재현·해결 확정했다고 보고하지 않는다. 실제 Windows 새 팩 결과가 다음 확인 항목이다.

## 변경 범위와 증거

- bundled minigame-lib: projection.glsl에 raw aspect scalar accessor 추가; DisplayHUD는 줌 함수 반환 행렬 인덱싱 대신 원본 화면비를 사용.
- Destiny PROFILE entity/item도 같은 화면비 helper를 사용. 월드 FOV 함수와 네트워크 운반, 모델/애니메이션, HUD 좌표는 유지.
- 셰이더 검사 요약: shader-checks.json. 실제 생성 바이트: generated-pack-check.json. Vision 입력/상태: vision-results.json. PNG는 같은 폴더의 무기명-hip/ads 및 mac-before-* 파일. windows-opengl-reported.png는 사용자가 보낸 문제 화면.
- 이번 변경은 셰이더 리소스4파일과 submodule 포인터, 이 QA 기록이다. 기존 dirty 파일은 커밋에 포함하지 않는다. 새로운 JUnit이나 전체 gameplay gate는 추가하지 않았다.
- 첫 접속의 서버 준비 전 connection refused와 경로 정정 중 재기동 취소는 실패로 남겼다. 정상 재기동 후 실제 생성 바이트와 캡처로만 최종 Mac 결과를 기록했다.

12. 실서버를 runServer로 재개하고 online-mode=true, dynamic-fov-shader=true, 25565 LISTEN 및 새 팩 생성 성공을 확인했다. 팩85,276,837bytes, SHA1 `d3d10dcddbe8a9d7ac97cf049efb6cfd55708ff8`. 검증한 모든 셰이더/include와 실제 팩 바이트가 일치한다. 주소 `192.168.35.237:25565`; 사용자 테스트를 위해 서버는 유지한다. 라이브러리 수정 커밋은 `2acd9ab`이다.
