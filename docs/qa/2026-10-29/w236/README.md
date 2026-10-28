# W236 리소스팩 로드 메모리 최적화

## 문제와 범위

사용자가 공식 Danmo와 4GB 힙 환경에서 팩 로드 OOM을 보고했다. 기존 실서버 팩은 ZIP 183,520,674 bytes, 압축 해제 1,851,217,319 bytes였다. 단순 다운로드 압축보다 클라이언트가 파싱·bake하는 item graph와 사용하지 않는 pose 수를 줄인다.

원본 무기 형상·UV·스킨 색상·장전61pose·게임플레이 수치는 유지한다. Windows의 팔·무기 찢어짐 원인은 별도 미확정이며, OOM 최적화만으로 그 결함까지 해결됐다고 간주하지 않는다. live의 dynamic-fov-shader=false 비교 설정을 유지한다.

## 구현 단계

1. W236 baseline ZIP과 기존 tracked dirty SHA-256 기준선을 외부 scratch에 보존했다.
2. WeaponPackRoots는 catalog와 현재 Reload/Insert/Aim/Bow/Scope/Izanagi/Swap selector에서 도달 가능한 item roots를 수집한다. W201 hands route 목록 중 해당하지 않는 과거 원본 item 및 hands wrapper만 출력 팩에서 제외한다. 소스 자산은 삭제하지 않는다.
3. 생성한 hands graph에서 상위 select/condition으로 이미 결정된 display_context·CMD string·flag 조건만 특수화한다. floating range thresholds와 NaN 동작은 변경하지 않는다.
4. 보존 item의 geometry/special base와 보존 geometry의 parent 연결을 추적한다. 자동 생성된 skin_arm_w204/poses, first_person_framing_w205, weapon_hands_w201/poses 안에서만 미참조 JSON을 제외한다. 기타 모델은 유지한다.
5. Polymer 0.18.4+26.3의 preFinish/ResourceConverter 공식 hook으로 실행한다. converter의 null은 출력 제외이며 ZIP builder에서 확인했다. 파일·소스·권위 item component를 런타임에 삭제/변조하지 않는다.

## 검사

- 작업자: Godel, 고정 worktree 슬롯4 재사용. ZIP closure audit + 테스트4개 반환·통합, baseline custom 누락0.
- 중앙: Java 컴파일 통과. Java 선택 동등성·runtime route·최적화 ZIP closure·4GB Vision 실제 로드는 진행 중.
- 최종 수치와 실화면 결과는 검사 완료 후 아래에 기록한다.

## 추가 메모리 진단과 26.3 형상 공유

2차 중복 제거팩은 ZIP141,774,068 bytes/raw1,054,647,859 bytes로 줄고 4GB Danmo/Vision 월드 진입에 성공했으나 GC 후에도 약3.3GiB를 유지했다. `jcmd GC.class_histogram`은 BakedQuad24,236,736개(2,132,832,768 bytes), CustomModelDataSource10,573,753개(253,770,072 bytes)를 보였다. 압축만으로 충분하다고 판단하지 않았다.

사용자 제공 `/Users/qf/Downloads/CORE-SHADER-HUD-GUIDE (1).md`를 읽었다. 여기의 공통 형상+변환 분리 방향을 적용하되 먼저26.3 바닐라 `CuboidItemModelWrapper.Unbaked.transformation`을 사용한다. pixel arm parent가 같아도 pose별 model ID가 달라 baked geometry가 중복된다. 자동 생성 skin_arm pose를8개 공통 parent mesh와 로컬 matrix로 바꾼다. 별도의 셰이더 수정 없이 현재 스킨 색과 형상을 유지하는 것이 첫 수락 대상이다.

`LayerRenderState.applyTransform`은 display 행렬 다음 local transform 순서다. 공통 mesh의 NO_TRANSFORM도 T(-.5)를 적용하므로 L=T(.5)·D_pose(ctx)를 사용한다. native ItemTransform의 왼손 X이동/YZ회전 부호, translation /16 및±5 clamp, scale±4 clamp, XYZ 회전 순서를 보존한다. 오른손·왼손 문맥마다 별도 행렬을 선택한다. 알 수 없는 parent/기존 local transform은 원래 pose 경로를 유지한다.

native ItemTransform.Deserializer/apply 및 native MATRIX4F encode/decode와 비교한 JUnit3개 통과(첫 fixture 소수점 표기 오류1회 수정). 원본 리그·장전 프레임을 다시 저작하는 변경은 아니다.


## 3차 시험과 개선 방향

8개 기본 손 mesh로 직접 교체한3차는 ZIP117,956,042 bytes지만 raw1,755,273,787 bytes였다. 좌우 문맥별로 tint 목록이 중복돼 CustomModelDataSource20,410,905개/489,861,720 bytes가 유지됐다. 실제4GiB 힙으로 월드에 진입했고 Ace 손·무기 PNG는 정상이나, 로드 총116.93초로2차73.41초보다 느렸다(기동·캐시 차이가 있어 엄밀한 속도 비교는 아니다). 강제GC후 heap2,862,794KiB, BakedQuad17,425,152개/1,533,413,376 bytes였다. ZIP 크기만 보고 최종 수락하지 않았다.

4차는 원래 pose 중 같은 좌우 카메라 구도를 갖는 대표 pose를 공유한다. C=D_left·inverse(D_right)가 같은 후보를 묶고, L=inverse(D_anchor_right)·D_pose_right를 사용한다. 두 문맥 모두 D_anchor(context)·L이 원래 D_pose(context)와2e-5 이내인지 확인한 경우만 공유한다. 양손을 같은 select case에 묶어 tint 중복을 없앤다. 원래 대표 pose의 native display를 그대로 사용하므로 새 shader나 display clamp 근사를 만들지 않는다. 불일치 pose는 별도 대표로 남는다. 원본61frame/스킨/소스는 보존한다.


## 최종 선택: 4차 대표 pose 공유

| 항목 | 기존 | 최종 |
|---|---:|---:|
| ZIP bytes | 183,520,674 | 139,999,626 (-23.7%) |
| 압축 해제 bytes | 1,851,217,319 | 1,059,471,598 (-42.8%) |
| 손 item JSON bytes | 1,537,916,857 | 774,982,068 (-49.6%) |
| ZIP entries | 167,692 | 127,802 |
| custom model 누락 | 0 | 0 |

정확 MaxHeapSize=4,294,967,296 bytes, 격리 공식 Danmo 기반62모드+사용자 주요 렌더 버전+Vision, Mac OpenGL에서 실제 접속했다. 클라이언트 로그상 전체 기동→월드62.59초, 메인메뉴→월드18.46초였다. 팩 파싱만의 순수 시간이나 Windows 속도로 해석하지 않는다. `GC.class_histogram` 직후 heap3,122,320KiB(약2.98GiB), BakedQuad23,836,544개/2,097,615,872 bytes, CustomModelDataSource10,555,241개/253,325,784 bytes. 짧은 대표 시나리오에서 OOM 없이 유지됐다. 이 값으로 Windows4GB 환경 전부의 OOM 해소를 보장하지 않는다.

### 실화면

- Ace: 스킨 손/힙/ADS/발사/장전/복귀 PNG 확인. Q 대신 명령으로 장전 트리거, native Q 경로 검증은 아니다.
- Izanagi, Biting Winds, IKELOS SG: 주 손을 비우고 load한 뒤 Vision mainModel로 실제 장착을 확인했다. 조준/발사/손 PNG를 확인했고 Izanagi·샷건 장전도 확인했다. 활은 자연 재장전 동작 후 명시 reload는 불가로 반환돼 이를 장전 명령 성공으로 세지 않는다.
- 첫 다무기 시도는 기존 탄약 보호로 장착이 거절되어 Ace가 유지됐음을 PNG로 발견했다. 잘못 이름 붙은 `*-anchor` 다무기 캡처는 근거에서 제외하고 `*-verified`만 사용했다.
- 증거: `/private/tmp/destiny-w235/qa/frames/w236-ace-anchor-sample-03.png`, `w236-ace-reload-anchor-sample-04.png`, `w236-izanagis_burden-reload-verified-sample-04.png`, `w236-biting_winds-verified-sample-03.png`, `w236-ikelos_sg_v1_0_1-reload-verified-sample-04.png`.
- 최종 leaseActive=false, heldKeys=[], pendingSteps=0, nativeInput 전부false 확인 후 소유 QA 종료.48시간 caffeinate는 별도 유지.

### 코어 셰이더 결정과 한계

[조사](shader-feasibility.md): player_head/PROFILE 스킨 텍스처를 팔 UV로 바꾸는 방식은 후속 후보이다. 현재 작업에서는 새 셰이더를 배포하지 않았다. 문서의 공통 형상·자세 분리 원리를26.3 native item transformation으로 적용했다.3차는 메모리가 더 낮아도 raw 증가와 로드 지연이 있어 선택하지 않았다. Windows 팔·무기 찢어짐과 Vulkan 호환성은 별도 미검증이며, 기존 dynamic-fov-shader=false를 유지한다.


## 최종 자동 검사와 통합

- Java 전체 JUnit2,102개: 실패0, 오류0, skip0 (`/private/tmp/destiny-w236/full-test.log`). 신규 graph7개·native matrix/anchor4개 포함.
- Python closure audit 테스트4개 통과. 최종 ZIP custom model 누락0/error0. 원본 ZIP과 비교 결과는[요약](pack-result.json).
- 고정 슬롯4 작업자 종료, delta 통합 후 idle-needs-refresh/W236으로 반영. 다른 슬롯 상태는 변경하지 않았다.
- 기존 tracked dirty SHA 기준선53개 중 이번 작업으로 달라진 것은 initializer 신규1줄과 슬롯4 기록뿐이다. 다른 기존 변경은 보존한다. 손 route/이자나기/교체 presentation3개는 기존 untracked 클래스에 pure getter/route helper를 추가한 관련 선행 파일이므로 해당 파일 전체를 커밋 범위에 포함한다. 그 외 기존 untracked 원본·자산·QA는 일괄 추가하지 않는다.


## 실서버 반영

`runServer` 세션64053, 포트25565로 재개했다. online-mode=true, allow-flight=false, andlist OP4, dynamic-fov-shader=false를 보존했다. live 고유 BetterModel 자산 때문에 위 격리 QA보다 ZIP이164,892 bytes 크며, 실제 배포 ZIP은140,164,518 bytes/SHA-1 `cae10eba39084e2ed0a1cd8b2eecc63f14be06a3`이다. live item915개/참조 누락0/error0, 손 graph774,982,068 bytes는 QA와 동일하다. 실제 hash URL의 제한 GET200/Content-Length140,164,518/ZIP magic504b0304를 확인했다. [실서버 요약](live-pack-result.json).

접속 주소: `192.168.35.237:25565`. Windows 사용자 재접속의 새 팩 로드·팔 찢어짐 결과는 아직 받지 않았다. 이번 최적화가 Windows 렌더 결함까지 해결됐다고 보고하지 않는다.
