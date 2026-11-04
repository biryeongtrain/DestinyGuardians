# W85 — 피격 플린치와 No Distractions

## 범위와 원칙

- Minecraft 26.3 Fabric/Polymer 서버사이드. 바닐라 상대 회전 패킷만 사용하며 필수 클라이언트 모드, 이동 위조, 순간이동, 자동 표적 추적을 추가하지 않는다.
- 기존 65무기·소리·모델·탄약·장전·Salvo 양손 파지/해제 추정은 보존한다. Sword/Glaive는 기존 전용 동작을 유지하며 이번 총기 ADS 플린치 대상이 아니다.
- 모든 수치가 최신 Destiny 2026 사양과 동일하다고 주장하지 않는다. [연구 결과](../../art/weapons/w85/reference-notes.md), [기계 판독 자료](../../art/weapons/w85/data/research.json)에 원문·버전·확인 한계가 있다.

## 출처 기반 동작

Izanagi’s Burden 3211806999의 고정 base No Distractions 2866798147만 구현한다. Enhanced 0.9초나 다른 전설 무기에 자동 부여하지 않는다.

1. 실제 ADS 입력 시작부터 **1초간 사격 없이 조준**하면 활성화한다. 20TPS에서 20 경과 tick이며 첫 관찰을 tick0으로 잡는다.
2. 활성 중 받는 플린치에 **0.65배**를 곱한다. 발사 자체는 이미 얻은 효과를 지우지 않으며 ADS 종료로 사라진다.
3. HUD는 활성 때만 `No Distractions` 행을 표시한다. 잔여 시간이 없는 효과에 가짜 초 타이머나 장전된 아이템 영구 태그를 만들지 않는다.
4. 2022 공식 Stability100 저항 endpoint: AR/SMG/Bow25%, Pulse/Scout/Sidearm/MG20%, HC/Trace15%, Fusion/Shotgun/Sniper/모든GL/LFR/Rocket10%. 역사적 자료이며 2026까지 불변 확인은 아니다. 효과는 잔여 플린치끼리 곱한다.

## 명시적 로컬 정책 — 원작 확정 사실 아님

- pre-proc 유료 발사는 quiet timer를 해당 시각부터 다시 시작한다. 정확한 reset/pause와 임계 tick 처리 원작은 미확정이다. 같은 tick에 먼저 경과 조건을 평가한 뒤 유료 발사를 처리하므로 이미20tick 경과했다면 활성 상태로 발사한다. 거절된 trigger/dry fire는 quiet timer를 바꾸지 않는다.
- reload/skill/handling이 ADS를 중단하면 reset한다. 서버의 기존 suspend 규칙에 따라 crouch를 놓아야 재진입한다. 키가 계속 눌린 상태를 실제 ADS 유지로 간주하지 않는다.
- 검증된 hotbar 변경, 실제 인벤토리 변이, 비Guardian의 실제 offhand swap, input shift-release를 관찰한다. 동일 tick에 원래 ItemStack으로 돌아와도 조준 연속성은 끊긴다. 거절된 packet/화면 열기만으로 stow를 만들지 않는다.
- Stability 저항은 `(clamp(stability,0,100)-20)/80 * familyEndpoint`로 보간/외삽한다. 아래20은 작은 penalty다. 공식 자료가 이 정확한 식을 제시한 것은 아니다.
- 기본 각도는 `(.20 + 1.80*clamp(actualLoss/maxHP*2,0,1))*(1+.35*ADSprogress)`도다. 여기에 저항을 곱하고 session당 tick2.5도 예산으로 제한한다. 수평은 피해 출처의 측면 부호×0.30이며 수직은 위로 튄다. 이것은 원작의 정확한 피해량·zoom·방향 함수가 아닌 안전한 초기 feel 값이다.
- 이후 카메라를 강제로 원위치 복귀시키는 task는 없다. 마우스 입력과 충돌하거나 적 머리로 돌아가는 aim assist를 만들지 않는다. 발사 반동과 별도로 실제 서버 조준도 같은 delta로 변경한다. pitch 상한에서는 clamp 후 실제 적용 delta만 전송한다.
- entity-attributed 실제 impact만 적용한다. source entity(없으면 direct entity)가 본인/다른 level이면 제외하고 entity 없는 fall/fire/drowning/void/DOT는 제외한다. entity가 남은 DOT/area는 impact 정책을 따르며 원작 source-type matrix와 동일하다고 하지 않는다.
- Resilience/armor-mod 저항과 2024 Crucible 전용 Primary15% 변경은 보편적 PvE 값으로 섞지 않는다. 이번 버전은 별도 Crucible mode/현대 전체 패치 감사가 아니다.

## 실제 피해 연결

`Player`는 `LivingEntity.actuallyHurt`를 override한다. 따라서 새 `PlayerDamageMixin`은 **Player.actuallyHurt**를 감싸고 armor/magic/absorption 이후의 실제 HP+흡수량 감소를 읽는다. `hurtServer`의 요청량이나 Fabric AFTER_DAMAGE의 중간 amount를 실제 debit으로 오인하지 않는다.

- dodge ALLOW_DAMAGE 거절, vanilla iframe, zero/full-block/immune 실제무손실은 새 회전을 만들지 않는다.
- absorption만 감소하는 shield hit도 대상이다. 죽거나 spectator/removed/disconnected, super, 장비 사용 불가, reload/handling, CameraViews·SuperCamera의 잔여 회복 카메라·본인 아닌 native getCamera의 외부 카메라 소유 중에는 적용하지 않는다.
- victim별 중첩 측정 stack은 child의 signed delta를 parent에서 빼 같은 nested 피해를 두 번 세지 않는다. 예외 시에도 finally로 frame을 정리하고 완료하지 않은 손상 callback에서는 추가 회전을 보내지 않는다.
- ADS FOV를 다른 소유자가 인계하면 해당 FOV를 덮어쓰지 않고 perk/ADS를 중단한다. death/disconnect/world-change/server-stop의 기존 WeaponAiming cleanup도 새 state를 제거한다.

## 검증 경계

[W85 QA](../qa/2026-10-25/w85/README.md)에 실제 완료한 gate와 실패 원본을 별도로 기록한다. pure 수학·clock 시험, native hurtServer GameTest, rotation packet codec, HUD asset/source/JAR/pack 검증은 각각 다른 증거다.

직전 native Vision의 SDL 초기 출력 정지에 대한 새 외부 상태 확인 없이 동일 launch를 재시도하지 않는다. 이번 headless 결과를 실제 framebuffer/키보드 입력/체감/음향 검증으로 보고하지 않는다. 출처의 sparse gameplay storyboard도 원작 각도나 frame timing 측정이 아니다.
