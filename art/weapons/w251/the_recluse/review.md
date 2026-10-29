# W251 은둔자 미술 보강

실제 출력 143 큐브: 본체 129, 탄창 14. full은 같은 조립체이며 중복 합산하지 않는다. 면 858개 모두 명시적 UV, 1024² atlas 유지.

기본 안료 사진과 복구 원본 FBX 20,369면·원본 stock/barrel 자료를 검토했다. 긴 receiver와 optic hood를 넓은 면을 가진 팔각 단면으로 바꾸고, stock의 세로 판·어깨를 둥글고 기울어진 부품으로 바꿨다. 두 grip의 단면·총열 단면도 실제 회전 큐브다. sight, 방아쇠 울, 포구 빈 공간을 보존한다. 기존 bird 마스크를 세계 좌표로 연속 전사하고, receiver 채널·빨간 charge 창·고무 liner·총구 천공은 면 UV로 정리했다. 무작위 얼룩이나 조명 보상 필터를 사용하지 않았다.

비교 그림은 마스터의 변경 전 snapshot과 W251을 동일 카메라·광원·배율로 렌더한다. axis/angle과 XYZ를 RzRyRx로 정규화했다. CPU 그림은 native 수락 증거가 아니다. 작은 원본 FBX 그림의 색은 W31 안료 lookup으로, 원본 셰이더 복원은 아니다.

검사: JSON parse, 실제 요소 수/UV 범위/texture 참조, full과 분리 조립체 일치, exact display, 원본 archive/FBX 해시, 재생성 --verify.

실행: `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/refine_weapon_w251_the_recluse.py` 및 같은 명령의 `--verify`. 원본 생성기는 읽기 전용 import하며 매번 semantic 설계부터 시작한다.

남은 master native QA: 공통 shader 수정 후 주간/실내의 1·3인칭, ADS sight 통공과 손 접촉, 탄창 분리·복귀, 10~20개 표시에서 틈·깜박임·끊김 확인. stock의 bird 경계는 이전 W31 마스크 해상도에 제한되며 미세 곡률은 팔각으로 단순화했다.
