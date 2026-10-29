# W255 — 원본 수류탄·직업능력과 원본 시간 재생

## 범위와 원본

- 수류탄: `/Volumes/qf-ssd/Destiny-Grenade-Models-W253-2026-10-30` 읽기 전용. Fusion/Solar/Vortex/Storm의 held와 projectile 후보를 구분한다. 추출본의 단계 라벨은 실제 게임 장면으로 확정되지 않았다.
- 모션: `/Volumes/qf-ssd/Destiny-Class-Ability-Motions-2026-10-30` 읽기 전용. 18클립/72본/30fps. 별도 headless Blender에서 실제 .blend action을 평가했다. 외형은 BetterModel 플레이어 스킨 리그로 제공한다.
- 현재 플레이 가능한 높은 방벽과 치유 균열에 원본 전신 모션·준비·지면 접촉·복귀를 연결한다. 집결 방벽/강화 균열 2클립은 준비 자산이며 새 능력으로 등록하지 않는다. 다른 8개 변형은 원본 감사 기록만 유지한다.

## 1. 워크트리 준비

고정 slot4/5를 재사용한다. 갱신 전 기존 기준선 이후 변경을 현재 main과 해시 대조했다. slot4의67파일과 slot5의4파일은 이미 main과 동일했다. slot5의 과거 W230 실험3파일은 현재 main과 다르므로 이번 제품에 섞지 않고 원문과 기준선을 `/private/tmp/destiny-w255/pre-refresh-drift-preserved.zip`에 보존했다. 이 차이와 일치파일만 metadata에 반영한 뒤 안전 갱신 도구를 실행했다. reset/clean/워크트리 삭제/원격pull 없음.

## 2. 구현 계약

- `GrenadeModels.item(id)`는 held, `projectile(id)`는 비행. 3직업 실제 투척 경로를 각각 연결한다. 기존 미확보 종은 기존 임시 Explosion/Pulse 원본을 유지한다.
- 투명 shader 전용 Fusion/Solar projectile은 중복 depth/shadow/compute 패스를 제외하고 에너지 재질을 Minecraft용으로 재작성한다. 회색 preview나 원본 shader와 동등하다고 보고하지 않는다. UV0만 사용하고 NaN/Inf UV1은 가져오지 않는다.
- `ClassAbilityCast`는 준비/접촉/회복을 소유한다. 장비는 가상 손에서 비우고 실제 인벤토리를 교체하지 않는다. 발사·조준·다른 능력 입력을 회복까지 제한한다. 죽음/로그아웃/차원·클래스·로드아웃 변경/시전 중 이동·텔레포트 시 지연 발동을 취소하고 카메라·손을 복원한다.
- 높은 방벽은 시작15틱 접촉/전체29틱, 치유 균열18틱 접촉/전체36틱. W255 초기 연결값이며, 아래 원본 시간 정렬 후의 최종14/28틱·17/35틱과 구분한다. BetterModel 현재 시작 보간은1틱이다. 접촉은 원본 손목 높이 기반 Minecraft 시각 보정값이며 해독된 Destiny 이벤트가 아니다.
- 설치한 방벽/균열은 시전 종료 후 기존 수명/피해·치유 규칙으로 유지한다. 모션 중 지면이 사라지거나 장애물이 생기면 설치하지 않는다.
- 초기 버전 `guardian_hunter_w255_r1` 이후 최종 `guardian_hunter_w255_r2`를 CREATE_NEW로 설치하며 사용자 기존 BetterModel 파일을 덮어쓰지 않는다. BetterModel을 사용할 수 없을 때는 기존 선택적 표시 정책에 따라 시간 지연만 유지한다.

## 3. 검증

서버·클라이언트 결과/실제 PNG/native 입력과 서버 fixture를 구분하여 아래에 기록한다.

### 원본/정적 검수

모션 worker가 57개 입력 해시 보존,18action 실제 평가, 각 단계61포즈(조립121/181포즈), 전신 본/축/연속성 검사와 정적 검수8장을 반환했다. JUnit독립2개 통과는 변환 자산 계약만 검증하며 실게임 검증을 대신하지 않는다. 반환5파일을 시작 해시와 대조하여 통합했다.

### 기존 필드 회귀 fixture

W229의 방벽 방호/균열 치유 검사는 즉시 설치된 필드를 전제로 한다. 이들 테스트의 준비 helper만 수락된 contact callback을 1회 호출하고 cast를 정리하도록 바꾸었다. 이 fixture는 실제 대기시간 증거가 아니다. W255 새 GameTest는 정상 AbilityService 경로의 실제 tick을 기다려 지연 설치·취소·카메라/장비 복원을 따로 검증한다. 제품에 테스트 전용 즉시 설치 API를 추가하지 않았다.

### 중앙 1차 gate

클래스 변환2, W199 기준 리그 보존1, one-shot timeline4 = JUnit7/7 통과 및 compileGametestJava 성공. 첫 Gradle 명령은 --tests 옵션이 compile task 뒤에 놓여 구성 단계에서 거절됐으며 올바른 test task 옵션 순서로 수정했다. 수류탄52파일은 시작/반환 해시를 대조하여 통합했다. 각 소품392~920요소,512² atlas. 첫 정적 검수의 체크무늬 에너지는 연속 에너지 표면으로 수정했다.

### 1차 실게임 검수와 수정 요청

격리 Danmo 4GB/OpenGL에서 native double-sneak로 방벽/균열, native swap-offhand로 Fusion/Solar/Vortex/Storm을 시전하고 실제 PNG를 남겼다. 짧은 held 모델은 별도 server tick freeze/step3·8 fixture로 확대 관찰했다. 이 fixture를 실제 native 입력 증거로 세지 않는다. 증거: `/private/tmp/destiny-w255/r1/`. 신규 class3·기존 field2·전직업 throw1 = GameTest6개 최종 통과. 첫 방벽 검사는 Peaceful에서 Husk가 사라져 실패했으며 Normal로 고친 재실행을 별도 보존했다.

수류탄 unit4개 중2개는 MC26.3 ItemStack component 미결합으로 실패했다. 테스트 bootstrap만 기존 sword fixture와 같은 방식으로 보정했다. 제품 ItemStack 코드를 이 오류 때문에 변경하지 않았다. 실제 PNG를 두 worker에게 전달하여 포즈/접지/에너지 표면의2차 검수를 요청했다.

### 사용자 추가 요청 — 원본 시간과 실제 시전 동기화

처음 사용자 답변에 따라1.35배속을 검토했으나, 후속 지시 ‘모션과 실제 시전 시간이 같아야 하고 가능한 한 원본 시간을 따라갈 것’을 우선한다. 임의 배속 코드는 전부 되돌렸고 검토 delta는 `/private/tmp/destiny-w255/superseded-speed135/`와 worker timing135 폴더에만 보존한다. 원본 길이와 접촉 시각·카메라/입력잠금을 같은 시간축으로 맞춘다. 공유 클록은40회 평가/20회 발행·display1틱 보간을 유지한다.

R1 후반 실제 FPS가8~10인 구간을 발견했다. 격리 QA의 Danmo FpsReducer가 idleFps10 설정이었다. client를 종료한 후 해당 QA 설정만 백업하고 enableFpsReducer=false로 재검수한다. 일반 Danmo 사용자 프로필은 수정하지 않았다.

원본 class 시퀀스 길이는 방벽40/30초, 치유 균열51/30초다. generator 문서의 entry2틱과 실제 공통 PlayerAnimations entry1틱이 달랐으므로 교정 중이다. 최소 손목높이를 접촉 후보로 삼은 점은 게임 이벤트 해독과 구분한다. dense keyframe의 엔진 양자화가 시간을 늘리는지 실제 파싱/재생을 조사한다.

### 원본 시간 보존 수정

실제 BetterModel3.5.1 AnimationStateHandler를 별도 Java probe로 실행했다.1초 곡선을20/40구간으로 주면43평가(2entry+1completion 포함),60구간은63평가,120구간은123평가,200구간은203평가가 걸렸다. 25ms보다 짧은 구간도 최소1회 평가를 소비하므로 키를 늘리는 것만으로 부드럽게 만들면 실제 재생은 늘어난다. 이 결과는 probe 입력에 대한 엔진 검사이며 설치된 parser 곡선의 실제 수명은 아래 GameTest로 별도 확인한다.

`SourceAnimationGrid`는 원본 JSON/Blender61포즈를 수정하지 않고 설치할 owned limb의 numeric linear 곡선을25ms 공통 격자에 재평가한다. 길이와 시작·마지막 포즈는 유지하며 엔진에서 한 평가당 정확히 다음 시간 표본을 읽게 한다. 원본 소스의 비선형/효과 채널은 지원 범위를 넘겨 변환하지 않는다. 새로운 설치본은 hunter `guardian_hunter_w255_r2`, classes `guardian_classes_w255_r1`이고 기존 설치파일은 보존한다.

클래스는 source contact seconds와 duration seconds를 작은 runtime timing자산으로 내보내서 `ClassAbilityTiming`이공통 entry1틱을 더한다. 높은 방벽 접촉14틱/전체28틱(원본1.333초+최대1틱 양자화), 치유 균열17/35틱(원본1.7초+entry1틱)으로 모션과 field/camera/input lifetime을 정렬한다. 임의1.35배속은 사용하지 않는다.

### 원본 시간 보존 gate

SourceAnimationGrid unit3개 통과: 실제 BM 상태기로 촘촘한1초 곡선의123평가 회귀를 재현하고, 격자 보간 후43평가(40본문+2entry+1completion)를 확인했다.93개 imported clip의 엔진 시간 상한·길이 보존과 class contact/전체 길이 연결도 검사했다. 수류탄4/클래스 변환2/W199원본1/pose샘플2 통과. 첫 통합 targeted14개 중 기존 설치모델 검사1개가 runtime curve에도61포즈를 요구하여 실패했다.61포즈는 원본 자산에 보존하고 설치본은 엔진 격자라는 새 계약에 맞춰 해당 검사만 갱신했다.

### 최종 전체 gate 및 추가 리뷰

중앙 전체 JUnit2207개 중2203개 통과,4개 실패. 실패는 이전W254에도 기록된 Austringer/Mindbender/WeaponSurfaceW115/WeaponSilhouetteW112 자산 계약4개와 동일하며 이번 scope의 새 실패는 없다. compileGametestJava와assemble 성공. 결과 `/private/tmp/destiny-w255/full-gate.json`. 전체 gate 뒤 비숫자 expression/effect 곡선을 원본 보존하도록 guard와 회귀 검사를 추가하여 targeted 재검사한다.

worker가 실제 BM parser bytecode도 추가 검토했다. parser가0과length 키를 재생성하므로 JSON0키 제거로 반복 경계의25ms 소비를 해결할 수 없다. 현재 설치용 격자는 원본 시간·끝 포즈를 보존하며, 반복 경계의25ms 및 비정수25ms 끝점 양자화는 잔여 한계로 남긴다. 한 클립은 시작/끝 포즈가 다르므로 포즈 시간을 임의 압축하거나 모든loop의0키를 무조건 건너뛰는 공통 엔진 패치는 적용하지 않았다. 시전 one-shot과 반복 locomotion의 오차를 구분하며60fps/원작과 완전 동일하다고 주장하지 않는다.

### R2 실제 파싱·실화면 결과

비숫자/effect guard 추가 후 SourceGrid4/4와compileGametestJava/assemble 성공. 실제 parsed one-shot55클립은 원본 ceil(length×40)+entry2에 completion평가1회가 추가되는 것으로 모두 확인됐다. dense key 수만큼 길어지는 회귀는 없다. `r2/parsed-clock.json` 보존.

R2 GameTest는 class3/field2/throw1/parsedclock1/clockpublication1/nova1 =9개 통과. 첫 runner의 startup 조건이 로그인 로그를 기다려 명령 제출 전 timeout됐으며 서버Done+BMloaded로 수정했다. clockpublication의 ID를 잘못 넣은 두 명령은 selector no match이며 테스트 실행으로 세지 않는다. 실제 ID w198publishes로 확인 후 통과했다. Titan3궁 회귀는 기존 즉시수류탄 가정 때문에 실패했다. 정상 ThrowTimeline 복귀를 기다리는 fixture로 수정해 R3에서 해당 검사만 재검사한다.

Danmo4GB/OpenGL R2 실제 native class2/grenade4 시퀀스가 모두 성공하고 release/빈heldKeys를 확인했다. class 접지·방벽/균열 생성·FP총기 복귀를 실제 PNG에서 확인했다. offline3P는 template fallback스킨이라 온라인 사용자 스킨 검증으로 세지 않는다. 수류탄 Solar/Fusion비행은 보였으나 Vortex/Storm의 짧은 held/비행 프레임이 부족해 단계 fixture를 추가한다. 실제 FPS snapshot5~43 구간이 있어60fps 부드러움 인증이 아니다.

R2 native6개 완료 뒤 클라이언트 로그는03:16:09 Stopping, 이후03:16:30 shutdown watchdog을 기록했다. 종료 요청의 출처는 확인되지 않았다. Stopping 전 OOM/게임중 fatal exception은 확인되지 않았으며 제품 모션 크래시로 단정하지 않는다. 보고서와 로그를 보존하고 소유 client 종료/port 해제를 확인한 뒤 잔여 시나리오용 R3를 준비한다.

### R3 타이탄 준비 fixture 재검증

기존 Titan3궁 검사의 ordinaryFlightCoexists는 즉시투척 가정이었다. 수락된 정상 수류탄의 DURATION_TICKS+1 이후 실제 비행이 살아 있는 상태에서 궁극기를 시작하도록 fixture만 수정했다. compileGametestJava 성공 및 해당 GameTest 재실행 통과. R2/R3 합계 고유10개 모두 최종 통과하며 첫 실패도 별도 보존한다. 제품 투척 대기·복귀 코드는 이 테스트를 위해 변경하지 않았다.

### R3 궁극기 증거 제외 및 R4 재개

R3 첫 궁극기4종 캡처는 준비 오류로 제외한다. `guardian reset`은 쿨다운만 초기화하며 에너지를 채우지 않는다. 실제 PNG는 일반 무기/ADS였고 시전 성공 증거가 아니었다. `guardian super 100 WeaponW129QA`를 추가한 재검증은 사용자 중단으로 결과 파일을 남기지 못했다. 재개 시03:39 KST에8102/25611/25565 포트가 모두 비어 있음을 확인했다. 기존 socket/log는 보존하고 새R4 세션을 시작했다.

R3 별도 tick freeze/step fixture에서 Solar held와 Vortex/Storm held·flight는 보였다. Fusion 짧은 단계는 프레임 도착이 불명확하여 R4에서 대기시간을 늘려 확인한다. 이 단계 fixture는 native 투척 증거와 구분한다.

R4는 Computer Use로 실제 데스크톱을 확인했고 새3시간 상한의 W255 소유 awake를 적용했다. 기존48시간 요청과 별개이며 일반 프로필/인증/잠금 설정은 변경하지 않는다. 기존 전체 gate와 유효 R2/R3 결과는 반복하지 않는다.

### R4 최종 시전 확인

첫 charged 시퀀스에서는 헌터 아크가 실제 발동했지만, 끝나기 전 class/subclass 변경이 서버에서 거절돼 나머지3개 label이 실제 직업과 일치하지 않았다. 이 캡처 묶음도4종 성공으로 세지 않는다. `supers_verified.py`는 매 시나리오 전후 원래 카메라 복귀를 기다리고, 직업·하위직업 변경 ACK와100%에너지를 검사한다.

최종 verified4종(헌터 아크/공허, 타이탄 아크, 워록 솔라)은 native sneak+swap 입력, 각 클래스별 궁극기 sound event 로그, remote camera 상태, 실제 PNG로 시전을 확인했다. 종료 후 모두 cameraIsPlayer=true, leaseActive=false, heldKeys=[], nativeInput 중립으로 복귀했다. sound 로그는 청취 증거가 아니다. 공허는 자동 발사 후 먼저 복귀했으며 뒤의 attack 입력은 일반 ADS로 보인다. 이를 별도 궁극기 공격으로 세지 않는다.

실제 캡처 FPS 범위는16~63이며 낮은FPS 구간이 있어 화면의 연속60fps를 인증하지 않는다. `super-verified-sheet.png`에서 아크 지팡이/공허 활/타이탄 강타/새벽의 칼날 본체 및 효과를 확인했다. **3인칭 궁극기 중1인칭 무기가 함께 남는 표시 문제도 발견했다. 이번 시간축 수정으로 해결됐다고 하지 않으며 발생 시점·원인은 아직 특정하지 않았다.** 오프라인 템플릿스킨은 온라인 유저 스킨 검증과 구분한다.

Fusion 단계 fixture는 충분한 렌더 대기 후 phase3에서 손 위 구체, phase8에서 분리된 비행 소품과 궤적을 확인했다. `fusion-held-phase3.png`, `fusion-flight-phase8.png`. 원본 메시를 Minecraft 재질로 표현한 결과이며 원작 셰이더와 동일한 에너지 표현이라고 하지 않는다.

03:45 KST tick unfreeze ACK 및 최종 카메라/lease/native 중립을 확인하고 소유 QA client와 server에 정상 종료를 요청했다. 원본 시간 보존 수정, 신규 class 시전 및 수류탄 자산의 범위로 커밋한다. 남은 표시 문제와 반복 경계25ms 한계는 완료 주장에 포함하지 않는다. 상세 요약은 `verification-summary.json`, 자동 gate는 함께 보존한 JSON을 참조한다.

후속: 위에서 발견한3인칭 중1인칭 무기 중복은 [W256](../w256/README.md)에서 수정·재검증했다. 최초 W255 캡처는 수정 전 증거로 그대로 보존한다.
