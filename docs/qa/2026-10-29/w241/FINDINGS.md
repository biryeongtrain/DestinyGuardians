# W241 읽기 전용 조사: 지향사격 탄퍼짐과 공중 ADS 정확도

조사일: 2026-10-29 KST. 저장 범위: /private/tmp/destiny-w241/research 만.
repo /Users/qf/IdeaProjects/DestinyGuardians 는 읽기만 했다. 게임창, 서버, 빌드 조작 없음.

## 결론
- 사용자 요구: 무기별 랜덤 지향사격 + 공중 ADS 탄퍼짐, AE >= 100에서는 추가 공중 penalty = 0.
- 이 조건을 충족하도록 AE를 [0,100]으로 clamp하고 100 이상은 명시적으로 추가 오차 0으로 처리하는 것은 사용자 지정 동작이다.
- 추가 penalty 0은 원게임에서 기본 탄퍼짐, 펠릿 패턴, 반동, 중력까지 전부 0이라는 뜻이 아니다. 공중 ADS를 완전 직선으로 만드는 구현은 그 요구에 따른 별도 게임 설계로 명시한다.
- DDC 확인 탭에서 무기별 기본 hip 각도(deg), 무기군 전체 기본각 표, 현행 AE -> 오차각 전체 곡선을 찾지 못했다. 이 값과 랜덤 분포, 회복속도, 상한, Minecraft 환산은 local tuning.
- 예를 들어 모든 무기군에 동일한 선형 1-AE/100을 적용하면 local tuning이다. 원게임 전체 확정 곡선으로 표기하지 않는다.

## DDC 탭/행: 기준 시트
https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4

Weapon Perks, gid=1662574278:
- 120행 Hip-Fire Grip: 지향사격 중 Accuracy Cone Size -30%, Stability +25, Aim Assist +15, Precision Angle Threshold +2.7도. 사거리 계열 +20%. +2.7도는 탄퍼짐 각도가 아닌 정밀 조준 보정 문턱이다. 강화형도 accuracy cone 감소율은 동일. Shotgun/Sniper/Fusion/The Last Word는 damage falloff 증가 제외.
- 297행 Freehand Grip: 기본/강화 hipfire Accuracy Cone Size 모두 -30%. 기본 ready duration 0.95x, 강화 0.?x는 미확정 유지.
- 298행 Icarus Grip: AE +15, 강화형 Handling +5.
- 12행 Air Assault: 기본/강화 수동 AE +10/+12; 처치 중첩당 +30/+32, 5초, 최대 2중첩; 공중 처치 2중첩, 추가 처치 갱신, 수납 제거.
- 326행 High-Impact Frame: ADS 및 이동속도 <=2.8m/s에서 Accuracy Cone Size -20%, Growth -17%. 이동조건 충족 시 공중에서도 적용.
- 335행 Precision Frame (Hand Cannon): AE +25, ADS 이동 페널티 10% 감소, 수평 recoil yaw -20%. manifest 기본 AE와 프레임의 동적/고유 보너스는 구별해야 한다.
- 157행 Opening Shot: 첫 발/버스트에 주무기/중화기 cone size -5%, growth -10%; 특수무기 size -2.5%, growth -5%; 발사 후 3초 쿨다운. 기본각 근거가 아니라 기존 원뿔에 대한 비율 보정이다.
- 328행 Legacy PR-55: cone size -70?%, Stability +30?, Precision threshold +1? 등은 미확정. 확정 hip 기본각으로 변환 금지.

Exotic Weapons, gid=441434520:
- 28행 The Last Word: hip 적중 Fan Fire 4초/최대4중첩, cone size -5/-10/-15/-20%. 기본각은 기재되지 않았다.

Exotic Armors, gid=1500097863:
- 73행 Lion Rampant: 수동 AE +50, Primary hip cone size -30%. Precision threshold +2?도는 미확정. DMT/Last Word/Tommy 예외가 있으므로 모든 무기에 동일한 bonus를 일반화하지 않는다.

Game Mechanics gid=1800463143 (302 parsed table rows), OLD Game Mechanics gid=135237481 (250 parsed table rows)도 조회했다. airborne 문자열은 Air Superiority/Grounded 활동 수정자에만 걸렸고 AE 곡선 표는 발견되지 않았다.
조회 HTML 및 정확한 행 텍스트는 ddc-sources.json, ddc-selected-rows.json, 각 gid.html/json에 저장했다. HTML은 cell merge, 원문 강조/강화 기호, 빈값 보존용이다. JSON은 원본 행 번호를 첫 필드로 보존한다.
XLSX export는 HTTP401: 공개 HTML을 직접 조회했으며 시트 수정은 하지 않았다.

## Bungie 공식 보충 근거: 반드시 역사적 버전을 구분
- 2022-04-21 (https://www.bungie.net/7/en/News/article/51250), Airborne Gunplay:
  당시 HC 추가 공중 오차는 AE0=0.450도, AE60=0도; Sniper AE0=2도, AE60=0.8도, AE100=0도.
  이는 당시 버전의 추가 공중 오차이고, 현재 hip 기본각이나 2026 현행 절대각이 아니다.
- 2022-05-05 (https://www.bungie.net/7/en/News/article/51319), Airborne Effectiveness:
  AE는 0~100. 당시 대부분 0~100 선형, Primary accuracy penalty는 0~60 선형/60~100은0이라는 설명.
  따라서 해당 역사 버전만 수학으로 옮기면 HC 0.450*max(0,1-AE/60), Sniper 2*max(0,1-AE/100)도라는 유도가 가능하다. 이는 문장과 앵커값으로 유도한 식이며 DDC 현행 확정식이 아니다.
- 2023-01-24 Hotfix6.3.0.5 (https://www.bungie.net/7/en/News/article/hotfix_6_3_0_5):
  Primary 추가 공중 accuracy penalty 감소율은 HC/Sidearm60%, AR/Scout/Pulse/SMG20%, Bow30%.
  Sniper/Slug base penalty50% 감소, Pellet Shotgun accuracy penalty 제거.
  Precision aim threshold의 지수 곡선은 aim assist/헤드샷 보정의 곡선이므로 탄퍼짐 곡선으로 사용하지 않는다.
- 2023-10-17 Update7.2.5 (https://www.bungie.net/7/en/News/Article/patch-7-2-5):
  Sniper/Precision Slug 추가 공중 accuracy penalty20% 감소. Pellet shotgun airborne spread penalty20% 감소.
  accuracy cone과 pellet spread는 서로 다르다. 2023-01 제거와 2023-10 spread 감소는 같은 항목을 두 번 계산하는 근거가 아니다.
- 위 공식 문서는 web search/open/find로 확인했다. 직접 urllib로 받은 bungie-*.html은 1301바이트 공통 JS shell이므로 기사 원문 확보 성공으로 간주하지 않는다. bungie-sources.json에 명시했다.
- 최신까지 모든 패치 누적을 전수 검증한 것이 아니므로 이 역사적 절대각을 현행 확정값으로 이식하지 않는다.

## 로컬 공식 manifest / characteristics 65종 전수
- 원본: art/weapons/w40/provenance.json이 가리키는 공식 inventory cache, run/private-sources/w73/bungie-items.json.
- manifestVersion: 245114.26.10.13.2000-1-bnet.66137 (Oct13 pinned snapshot; 최신 network manifest를 새로 받은 것은 아님)
- SHA256: b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c
- 비교: src/main/resources/destiny/weapons/w40-characteristics.json 63종 + w83-exotics.json 1종 + w84-exotics.json 1종.
- hash2714457168의 stat definition 이름: Airborne Effectiveness.
- 총65종 / 해시 존재60종 / 누락5종 / 공식 cache와 characteristics 값 불일치0.
- 누락5종 모두 Sword: abide_the_return, goldtusk, crown_splitter, falling_guillotine, temptation_s_hook. 누락은 0이 아니며 null로 보존했다.
- 경이 원문별도: art/weapons/w83/references/official-ace-item-raw.json AE14; art/weapons/w84/references/official-izanagi-item-raw.json AE6. cache 및 packaged characteristics와 일치.
- 65개 전체 값/무기군/프레임/아이템hash/존재 여부/일치 여부: ae-65.csv 및 ae-65.json.
- 이는 기본 manifest 스탯이고, 퍽·갑옷·서브클래스·프레임 보너스까지 합산한 최종 AE가 아니다.

## 구현 담당자에게 반환할 경계
- 무기별 기본 hip spread, ADS 기본 spread, AE<100에서의 공중 최대각/중간곡선, 랜덤 분포는 local tuning으로 표기.
- AE>=100 공중 추가 penalty=0은 사용자 명시 요구. Hip-fire Grip의 +2.7도 precision threshold를 hip spread로 사용 금지.
- Sword AE missing을0으로 확정하지 않는다. ADS 없는 무기와 projectile 고유탄도, shotgun pellet pattern을 별도 취급한다.
- 데이터 조사만 수행했으므로 테스트/빌드/실게임 QA는 실행하지 않았다.
