# Drive 원본 재질 검토 — 2026-11-03

사용자 지정 원본:
- [House of Dusk](https://drive.google.com/drive/folders/1cSe27uEuAvI0SUfJipNAs886xHFGEYzM)
- [Hive 상위 폴더](https://drive.google.com/drive/folders/1MY3GRfOeW-gJKw8nEp6GS7Q2HAAbqMoP)
- [Normal Hive](https://drive.google.com/drive/folders/1pglBkCuc6dAzwJr90iVmo4Qufh0yvM6M). 사용자 지시대로 빨간 군체를 제외한다.

로컬 원본: `/Users/qf/Downloads/Devils-Lair-Dusk-Drive-2026-11-03`.
워커, 대장, 드렉, 반달, 서비터, 세픽스, ShockRifle 샹크와 Normal Hive 시종/노예/기사/마법사 11종 RAR를 내려받아 해제했다. `source-manifest.json`은 압축본과 blend/FBX/PNG 334파일의 SHA-256이다. 원본 모델은 저장하거나 수정하지 않았다.

워커 Blender 검토: headless `--factory-startup --disable-autoexec`, 73 mesh, 34693 vertices, 10 materials. Bungie Overlay Blend Mode, 4-Way Switch, Normalizer 그룹과 장갑/파손/내부/데칼/발광 재질을 확인했다. 텍스처 경로를 메모리에서만 복구한 원본 셰이더 렌더가 `walker-source.png`이다. 머신건 IK dependency cycle 경고는 원본에서 발생하므로 동작 검토가 필요하다. Blender 5.4의 이미지 출력 media_type을 IMAGE로 설정했다.

이는 원본 재질 확인용 렌더이며 Minecraft 베이크나 실제 인게임 수락이 아니다. 기존 수동 recolour 후보는 통합하지 않는다. 원본 셰이더를 평가한 색상/질감과 발광을 게임용 atlas로 옮기고, 비교 이미지 및 실제 클라이언트 검토를 진행한다. 이 폴더에서 Brig 원본은 확인하지 못했다.

## 추가 Walker / Brig 후보

추가 Walker의 `WalkerButBetter.blend`는 44본, Action 0개다. 기존 모션은 해시 이름의 50본이며 이름 일치 0개. 동봉 FBX를 빈 scene에 import한 결과 아마추어 0개. 직접 교체 호환은 불가하며 리타게팅/재질 전송은 미검증이다. 상세 해시는 alternative-walker-rig-comparison.json에 있다.

구원의 가문 Brig와 폭동 프라임 압축 원본도 확보·해제했다. 구원의 가문 Brig에는 18재질, 제어 리그와 파손/눈/VFX 재질이 있으며 Action은 0개다. 베이크·흉부 개방 동작 검토는 아직 미완료다.
