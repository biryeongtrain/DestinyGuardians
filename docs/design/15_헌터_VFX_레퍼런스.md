# 헌터 VFX 레퍼런스 — H13 조사 전용

조사일: 2026-10-22. H12 다음 단계의 **시각 자료 조사**이며 구현 명세 확정이나 코드·모델 변경이 아니다.
후속 구현과 최종 QA는 [16. 헌터 VFX 구현](16_헌터_VFX_구현.md)에 별도로 기록했다.
목표는 일반 SF 효과보다 실제 Destiny의 속성별 색·명암·실루엣에 가까운 lowpoly VFX 방향을 확보하는 것이다.

## 1. 확보 결과와 증거 등급

**Arc·Solar·Void를 포함한 실제 Destiny 시각 자료 6장을 다운로드하고 직접 육안 확인했다.**
이 중 이름이 명시된 능력의 게임 스크린샷은 소이와 소용돌이 2장이다.
Arc는 작가 포트폴리오의 Hunter VFX 표지와 Flashbang Grimoire 카드로 확인했다.
Arc 자료는 실제 Destiny 이미지이나, 요청한 연속 타격의 착탄 프레임이나 섬광탄 폭발의 게임플레이 캡처로 확정하지 않는다.

| 등급 | 의미 | 이번 조사 |
|---|---|---|
| A | 능력 이름에 연결된 실제 게임 스크린샷을 육안 확인 | Incendiary, Vortex. 정확한 게임 버전·시각은 미상 |
| B | 실제 Destiny 작가 게시 표지 또는 공식 게임 카드 이미지 확인. 해당 개별 능력의 동작 검증과 구분 | Dave Samuel 표지 3장, Flashbang 카드 |
| C | 페이지 설명·검색 메타데이터만 확인 | Combination Blow, Solar knife 변형, Snare Bomb의 동작 설명 |
| 제외 | 일반 SF·팬 모델 또는 작품 이미지 미확인 자료 | Sketchfab 검색 결과. 실제 Destiny VFX 근거로 사용하지 않음 |

등급 A도 영상 시간 분석·최신 패치 검증·원본 제작 에셋 확보를 뜻하지 않는다.
**프레임 간 타이밍을 측정한 영상은 없다.** 아래 시간 순서는 출처의 동작 설명 또는 별도로 표시한 연출 제안이다.
초·프레임·FPS·정확한 지속시간은 확정하지 않는다.

## 2. 직접 확인한 핵심 프레임

### 2.1 Arc — Dave Samuel의 Hunter VFX 표지 [B]

- 작품: [Dave Samuel — Destiny 2 | Hunter Abilities VFX](https://www.artstation.com/artwork/31lkyE)
- [직접 확인한 공개 표지 이미지](https://cdna.artstation.com/p/assets/covers/images/100/289/882/smaller_square/dave-samuel-dave-samuel-artstation-hunter-thumbnail.webp?1782417815)
- 로컬 증거: `/tmp/destiny-h13-vfx-refs/as-hunter-cover.webp` (400×400).
- 출처 귀속: 작품 게시자 Dave Samuel, Destiny 2 이미지의 게임 권리 귀속 Bungie. 개별 효과의 제작 분담은 상세 본문 미열람으로 확인하지 못했다.

**보이는 특징:** 몸을 낮춘 Hunter와 뒤쪽으로 길게 뻗은 봉 형태의 무기가 보인다.
인체의 어두운 덩어리는 남고, 몸 윤곽·팔·무기 주변에 가는 불규칙 전격 선이 걸린다.
배경을 덮는 넓은 청백색 발광, 더 가는 방사형 입자 선, 바깥의 청회색이 층을 만든다.
전격은 굵기가 일정한 장식용 원이 아니라 분기·꺾임이 있는 선으로 읽힌다.

- 팔레트: 청백색 최고광 → 옅은 cyan/하늘색 광륜 → 낮은 채도의 청회색 주변부 → 어두운 몸 실루엣.
- 실루엣: 인체와 긴 무기를 가는 전격이 강조하는 구조. 전체를 불투명한 파란 구로 덮는 형태는 이 프레임의 특징을 잃는다.
- 타이밍: 정지 표지 한 장이므로 준비·타격·잔광의 길이와 순서를 판정할 수 없다.
- 한계: 봉이 보이는 Arc 계열 이미지다. **Combination Blow 주먹 타격의 직접 증거가 아니다.** 맨손 능력에 봉·창을 추가하는 근거로 쓰지 않는다.

### 2.2 Arc — Flashbang Grimoire 카드 [B]

- [파일 출처·이력](https://www.destinypedia.com/File:Grimoire_Flashbang.jpg)
- [직접 이미지](https://destiny.wiki.gallery/images/0/0c/Grimoire_Flashbang.jpg)
- 로컬: `/tmp/destiny-h13-vfx-refs/wiki-flashbang-grimoire.jpg` (560×728).
- 귀속: Bungie의 Destiny Grimoire 이미지, Destinypedia 제공. 개별 작가 미확인.

**보이는 특징:** 오른쪽 아래에 큰 청백색 빛 덩어리가 있고 그 앞의 인물은 어둡게 남는다.
얇은 청색 전격, 소수의 길쭉한 빛 조각, 넓게 번지는 저채도 파란 빛이 보인다.
중앙의 수류탄 도형은 카드에 겹친 그래픽으로 보이므로 실제 폭발 구조나 소품으로 해석하지 않는다.

- 팔레트: 거의 흰 청색 중심, 밝은 하늘색 번짐, 짙은 남청색 외곽.
- 실루엣: 작은 파편 다발보다 **넓은 밝기 변화와 대비**가 우세하다. 카드 프레임·엠블럼은 VFX 대상에서 제외한다.
- 시간 근거 C: [Flashbang 설명](https://www.destinypedia.com/Flashbang_Grenade)은 첫 충돌 후 한 번 튀고 곧 폭발한다고 서술한다. 실측 지연시간은 없다.
- 한계: Destiny 1 카드의 정지 표현이다. 실제 Destiny 2 Hunter 폭발 반경·화면 눈부심·입자량을 확정할 수 없다. Titan의 Touch of Thunder 추가 바운스 폭발을 Hunter 기본 동작으로 가져오지 않는다.

### 2.3 Solar — Incendiary Grenade 폭발 [A]

- [능력 페이지](https://www.destinypedia.com/Incendiary_Grenade) · [파일 이력·권리 안내](https://www.destinypedia.com/File:Incendiary_Grenade.jpg)
- [직접 게임 스크린샷](https://destiny.wiki.gallery/images/1/1f/Incendiary_Grenade.jpg)
- 로컬: `/tmp/destiny-h13-vfx-refs/wiki-incendiary.jpg` (1016×292).
- 귀속: Bungie / Destiny 게임 이미지. Destinypedia 업로더 WizardWolf는 파일 게시자이며 효과 제작자로 확인된 인물이 아니다.

**보이는 특징:** 가로로 넓은 황백색 중심에서 가늘고 긴 불꽃이 바깥으로 튄다.
중심은 노랑·흰색, 중간은 주황, 넓은 번짐은 적색이다. 가장자리에는 드문 불꽃 덩어리와 휘어진 화염 선이 보인다.
어두운 배경 때문에 붉은 광륜과 밝은 입자 사이의 대비가 강하다.

- 팔레트: 황백색 최고광 → 노랑 → 주황 → 빨강 번짐 → 검붉은 외곽. 전부 같은 주황으로 채우면 중심의 열감이 사라진다.
- 실루엣: 촘촘하고 가느다란 방사형 불꽃, 가로로 퍼진 불규칙한 폭발 덩어리. 다만 좁은 크롭만으로 전체 3D 폭발이 평평한 원반이라고 단정하지 않는다.
- 시간 근거 C: 능력 설명은 충돌 후 바운스하고 곧 폭발하며 주변 대상을 scorch한다고 서술한다. 이 이미지는 밝은 폭발 구간만 보여준다.
- lowpoly 관찰 전환안: 밝은 중심과 크기가 다른 소수의 뾰족한 불꽃 조각, 낮은 밝기의 적색 외곽으로 계층을 보존한다. 조각 수·수명은 아직 미정이다.
- 한계: 후속 연소의 길이·연기량·피격 대상의 상태 변화는 이 한 장에서 확인되지 않는다. 투척 전 외피의 리브·캡슐 구조를 증명하는 이미지도 아니다.

### 2.4 Void — Vortex Grenade [A]

- [능력 페이지](https://www.destinypedia.com/Vortex_Grenade) · [파일 이력·권리 안내](https://www.destinypedia.com/File:Vortex_Grenade.jpg)
- [직접 게임 스크린샷](https://destiny.wiki.gallery/images/f/ff/Vortex_Grenade.jpg)
- 로컬: `/tmp/destiny-h13-vfx-refs/wiki-vortex.jpg` (1015×295).
- 귀속: Bungie / Destiny 게임 이미지. Destinypedia 파일 게시자 WizardWolf. 개별 VFX 작가 미확인.

**보이는 특징:** 중앙에는 흰색에 가까운 분홍보라 광점이 크고 강하게 보인다.
그 주위를 짙은 청보라 바탕과 밝은 보라색의 여러 휘어진 띠가 둘러싼다.
외곽 띠는 화면에서 타원처럼 보이고, 짧은 밝은 파편·선들이 내부에 분산되어 있다.
검은 코어가 확실히 보이는 장면은 아니다. 설명의 ‘black hole’을 검정 구체라는 외형 사실로 치환하지 않는다.

- 팔레트: 분홍빛 백색 중심 → 연보라/라일락 → 선명한 보라 띠 → 짙은 청보라 공간.
- 실루엣: **밝은 중심 + 큰 곡선 경계 + 어두운 내부 여백**. 균일한 보라 연막이나 주황 폭발의 색상 교체만으로는 특징을 살리기 어렵다.
- 시간 근거 C: 능력 설명에는 충돌 시 발생하고 중심으로 끌어당기며 지속 피해를 준다고 적혀 있다. 정지 이미지로 회전 방향·회전 속도·수축·펄스 주기는 확인할 수 없다.
- lowpoly 관찰 전환안: 각진 호나 분절된 띠로 중심과 외곽의 구분을 남긴다. 분절 개수·회전 애니메이션·지속시간은 구현 전 검증 항목이다.
- 한계: 원근·크롭 때문에 완전한 구체/원반의 3D 형태를 확정하지 않는다. Warlock Chaos Accelerant의 확장 크기·지속시간을 Hunter의 기본값으로 전용하지 않는다.

## 3. 요청 능력별로 사용할 수 있는 근거

팔레트 명칭은 위 이미지의 육안 해석이다. Bungie의 공식 색상표·선형광 값·정확한 HEX 샘플이 아니다.

| 능력 | 팔레트·실루엣 방향 | 시간 순서와 근거 | 확실하지 않은 부분 |
|---|---|---|---|
| Arc Flashbang | 청백색 순간 광량을 중심으로, 가는 청색 전격과 드문 길쭉한 입자. B 카드 참고 | 바운스 → 곧 폭발: C 설명. 짧은 최고광 → 잔광은 연출 제안 | 실제 게임플레이 폭발 프레임, 정량 밝기·시간 미확인 |
| Arc Combination Blow | Hunter 표지의 가는 불규칙 전격과 어두운 인체 대비만 차용. 주먹/접촉점 중심의 짧은 강조는 제안 | [Arcstrider](https://www.destinypedia.com/Arcstrider)의 ‘quick strike’: C. 접촉 순간 강조 → 빠른 감쇠는 제안 | 실제 타격 프레임 없음. Arc Staff/Tempest Strike/추가 jolt 효과를 기본 주먹과 동일시하지 않음 |
| Solar Incendiary | A의 황백색 중심·주황 불꽃·적색 번짐과 방사형 가는 조각 | 바운스 → 폭발 → scorch: C 설명. A는 폭발의 한 순간 | 지연시간·후속 연소 지속·불꽃 궤적 길이 미측정 |
| Solar knife | H12 실물 칼 실루엣을 식별 가능하게 유지. 작은 온색 잔광은 잠정 제안 | [Gunslinger](https://www.destinypedia.com/Gunslinger) 설명에서 변형별 트리거를 구분: C | 특정 knife 변형의 VFX 프레임 없음. 소이 폭발이나 Warlock의 거대 광검을 일반 단검에 적용할 근거 없음 |
| Void Vortex | A의 밝은 라일락 중심·짙은 청보라 여백·외곽 곡선 띠 | 충돌 → 중심 흡인·지속 피해: C 설명. 회전은 이미지에서 미검증 | 정확한 볼륨·방향·주기·지속시간 미측정 |
| Void smoke bomb | 짙은 보라/회보라 연무를 덩어리로 구분하는 안은 **잠정 제안**. Vortex의 흰 중심·호를 그대로 재사용할 근거 없음 | [Nightstalker](https://www.destinypedia.com/Nightstalker)의 Snare Bomb: 부착/배치 → 폭발·연막: C. 버전별 세부는 분리 필요 | 실제 Hunter 연막 프레임 없음. 색·밀도·퍼짐·은신 전환 시간 모두 미검증 |

Solar knife는 하나의 고정된 효과라고 취급하지 않는다. 위 Gunslinger의 Solar 3.0 설명에는
Knife Trick의 부채꼴 투척·scorch, Lightweight Knife의 빠른 단일 투척,
Weighted Throwing Knife의 조건부 ignite, Proximity Explosive Knife의 부착 후 근접 폭발이 구분되어 있다.
이는 **동작 설명만 확인한 결과**다. 일반 칼 투척마다 큰 폭발을 추가하는 근거가 되지 않는다.
연막도 과거 Vanish in Smoke와 현재 페이지의 Snare Bomb 설명을 한 버전의 동일한 연출로 합치지 않는다.

## 4. ArtStation 추가 조회 결과

새 후속 지시에 따라 공개 검색 API를 재조회했다. 각 검색은 HTTP 200이었으며 다음 제목·게시자를 확인했다.

| 작품 / 게시자 | 직접 확인한 이미지 | 용도와 제한 |
|---|---|---|
| [Hunter Abilities VFX — Dave Samuel](https://www.artstation.com/artwork/31lkyE) | 위 2.1의 청색 Hunter 표지 | Arc 계열 색·선·인체 대비. 연속 타격 직접 증거 아님 |
| [Titan Abilities VFX — Dave Samuel](https://www.artstation.com/artwork/41o2mq) | [보라색 Titan 표지](https://cdna.artstation.com/p/assets/covers/images/100/289/690/smaller_square/dave-samuel-dave-samuel-artstation-titan-thumbnail.webp?1782417523) | 들어 올린 팔 위의 밝은 원형 광륜, 보라색 몸 윤곽과 작은 입자를 육안 확인. Hunter 연막·Vortex 자체의 증거 아님 |
| [Warlock Abilities VFX — Dave Samuel](https://www.artstation.com/artwork/JwaW4a) | [태양색 Warlock 표지](https://cdna.artstation.com/p/assets/covers/images/100/289/238/smaller_square/dave-samuel-dave-samuel-artstation-warlock-thumbnail.webp?1782416722) | 머리 위 긴 검, 좌우로 펼쳐진 밝은 날개 모양, 황백색/주황 광륜과 잔불 확인. Hunter 칼 투척 증거 아님 |

추가 로컬 이미지: `as-titan-cover.webp`, `as-warlock-cover.webp` — 모두 `/tmp/destiny-h13-vfx-refs/` 안에 있다.
작품 제목과 게시자만으로 해당 작가의 모든 효과 제작 분담이나 Bungie의 공식 업로드 여부를 단정하지 않는다.

확인한 공개 검색 주소:

- [Hunter 검색 JSON](https://www.artstation.com/api/v2/search/projects.json?query=Hunter%20Abilities%20VFX&page=1&per_page=30)
- [Titan 검색 JSON](https://www.artstation.com/api/v2/search/projects.json?query=Titan%20Abilities%20VFX&page=1&per_page=30)
- [Warlock 검색 JSON](https://www.artstation.com/api/v2/search/projects.json?query=Warlock%20Abilities%20VFX&page=1&per_page=30)

`https://www.artstation.com/artwork/31lkyE.json` 상세 조회는 **HTTP 403**이었다.
이후 `www.artstation.com` 조회를 중단했다. 다른 상세 경로·프록시·인증 우회는 시도하지 않았다.
표지는 공개 검색 응답에 실제 제공된 `cdna.artstation.com` URL의 작은 미리보기만 저장했다.
상세 페이지의 비디오·설명·타임라인은 확인하지 못했다. H12 문서의 미확인 이력은 보존하며,
이번 문서가 추가 검증한 범위는 이 **표지 3장**까지다.

## 5. Sketchfab 조회와 배제 결과

[공식 검색 API: Destiny grenade](https://api.sketchfab.com/v3/search?type=models&q=Destiny%20grenade&count=10)에서 3개 결과를 확인했다.
메타데이터만 조회했고 모델·텍스처·뷰어 에셋은 다운로드하지 않았다.

| 결과 | 게시자 | 판단 |
|---|---|---|
| [Witherhoard ornament Destiny 2](https://sketchfab.com/3d-models/4625bca86abc494fa8bba46c74dac99b) | myrthevdmeulen | Destiny 관련 사용자 게시 모델. 요청한 Hunter 능력 VFX가 아니므로 제외 |
| [The Demolitions Expert - Exotic Auto Rifle](https://sketchfab.com/3d-models/90cb6750f0044bb7b4f4ff6fd2ae143a) | Andrew Sliwowski | 원작 출시 에셋인지 확인되지 않은 사용자 게시 무기. Hunter VFX 근거에서 제외 |
| [ORBIT Magnetic grenade](https://sketchfab.com/3d-models/d382304852a04339aed6aa325fafd195) | kawuru | 일반 SF 소품. 실제 Destiny 자료가 아니므로 제외 |

세 결과의 API 라이선스 필드는 비어 있었다. 팬·사용자 제작 또는 원작 미확인 자료를 실제 Destiny로 표시하지 않는다.
이번 lowpoly 방향의 우선 근거는 Sketchfab의 일반 SF 형상이 아니라 2절의 실제 Destiny 이미지다.

## 6. 인계와 남은 검증

우선 적용을 검토할 시각적 구분은 **Arc의 청백색 섬광과 가는 전격, Solar의 황백색 중심과 방사형 불꽃,
Void Vortex의 밝은 중심과 짙은 공간·곡선 경계**다. 형상을 단순화하더라도 중심/외곽 밝기 차이와 빈 공간을 남기는 것이 관찰된 특징에 가깝다.
모든 속성을 같은 구체·고리의 색상만 바꿔 표현하는 근거는 이번 자료에 없다.
이는 디자인 방향이며 구현·파티클 수·모델 예산·서버 성능 검증 결과가 아니다.

추가 확정이 필요한 것은 Flashbang 실제 폭발, Combination Blow 접촉 순간, 선택한 Solar knife 변형의 비행/피격,
Hunter 연막의 발생/확산/소멸 영상이다. 이 네 가지는 이번 조사에서 확보했다고 주장하지 않는다.
특히 영상 전후 프레임이 없으므로 정량 타이밍은 후속 확인 대상으로 남긴다.
유용한 속성별 실제 자료가 확보되어 추가 검색은 여기서 종료했다.

증거 묶음: `/tmp/destiny-h13-vfx-refs/`.

- `evidence-manifest.json`: 이미지 6장의 직접 URL·게시자·증거 등급·SHA-256·접근 결과·미확인 항목.
- `wiki-incendiary.jpg`, `wiki-vortex.jpg`, `wiki-flashbang-grimoire.jpg`, `as-*-cover.webp`: 육안 확인한 6장.
- `as-*_Abilities_VFX.json`, `sketchfab-search.json`: 검색 응답 원문.
- 위키 능력/파일/직업 페이지의 `.html` 및 추출 `.txt`: 설명·권리·파일 이력 확인 근거.

기존 `/tmp/wiki-grenade-0.jpg`는 소이, `-1.jpg`는 소용돌이 원본 URL에서 재확보한 파일과 바이트 단위로 일치했다.
Bungie Arc 3.0 기사 후보는 JavaScript 앱 껍데기만 응답하여 본문·영상 근거에서 제외했다.
위키 파일 검색에서도 Combination Blow와 Hunter smoke의 직접 프레임은 확보되지 않았다.

게임 이미지의 권리 귀속과 위키의 fair-use 안내는 에셋 재배포 라이선스가 아니다.
미리보기는 `/tmp` 연구 증거로만 보관했고 저장소·리소스팩에 넣지 않았다.
Bungie 원본 메시·텍스처·셰이더를 추출하거나 내려받지 않았다.
저장소에는 이 새 문서만 추가하며 H12 문서, 코드, BetterModel, Blockbench, 모델·텍스처를 변경하지 않는다.
