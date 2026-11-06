# W327 소총 출력 최적화

동일 semantic part·재질·평면의 authored 삼각면을 polygon-union alpha 평면으로 병합했다. 세부 윤곽을 채우는 직사각 슬래브를 만들지 않았다. 실제 삼각 꼭짓점과 solid cuboid, material projection, 좌표계, 탄창 분리 이름을 보존한다. 가려진 원본 면이나 비평면 실루엣을 임의로 삭제하지 않는다.

|무기|기존|변경|본체|탄창|
|---|---:|---:|---:|---:|
|krait|985|412|408|4|
|rufuss_fury|968|424|412|12|
|origin_story|500|238|223|15|
|age_old_bond|729|269|251|18|
|insidious|378|219|189|30|
|phyllotactic_spiral|608|390|383|7|

합계 4,168 → 1,952개 (53.2% 감소). 원본 authored triangle vertices 비교 일치; maximum plane projection error < 2e-15 model units. Native standard from/to/rotation/faces만 사용, 모든 UV 0–16, body/magazine 분리 및 무기당 ≤1,000 확인. generator 2개 py_compile 통과.

대표 Krait: 동일 카메라·조명 Cycles 사선 렌더 전후 각 1회. 장식·재질 대비·윤곽 유지, 기존 triangle seam 틈 감소를 관찰했다. `optimization_comparison.png`는 offline 비교이며 Minecraft PNG가 아니다.

실제 게임 팩 로드, 1/3인칭·ADS·장전, 10–20개 표시 끊김/FPS, 최종 배포 ZIP 크기는 master 통합 QA 대상이며 이 worker는 실행하지 않았다. 출력 요소 감소를 실측 FPS 개선으로 주장하지 않는다.

기존 원본 source/reference·HUD 아이콘·손 좌표·장전 동작·공유 kit는 수정하지 않았다. 추가 의미 없는 큐브 분할은 하지 않았다. 원본 형태를 바꾸는 재디자인 대신 기존 입체를 효율적으로 내보내는 변경이다.
