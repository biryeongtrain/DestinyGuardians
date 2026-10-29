# W245 — 타워 원본 머테리얼 베이크

사용자 SSD의 `Destiny-Tower-Materials-2026-10-29`를 기존 Courtyard에 연결했다. 별도 Blender 장면에서 원본 형태에 베이크를 미리 보고, 그 색을 기존 Minecraft 노출면의 바닐라 블록으로 옮겼다. 지형·동선·중앙 나무·기존 소품은 유지한다. 클라이언트 리소스팩에 새 대형 텍스처나 모델은 추가하지 않았다.

## 결과

- 원본: 머테리얼 753개, DDS 806개, HLSL 404개. DDS 자체는 이전 전달본과 동일했고 shader tint/layer 합성이 누락돼 있었다.
- 합성 지원: 24개 shader, 98개 머테리얼. 노출면 122,103셀 중 103,577셀을 대표 basecolor로 베이크했다.
- 최종 변경 후보: 96,577셀 / 116청크. 서버 데이터 gzip은 271,510바이트다.
- 격리 QA 적용: 96,550변경 / 27보호 skip. 현재 블록이 예상 상태와 다른 좌표는 보존했다.
- 붉은색·황토색 천막과 어두운 구조체·바닥, 밝은 보행선의 구분을 확인했다. 원본 지형과 이전 W243 소품은 변경하지 않았다.

[Blender 전후 비교](blender-material-comparison.jpg) · [Danmo 실게임 전후 비교](danmo-material-comparison.jpg) · [단계별 기록](step-log.md)

## 검증

main의 `compileJava`와 `compileGametestJava`가 통과했다. 최종 데이터의 실제 제품 decoder로 SHA·중복·expected·노출면/full cube 계약을 검사했고, ledger codec 왕복 후 재시작 상태와 사용자 편집·소품 보호 fixture가 통과했다. 전체 과거 GameTest의 성공을 주장하지 않는다. [실행 로그](runtime-targeted.txt)

Danmo 4GB QA에서 최종 적용 완료 후 광장 도착점·시장·정원·전망·서비스 통로의 PNG를 직접 검수했다. runtime worker도 같은 5구도를 확인했다. 새로운 구멍·누락 텍스처·나무 손상은 보이지 않았다. 시장 바닥의 검은 무늬는 적용 전에도 있었다. 서비스 통로의 색 패치는 다소 거칠게 보이는 한계가 있다.

실제 client native forward 20틱과 neutral 5틱으로 4.3139블록을 걸었고 서버 Pos와 일치했다. health 20, lease 해제와 native 입력 중립을 확인했다. 촬영용 teleport는 fixture이며 native 보행 근거와 구분한다. OS 키보드 조작·원작 영상의 픽셀 일치·장기 성능 검증은 아니다. [보행 상태](w245-walk-state.json)

## UV 계약과 한계

Charm `StaticPart.TransformUVs`가 STATIC export에 scale/translation과 V flip을 이미 적용한다. 따라서 shader PS UV는 `(exported U,1-exported V)`이며 scale/offset을 다시 적용하지 않는다. 현재 crop에는 terrain이 없고 미검증 terrain 입력은 거부한다.

TEXCOORD8 vertex buffer·원본 조명·반사·일부 Frame/TFX 입력은 확보되지 않았다. 대표값으로 정적 basecolor를 합성했으며 원작 렌더 완전 복원은 아니다. 배경 합성이 필요한 projected decal은 블록 치환에서 제외했다. Minecraft에서는 텍스처 픽셀을 직접 붙이는 대신 바닐라 블록 색으로 양자화한다.

24개 shader의 독립 HLSL 식 대조 최대 linear 오차는 2.98e-8이다. sampler를 공유하므로 GPU/DXBC 렌더 검증은 아니다. 자세한 계약은 [shader worker 보고](shader-worker.md), [recipe](shader-recipes.json), [최종 베이크 수치](bake-audit.json), [runtime worker 보고](runtime-worker.md)를 참조한다.

## 재현

저장소 루트에서 NumPy/Pillow가 있는 Python으로 실행한다. 원본 SSD 자료는 읽기 전용이며 중간 GLB·DDS·preview PNG는 저장소 밖에 둔다.

```sh
rtk proxy python3 scripts/tower/map_material_uv_w245.py --output /private/tmp/tower-w245/geometry
rtk proxy python3 scripts/tower/bake_courtyard_w245.py --cache /private/tmp/tower-w245/geometry/geometry-uv.npz --out /private/tmp/tower-w245/bake
rtk proxy python3 scripts/tower/prepare_material_preview_w245.py --source /private/tmp/tower-w245/geometry/source-crop.glb --output /private/tmp/tower-w245/preview
```

원본 자료 경로를 바꾸려면 mapper의 `--source`, baker/preview의 `--materials`를 지정한다. W245는 별도 ledger와 expected 검사를 사용한다. 기존 월드의 ledger를 지워 재적용하지 않는다. 미술 조정의 반복 검수는 적용 전 스냅샷을 복제한 전용 QA 월드에서 수행한다.

## 운영 반영과 정리

운영 타워를 적용 전 CoW 스냅샷으로 보존한 뒤 96,550변경/27보호 skip으로 갱신했다. `save-all flush`·정상 종료 후 새 JVM에서 같은 저장 월드를 열었고 W245는 **0변경/0건너뜀**으로 완료했다. 리소스팩 생성도 성공했다. 서버는 `192.168.35.237:25565`, online-mode=true, andlist OP4로 열어 두었다. 무인 일시정지 설정은 원래 60초로 복원했다. [배포 상태](deployment.json) · [선별 로그](deployment-log.txt)

QA 서버와 Danmo client를 종료하고 8102/25611 포트가 닫힌 것을 확인했다. 이번 bounded awake만 종료했고 사용자 요청의 48시간 caffeinate PID79904는 유지했다. 고정 worktree slot1/4는 삭제하지 않고 반환했다. 기존 다른 작업의 미커밋 변경은 보존한다.
