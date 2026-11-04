# W69 — Ammit AR2 재장전 출처와 작성 범위

## 정체성과 원본

- 공식 아이템 hash **2119346509**: <https://www.bungie.net/en/Explore/Detail/DestinyInventoryItemDefinition/2119346509>.
- 사용자가 제공한 Drive의 정적 모델: <https://drive.google.com/file/d/10O1xjObGAvW5x6uESPax0G-U1qA7Vh7f/view>.
- [원본 검사](references/original-model-audit.md): BLEND/FBX SHA를 W30과 재대조했다. 각13mesh/20,250triangle, Reticle25triangle 제외한 W30은20,225. Armature/bone/action/NLA 0. 남은 Armature modifier는 null target이며, vertex group 이름만으로 실제 rig가 존재한다고 간주하지 않는다.
- `Magazine`는 분리된 정적180vertex/164triangle mesh. `Fluid`의 frame driver는 texture coordinate용이며 재장전/손 애니메이션이 아니다. **원본 애니메이션을 가져와 적용한 작업이 아니다.**

## 실제로 확인한 영상

[xHOUNDISHx, This is BETTER Than Most Exotic Autos and Its FREE](https://www.youtube.com/watch?v=w3CYQprLoc0), 2022-09-01, 312초.
최초65초를1280×720/60fps로 받아 확인했다. 인벤토리28–34/64초에서 Ammit AR2 정체성을 확인했다.
[선택 프레임](references/ammit-reload-contact.jpg) · [다운로드/프레임 SHA와 관찰](references/gameplay-provenance.json).

빈 탄창23.8–25.6초 및 부분 장전49.4–50.5초를 살폈다. 총을 들어 기울여 측면을 드러내고, 왼손이 둥근 창 아래쪽 탄창 근처를 잡았다가 다시 밀어 넣는 동작이 보인다. **원형 액체 창은 몸체에 붙어 있다.**
다만 빠른 손/화면 하단 가림 때문에 탄창의 전체 이동 궤적은 확정하지 못했다. 따라서 로컬 아래/약간 좌측으로 빼고 다시 끼우는 경로와 회전·위치·정규화 비율은 **작성한 근사치**다. 불확실한 부분을 원작에서 추출한 정확한 경로로 표현하지 않는다. 액체 탱크 전체 분리나 실린더 교환을 추정하지 않는다.

영상은 Ambitious Assassin의 **110발** 상태이고 shader도 현재 기본색과 다르다. 이 영상의 보충 시점(빈25.000→25.150, 부분50.200→50.350초)은 관찰 bracket일 뿐이다. 기본 탄창 수/기본 재장전 시간/새 early-credit 비율/현재 원작 규칙으로 이식하지 않는다. 기존 서버의 실제 reload phase에만 시각 단계를 매핑한다.

## 적용 경계

기존199큐브·UV·기본색 texture를 보존하고 몸체/하부 탄창을 나눈다. 21단계, 양쪽1인칭 context와 native/twohand 보상. 일반3인칭/GUI/드롭/비활성 graph는 기존 그대로다.
기존 W63 자동소총 소리는 **무기군 대표**이며 이 영상/Ammit 고유음 추출이 아니다. 새 audio/시간/탄약/보충 정책을 도입하지 않는다.
손·IK·유체 shader·charging handle·3인칭 reload·연속적인 mesh interpolation은 없다. Blockbench 검사와 headless 테스트는 실제 Minecraft framebuffer/사용자 입력/실청취를 대체하지 않는다.

## 실제 큐브 분할 감사

[원본 Magazine 정점/삼각형의 좌표 증거](references/magazine-mesh-audit.json) · [표면 비교/분할](references/magazine-partition-audit.json) · [투영 도해](references/magazine-partition-audit.png).
원본 Magazine와 다른 모든 mesh의 실제 표면거리를 각cube의6면16×16sample/면적가중으로 비교했다. 단순 bounding box 포함 여부만으로 선택하지 않았다.
15개 index `52,54,56,64,65,73,75,134,137,139,142,171,172,174,180`를 사용한다. 초기25개 후보 중10개를 고정 몸체로 남기고, 몸체와 교차하는10/11도 고정했다.
선택7개 cube는 다른 mesh 표면 기여가 약4.2–24% 남아 있다. 따라서 whole-cube 분할은 기존 재구성의 경계를 보존하는 근사이지 원본 mesh의 정확한 분리와 같지 않다.
저장한 검사 bbmodel은 편집 가능한 정적184body/15cartridge 그룹이며 재생 가능한 원작 animation clip이 아니다. 생성 입력은 반올림된 검사 bbmodel이 아니라 기존 정확한 runtimeJSON이다.
