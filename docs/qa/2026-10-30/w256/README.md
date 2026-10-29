# W256 — 후방 카메라의 1인칭 무기·팔 중복 표시 수정

## 요청과 원인

W255 Danmo 실화면에서 궁극기3인칭 모델과1인칭 무기가 동시에 보였다. 사용자가 이 표시 문제를 바로 수정하도록 요청했다.

서버사이드 SuperCamera는 카메라 패킷만 보내고 실제 ServerPlayer.getCamera()는 플레이어로 유지한다. ProfileWeaponView는 getCamera()!=player 및 GCB3인칭만 검사해, 셰이더 기반 owner-only gun/4arms/grenade display HUD를 후방 카메라 중에도 갱신했다. 실제 인벤토리나 BetterModel 전신 장비를 비우는 문제가 아니다.

## 구현과 분담

master는 ProfileWeaponView와 SuperCamera를 수정한다. 카메라 세션 시작 직후1인칭 HUD6개를 제거하고, 세션이 살아 있는 동안 update에서 재생성하지 않는다. 종료 뒤 다음 update가 현재 손의 무기로 새로 생성하므로 이전 무기를 복원하지 않는다. 황금총의 solar start는 세션을 만들지 않아1인칭을 유지한다.

slot5를 재사용하는 Bohr는 별도 ProfileViewCameraW256GameTests.java만 작성하며 main 빌드/실게임 입력은 master가 맡는다. 워크트리는 삭제하지 않는다. 운영서버 접속자0명 확인 후 정상 종료했다.

## 검증

진행 중. server GameTest와 Danmo native/실제 PNG를 분리해 기록한다. 기존 W255 원본 모션/배속/시전시간은 변경하지 않는다.


### 소스 통합·targeted gate

Bohr의2개 GameTest를 검토 후 SHA256 ca37e1c2cc6e4e7d174e02907be393cedbec22272360c6d0318245ad3bb928af로 통합했다. 실제 DisplayHud registry6개 제거, 반복 updater의 재생성 차단, 시전 중 무기교체 후 현재 graph/양손 selector 복구, real ItemStack identity·components 보존, 황금총 solar camera no-op을 검사한다. 테스트용 공개 제품 API는 추가하지 않았다.

기존 ProfileViewFraming/ProfileArmGraph/SwordHandPackets/CameraMath JUnit39개 통과, assemble 성공. 수치나 모델을 바꾸지 않았으므로 Blender/61포즈 변환은 반복하지 않는다. 새 runtime GameTest와 실제 Danmo PNG를 이어서 확인한다.


### 통합 gate 및 runtime 회귀

전체 JUnit2208개 중2204통과,4실패. W255와 동일한 Austringer/Mindbender/WeaponSurfaceW115/WeaponSilhouetteW112 자산 계약 실패이며 새 실패는 없다. compileGametestJava 성공. 전체 명령의 종료코드1은 이 네 기존 실패 때문이다.

첫 신규GameTest는 팩생성 완료 전에 실행해 ProfileArmAssets.graph가 아직 비어 있었고, 최초 HUD생성에서 실패했다. 실패와 서버log를 보존했다. Profile skin view 생성03:58:21, 팩완료03:58:39 이후 같은 코드를 재실행하여 신규2개 및 기존 classContact 회귀까지3/3 통과했다. 제품/fixture를 통과용으로 변경하지 않았다. QA runner에 팩완료 대기 조건을 추가했다.


### Danmo 실화면 및 worker 재검수

기존 Danmo 격리4GB 클라이언트/OpenGL에서 헌터 아크·공허/타이탄 아크/워록 솔라를 실제 sneak+swap 입력으로 시전했다. 클래스·하위직업 변경 ACK, 에너지100%, remote camera와 클래스별 event 로그를 함께 확인했다. 후방 카메라 중1인칭 총/팔이 사라졌으며 공허 복귀 뒤 다시 표시됐다. 황금총은 별도 native 시전으로1인칭 총을 유지했다. 마지막에는 일반 Ace 복귀와 lease/native 중립을 실제 PNG+상태로 확인했다.

첫 아크 캡처에서 몸체 없이 지팡이만 보인 현상이 있었으나, 같은 빌드의 아크 재시전은 본체·지팡이 정상이며1인칭 무기 중복이 없었다. 최초 현상은 원인 미확정으로 보존하며 반복 검증에서 재현되지 않았다는 범위로만 기록한다. FPS 저하 구간을 포함하므로 연속60fps 검증이 아니다. 후방 카메라중복 제거의 최종 collage에는 재시전 아크를 사용했다.

Bohr에게 W255/W256 실제 PNG와 아크 재시전 원본을 전달해 재검수를 받았다. 직접 이미지 확인 결과 중복 제거 수락, 추가 수정 요청 없음. 원본 모션/시전시간은 변경하지 않았다. 운영 online 사용자 스킨은 이 offline QA의 검증 범위가 아니다.

### 서버 메모리 — 사용자 추가 지시

runServer/runGameTest에 maxHeapSize=4g를 지정한다. 이전에는 서버 task의 명시적 상한이 없어 JVM의 호스트 메모리 기준 기본값을 사용했다. Gradle daemon의3GB 및 JUnit의2GB와 서버 JVM은 별개다. 앞의 실화면 검증은 변경 전 이미 떠 있던 QA 서버에서 수행했으며,4GB 서버 런타임 확인과 구분한다. 현재 QA를 정상 종료했고 운영 테스트 서버를4GB 상한으로 재기동한다.


heap 설정 검사는 첫 init script가 included minigame-lib까지 대상으로 삼아 null로 실패했다. main 프로젝트 경로로 제한한 재검사에서 runServer=4g, runGameTest=4g를 확인했다. 이는 검사 대상 오류이며 제품 코드는 그대로다. startup 설정 확인만 필요하므로 전체 단위검사를 다시 실행하지 않았다.


운영 runServer PID24035의 실제 VM.flags에서 MaxHeapSize=4294967296, SoftMaxHeapSize=4294967296(4GiB)을 확인했다. 포트25565가 열렸고 online-mode=true, andlist OP4 설정은 유지한다. QA8102/25611은 소유 세션 정상종료로 해제했다. UI 테스트 종료 후 bounded awake는 master가 자기 assertion만 정리한다.

04:10:14 KST 운영4GiB 서버에서 리소스팩 생성 완료를 확인했다. online-mode=true와andlist OP4 재확인,25565 유지. W255/W256 소유 awake만 종료하고 다른 assertion은 건드리지 않았다.
