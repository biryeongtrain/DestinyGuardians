# 요구사항과 우선순위

## 필수 반환
1. 실제 추출 raw clip/skeleton/runtime-rig와 각 SHA256·바이트 크기.
2. game buildID·Steam depot/manifestID(확인 가능한 경우), 실제 사용 package 파일명·SHA256, base/patch 의존 목록, tool revision·명령·로그.
3. clip별 status와 perspective(1P/3P/unknown), 분류 근거. 원본과 변환본의 구분.
4. 실패해도 추출된 파일과 미확보 목록을 남긴다. 보고값으로 빈 bin을 만들거나 수동 재현 모션을 원본으로 제출하지 않는다.

Charm 직접 FBX가 먼저 성공하고 raw 일부가 미확보라면 FBX·재생 증거를 partial 상태로 우선 반환한다. raw3종은 완전한 재현 세트를 위한 목표이며 유효한 직접 export를 보류시키는 조건으로 삼지 않는다. retarget glTF는 별도 parser 경로의 결과로, Charm FBX 성공에 필수는 아니다.

## 우선순위
- P0: 일반 HC 80A8A567 후보 한 세트로 pipeline 성립 확인.
- P1: Ace·Izanagi 고유 장전 탐색 + AR/SMG/pulse/scout/sidearm/sniper/shotgun/fusion/LFR/MG/rocket/GL 등 무기군 대표 reload.
- P2: empty/tactical·per-shell·special reload 변형, 필요한 equip/recoil/draw. 검·활·월도의 실제 사용 동작을 일반 reload로 강제 분류하지 않는다.

## 환경
Windows x64, 기존 Destiny 2 packages 우선. Git, Python3.13+, Blender(glTF 검증용). Charm은 .NET8 Desktop Runtime x64와 VC++ runtime이 README 요구사항. tiger-pkg를 빌드할 때 Rust/MSVC 환경 및 게임에서 확보한 대응 Oodle DLL이 필요할 수 있다. 도구 README·실제 오류를 먼저 확인하고 무조건 모든 SDK를 설치하지 않는다.
필요 디스크는 현재 설치·선택 package·캐시를 실제 측정한다. Bungie의 최대180.90GB 전체 설치 안내를 최소 선택 다운로드 용량으로 오해하지 않는다. 기존 설치+preload353GB도 이번 PoC의 고정 요구량이 아니다.

## 제외
Minecraft 설치/테스트, 무기 리모델링, 전체 게임 재배포, 실행중인 게임 메모리/anti-cheat 조작. 목적은 디스크상의 가용 패키지에서 애니메이션 파일을 추출하는 것이다.
