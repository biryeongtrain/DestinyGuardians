# W129 — Halfdan-D · Austringer · Antiope-D

에이스87/이자나기79 연구와 minecraft-weapon-art-design을 적용한 독립 CoW 작업 3정. 리핑 섬/voxel을 이식하지 않고 의미 있는 큰 opaque 입체 + 면별1024² UV로 재설계했다.

|무기|조립체 출력|유지한 정체성|
|---|---:|---|
|Halfdan-D|114|ivory/silver HAKKE upper, orange stripe, brown lower/grip, 열린 sight/guard와 깊은 bore|
|Austringer|126|금빛 shroud, 검정 frame/cylinder/wrapped grip, 보라 inset2개, 아래 optic와 실제 recess/underlug gap|
|Antiope-D|118|ivory HAKKE body, 검정·주황·갈색 소재 대비, 연속 panel, 실제 recessed bore와 열린 peep|

모두 full-only이며 기존 generic reload/ADS/scale/display/손 접점/전투·음향 불변. 의미 있는 깊이는 입체, 얕은 나사/패널/무늬는 UV. 원작 default photo와 raw detail을 함께 사용하며 neutral diffuse를 기본 안료로 오해하지 않았다. 원작 PBR/동적 shader 복원은 아니다. 한 조립체1000이하, 요소수를 채우기 위한 증식 없음.

실제 Blockbench private 사선3정 및 Antiope front bore를 확인했다. 기존 active 프로젝트/미저장 탭 보존, private view 폐기 후 목록 확인. worker tests9/8/12, master JUnit9, 실제 Polymer ZIP25models/12textures/98fallbacks 확인. Mac 잠금으로 client는 미기동: 다운로드/native parser/1·3인칭/ADS·reload/20표시/청취 통과로 세지 않는다. 서버0player 종료0/포트정리 완료.

[QA](../qa/2026-10-26/w129/README.md) · [검증](../qa/2026-10-26/w129/validation.json)

[Halfdan 비교](../../art/weapons/w123/halfdan_d/comparison.png) · [Austringer 비교](../../art/weapons/w123/austringer/comparison.png) · [Antiope 비교](../../art/weapons/w123/antiope_d/comparison.png)

누적12/63 semantic통합,3 native대표검토/9대기/51리모델링잔여. 재귀spawn은 worker도구 미제공으로 불가하여 master직접3명 병렬로 수행했다. 전체goal은active이며 다음 scout/fusion/rocket의 서로 다른3정으로 확대한다.
