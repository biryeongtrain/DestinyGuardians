# W230 워록 추가 궁극기

## 구현 범위

`warlock/well_of_radiance`(빛의 샘), `warlock/chaos_reach`(혼돈 범위), `warlock/nova_warp`(신성 차원)을 실제 플레이 가능한 서버사이드 궁극기로 등록한다. 발동은 기존 웅크리기+손바꾸기, 기본 공격은 좌클릭, 신성 차원 점멸은 웅크리기+좌클릭이다. 중앙 AbilityService의 tick/cleanup/clearAll 연결과 Combat의 무기 배율 적용은 master 소유다. 인벤토리·게임모드·영구 비행/무중력 플래그를 변경하지 않는다.

## 원본과 타이밍

읽기 전용 원본은 `/Volumes/qf-ssd/Titan-Fists-of-Havoc-2026-10-28/supers/warlock_{well_of_radiance,chaos_reach,nova_warp}/source.blend`다. animation leader가 격리 Blender에서 평가한 `timing-manifest.json`과 61 pose 출력에 연결한다. 이 worker는 원본 Blender를 직접 열었다고 주장하지 않는다. `ClassSuperModelAssets.durationTicks(path, phase, fallback)`는 순수 ceil(20TPS) 기간을 반환하며 런타임에서 시작 보간1틱을 추가한다. fallback은 보간을 제외한36/12/22,15/8,41틱이다. `beginSuper`가 지상/공중 시전 클립을 한 번 선택하고 Session.begin은 재생을 중복하지 않는다.

| 동작 | 소스 기간 | 런타임 계약 |
|---|---:|---|
| 샘 지상 시전 | 1.7667초 | 시작 보간 포함37틱 뒤 식립 |
| 샘 공중 진입/착지 | 0.5667초/1.0667초 | 13틱 진입 뒤 실제 지면 대기, 착지23틱 후 식립 |
| 혼돈 진입/루프/종료 | 0.7333초/0.0667초/0.4초 | 16틱 준비, 총80틱 채널, 9틱 종료 |
| 신성 차원 시전 | 2.0333초, 원본62프레임 | 시간 유지61pose, 시작 보간 포함42틱 |

혼돈 루프는 Blender 키가1개인 상수 포즈를 metadata 기간으로 유지한 것이다. 움직이는 리핑 루프라고 주장하지 않는다. 신성 차원의 additive charge 자료는 완전한 base motion으로 사용하지 않고, 현재 idle/move/air/attack은 animation leader가 명시한 authored 상태다. 피해 접촉 시점은 원본 이벤트로 복호화된 값이 아니다.

## 빛의 샘

실제 지면 충돌을 검사한다. 지상에서는37틱 준비 뒤, 공중에서는 진입→실제 지면 접촉→별도 착지 모션 뒤 검과 장판을 설치한다. 공중 대기는160틱으로 제한하며 바닥이 없는 곳에 떠 있는 샘을 만들지 않는다. native 중력·충돌을 유지한다. 설치 완료 즉시 시전 세션과 후방 카메라를 끝내므로 무기를 다시 사용할 수 있다.

샘은 시전 세션과 분리된600틱 필드다. 주인은 접속 connection·level·GuardianData·GuardianRuntime·실제 Loadout 객체와 장착 super ID를 캡처한다. 죽음/로그아웃/관전/차원/직업/장착 교체와 명시 cleanup은 해당 소유 필드·표시만 해제한다. 동일 직업으로 돌아와도 제거된 예전 필드는 복구하지 않는다. 동일 gameTime 반복 tick은 회복을 중복 적용하지 않는다.

반경·높이·벽 LOS 안에 있는 본인 또는 `owner.isAlliedTo(player)`인 실제 아군만 회복하고 무기 강화를 얻는다. 무관한 모든 플레이어를 아군으로 취급하지 않는다. 실제 `heal()`을 호출하며, 효과 파티클만 표시하는 구현이 아니다. `outgoingDamageMultiplier(ServerPlayer)`는 유효한 필드의 가장 큰 배율만 반환해 중첩을 막는다. master가 Combat.damage의 PRIMARY/SPECIAL/HEAVY 경로에 정확히1회 곱한다. ABILITY/SUPER 피해에는 곱하지 않는다. 필드를 나가면 이 필드의 배율은 즉시 해제된다.

소품은 canonical 지면 중심8,8,8이다. 장판은 raw XZ반경8이므로 scale(2R,1,2R), 별도 식립 검은 scale1이다. 필드 모델을 손장비로 쓰지 않는다.

## 혼돈 범위

클릭 없이 준비→자동 광선→원본 종료 모션으로 진행한다. 매 틱 현재 시야에서 유한 거리 ray를 만들고 블록 충돌점에서 자른다. ray가 교차하는 가장 가까운 적1개만 선택하므로 일직선 뒤의 적에게 관통 피해를 중복 주지 않는다. 파티클과 +Z canonical item_display 광선은 같은 종료점을 쓴다. 3틱마다 SUPER 귀속 피해를 적용한다. 준비와 채널의 이동 입력은 제한하지만 시야 회전은 계속 허용하고 기존 중력·충돌을 유지한다. 채널/소유권 종료 뒤 늦은 펄스는 없다.

## 신성 차원

42틱 발동 뒤 이동형 궁극기로 전환한다. 좌클릭1회는12틱 충전을 예약한 뒤 LOS를 통과한 적에게 반경 폭발을1회 발생시킨다. 충전 중 재입력은 무시하고 회복 간격을 둔다. 기본490틱에서 공격당5%, 점멸당3.5%를 추가 소모한다. 실제 버튼 해제를 전송하지 않는 바닐라 좌클릭 입력에 맞춰 탭→자동 완충 폭발로 매핑했다. 원작의 비충전/홀드해제 두 단계를 그대로 복제한 것은 아니다.

웅크리기+좌클릭은 현재 시야 방향으로 최대4블록 이동한다. 0.25블록마다 이전/다음 플레이어 bbox의 swept volume, 월드 높이/경계와 로드된 청크를 확인한다. 벽·천장·얇은 충돌형상을 통과하지 않고 마지막 안전 부피까지만 이동한다. 최소 이동 공간이 없으면 발동하지 않는다. 플레이어 속도·낙하 상태와 인벤토리는 보존한다. 충전 중 취소/소유권 변경은 예약 폭발과 aura를 함께 제거한다.

## 수치 출처와 잠정 범위

2026-10-28 fresh HTTP200 DDC `solar139`, `arc124`, `void129` (`/private/tmp/destiny-w230-sources/ddc-values.json`)의 Base Cooldown과 기본 지속시간을 사용한다. Chunk Scalar를 곱하지 않는다.

| 궁극기 | CD | 지속 | 직접 사용한 조건 |
|---|---:|---:|---|
| 빛의 샘 | 455초 | 설치물30초 | 무기25% 강화, 기본 수명 |
| 혼돈 범위 | 455초 | 채널4초 | 최초0.67초 무피해, 약0.13초 펄스는20TPS에서3틱으로 양자화 |
| 신성 차원 | 556초 | 기본24.5초 | 완충0.6초, 공격5%/점멸3.5% 소모 |

Minecraft HP·피해·반경·회복량은 잠정값이며 Destiny 미터/HP와 동등하다고 주장하지 않는다. 샘의 이탈 후 Radiant 잔류/소유자 공격의 원작 Super 분류/파괴 가능한 검800HP/저항/면역/빛의 보주, 혼돈 수동 취소 환급·7회 추가타, 신성 차원 비충전 발사·완충 흡인·약화 추적체는 이 배치에 구현하지 않았다. 원작 전체 부가효과 완료로 보고하지 않는다.

## 검증 절차와 상태

소유7파일만 변경하며 main·공유 helper·Gradle·실제 게임·Vision·commit은 변경하지 않는다. 행동 GameTest6개를 추가했다: 샘 실제 회복/아군 배율/시전 종료/만료, 공중 착지, epoch/죽음/복원 방지, 혼돈 자동 발사/가까운 표적/현재 조준/벽/종료, 신성 차원 단발 충전/충돌 점멸, 취소 후 늦은 피해 방지. 단순 수치별 검사 신설은 하지 않는다.

독립 javac에서 소유 Java3파일을 기존 main compiled classes와 격리된 명시적 helper API 계약 stub에 대해 컴파일해 통과했다. 이는 shared 구현을 포함한 통합 빌드나 실행 검증이 아니다. 현재 worker는 GameTest/중앙 컴파일/Vision을 실행하지 않았다. master 1차 실화면과 실패 정보를 받으면 owned delta만 수정한 뒤2차 검수를 요청한다.

### 광선 회전 보정 근거

정확한26.3 merged jar의 `DisplayRenderer$ItemDisplayRenderer.submitInner`를 javap로 확인했다. bytecode11..17이 모델 submit 전에 `Axis.YP`, `PI`, `PoseStack.rotate`를 적용한다. 현재 Qaim*Ypi 보정과 nativeYpi가 상쇄되며 canonical +Z가 조준 방향을 따른다. 폭/길이의 대각 scale은 Ypi와 교환하므로 이 상쇄를 깨지 않는다. 다만 최종 art NONE transform과 실제 렌더 결과는 master Vision에서 발사점→조준점·벽 충돌점 방향을 확인해야 한다. 근거: worker `evidence/minecraft26.3-ItemDisplayRenderer-javap.txt`.
