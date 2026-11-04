# Mac 통합에 필요한 데이터

제품은 Minecraft26.3 Fabric/Polymer 서버사이드 + 바닐라 클라이언트/리소스팩이다. 원본 glTF를 곧바로 Minecraft가 재생할 수는 없다. 현재 정돈한 큐브/삼각 무기 외형을 유지하고 원본 motion을 의미 있는 group에 bake/retarget할 계획이다. 조립 무기당 출력 큐브+삼각 요소 합계1000개 이내라는 기존 미술 규칙을 유지한다. Windows 추출 담당은 고밀도 mesh로 제품을 교체하지 않는다.

`context/WeaponReloadPresentation.java`는 인계 시점의 참고 사본이다. 원본 repo 전체가 아니며 이 파일만 수정해서 Mac 제품에 적용하려 하지 않는다. 현재 서버 장전 진행률을21개 샘플로 표현하는 경로가 있다. 실제 탄약 지급·소유권·취소는 서버 권한이며 animation event로 옮기지 않는다. Izanagi/shell insert는 별도 경로가 있다.

반환할 좌표 정보: source up/forward/handedness, 단위, root/rest matrix, bone parent/name/hash, transform local/world 여부, rotation quaternion xyzw/wxyz, 무기/탄창/실린더·양손 attachment와 pivot. 알 수 없으면 null+근거를 남긴다. 임의로 zero/default를 정답처럼 채우지 않는다.

retarget본은 source rig와 별개로 저장한다.1P 원본 팔 clip과3P player body clip을 혼용하지 않는다.3P BetterModel 통합은 별도 player-bone retarget가 필요하다. fp로 확정되지 않은 clip도 source 자료로 받을 수 있지만 unknown 표시를 유지한다.

원본30fps 시간축/clip 길이와 DDC의 gameplay reload 완료·취소 시간은 별개다. mag-out/in, bolt, cylinder-close, ready 등 event는 관찰 시점(frame/seconds)+confidence를 기록하고, 발췌 영상으로만 확인한 것을 게임 논리 event로 확정하지 않는다. 추출 시 retime하지 않고 원본 키를 보존한다.

DDC 사용자 기준 링크는 context/DDC_POLICY.md에 있다. source catalog의 수치가 모두 최신 DDC로 소급 검증됐다는 뜻은 아니다. 단순 스탯 수치는 출처와 적용 경로 확인만 하고 별도 반복 테스트를 추가하지 않는 최신 사용자 방침을 적용한다.
