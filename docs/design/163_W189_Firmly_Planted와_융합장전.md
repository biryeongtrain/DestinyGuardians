# W189 — Firmly Planted / 에렌틸·코리올리 장전

사용자 지정 [DDC](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4)의 Weapon Perks97행을 수치 우선 원문으로 적용한다. 기본형280464955만 구현한다. enhanced3920370755와 노란 증가값은 구분한다. 이 행에는 PvE/PvP 분리가 없고 기본 수치에 물음표가 없다. 조회 HTML·행 원문·공식8소켓·동반선택32개·원시handling곡선은 [원문 기록](../../art/weapons/w189/firmly_planted/SOURCE.md)에 있다.

| 실제 웅크린 상태 | 안정성 | 조작성 | 명중률 원뿔 | 원뿔 증가량 | 수평 반동 |
|---|---:|---:|---:|---:|---:|
| 일반 |+20|+30|×0.6|×0.83|×0.2|
| 융합소총 |+10|+15|×0.8|×0.915|×0.6|

`Entity.isCrouching()`은26.3에서실제Pose.CROUCHING을판정한다. shift flag나custommodel ADS만으로효과를주지않는다. 현재포트의shift가웅크림과ADS를함께유발하는조작상결합은유지한다. actualcrouched hip-fire도유효하다. 즉시stand/선택해제/소스이동/super등에서현재passive권한을다시읽는다. 실제장착originalobject만허용하고copy/backpack/offhand/count2는제외한다. 상태세션/attachment/timer/HUDproc행은추가하지않는다.

생산반동/확산/피격은기존W44의Minecraft튜닝함수이며원작엔진정확각도·cone단위를주장하지않는다. 안정성은기존안정성합산에들어가고cone/growth/yaw는각각따로적용한다. yaw0.2를수직kick에또곱하지않는다. 실제damage/ammo/reload에는새보너스를주지않는다.

FP+ArcEC(강철깃털)와FP+Frenzy(꿈의파괴자)는실제선택된별도소켓의실제활성값만합산한다. 원소축전지의기존pure active-class SUPER selector를재사용한다. FP소스검증이genuine incoming/outgoing을이미확인하므로selectedslot변경전에도허용한다. rawstat을합산·100cap→historicalrawcurve→scalar→20TPSceil1회,Snapshot은배교자진입만,Quickdraw는기존outerpolicy를유지한다. acceptedHandlingdeadline은이후stand로다시계산하지않는다. 수치의틱환산은원작프레임관측값과구분한다.

장전두제품은별도dirty-CoWworktree에서동일무기실제영상·리핑구조를참조한다. 기존canonicalUV/ADS/3P/게임장전시간/탄약/음원은보존하고실제binding이있는동안만21샘플·2파지·좌우FP를사용한다. whole-mag경로는43개로확대한다. 실제handIK/새3Particulatedreload를완료로세지않는다.

검증진행상태와실패/한계는[W189 QA](../qa/2026-10-27/w189/README.md)에최종기록한다. 전체무기시스템goal은진행중이다.
