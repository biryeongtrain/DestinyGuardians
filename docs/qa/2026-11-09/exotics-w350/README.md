# W350 경이 9종 — 구현 및 검수 기록

장착 슬롯 기준 기본·에너지·파워 각 3종을 추가한다. 시공·초월과 촉매 효과는 이번 범위에 포함하지 않는다.

| 슬롯 | 무기 | 원작 inventory hash |
|---|---|---|
| 기본 | 진홍 핏자국 / Crimson | 3437746471 |
| 기본 | 가시 / Thorn | 3973202132 |
| 기본 | 완벽한 폭동 / Outbreak Perfected | 3824673936 |
| 에너지 | 태양탄 / Sunshot | 2907129557 |
| 에너지 | 중력자의 창 / Graviton Lance | 3628991658 |
| 에너지 | 요툰 / Jötunn | 417164956 |
| 파워 | 걀라르호른 / Gjallarhorn | 1363886209 |
| 파워 | 벌레의 속삭임 / Whisper of the Worm | 1891561814 |
| 파워 | 트랙터 대포 / Tractor Cannon | 3580904581 |

## 출처와 환산

- 사용자가 제공한 [모델 Drive](https://drive.google.com/drive/folders/1_q5j5BCminJGp52bXmf9Y8RYJgQRlGYr), [사운드 Drive](https://drive.google.com/drive/folders/1ytF85L4RhUtECU78hnB0a1kXmlNenJdJ)를 사용했다. 원본과 각 파일 SHA는 무기별 source-evaluation 및 audio manifest에 보존한다.
- Bungie manifest `245114.26.10.13.2000-1-bnet.66137`의 원본 비제작·비촉매 아이템을 선택했다. `art/weapons/w350/catalog-source.json`과 빌더의 오프라인 검증 경로를 사용한다. 태양탄은 2907129557이며, 2907129556은 질풍이므로 사용하지 않는다.
- 우선 수치 출처는 [Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4)의 Exotic Weapons 탭 gid441434520이다. 확인한 행은 Crimson16, Outbreak39, Thorn50, Graviton83, Jötunn90, Sunshot104, Gjallarhorn130, Tractor148, Whisper152이며 캡처는 `art/weapons/w350/mechanics/ddc-exotic-rows.json`이다.
- Minecraft 피해·거리·투사체 속도·주변 대상 제한과 W46 계열 스탯 곡선은 현지 환산이다. 원작 수치 확정으로 표시하지 않는다. DDC의 불명확한 가시 PvP 강화 독 수치는 활성화하지 않았다.
- Crimson은 3발 점사 8회=24발을 소비한다. Outbreak의 35발 표시는 기존 완전 점사 정책에 따라 36발로 환산했다. Whisper는 정밀 3회마다 1발 생성+예비 2발 이동이며 무한 파워탄이 아니다.

## 모델과 프레젠테이션

초기 R1 블록 모델은 사용자 품질 피드백으로 반려되었다. 수락 기준은 첨부 W327 무기의 입체 실루엣·실제 구멍·재질 대비·정돈된 UV이다. 최신 사용자 지시에 따라 모델 담당은 Sol high로 변경했다.

원본 .blend를 별도 headless Blender에서 실제 평가했다. 원본에 유효한 플레이어 손·장전 action이 없어 장전 61 pose와 ADS 21 pose는 직접 작성한 근사 동작이다. 원작 장전을 추출·복원했다고 주장하지 않는다. 원본의 반투명 FX 카드는 본체 입체로 복사하지 않았다.

모든 native 출력은 지원되는 item JSON elements/회전/면별 UV 경로를 사용한다. 임의 `vertices`/`triangles` 필드를 사용하지 않는다. 본체와 탄창 등 동시 표시 조립체를 합쳐 1,000요소 이하로 검사한다. `scripts/art/w350/integrate_routes.py`는 전용 모델과 공용 피부색 손·HUD·Whisper 스코프 경로를 연결한다. Whisper 스코프의 원형 마스크는 기존 공용 저격총 마스크를 재사용한다.

R2 모델과 사용자 렌더 색/입체를 반영한 Whisper R3를 통합했다. Whisper995요소(본체980+탄창15), authored2048×1024아틀라스, 배포1024×512, 흰 뼈338요소 light_emission15, 푸른 렌즈20요소 light_emission8이다. 검은 기계 부품637요소는 비발광이다. 원작 bloom은 기본 렌더러에서 복원했다고 주장하지 않는다. 실제 1차 입력/PNG → Sol high 담당 검토 및 수정 → 통합 후 2차 입력/PNG 검수를 완료했다. 최종 범위와 한계는 아래에 기록한다.

## 사운드

36개 동작에 34개 단일 OGG, 합계 880,413바이트를 사용한다. 원본 무음 여백을 임의로 잘라내지 않고 모노48kHz Vorbis로 변환했다. 장전은 전체 길이 cue 한 개를 해당 기본 장전 시간에 맞춘다. 확률 선택용 variants는 추가하지 않았다.

파일 무결성·완전 디코드·이벤트/alias 연결은 검사했다. Graviton과 Tractor의 ADS는 draw cue 재사용을 명시했다. Tractor F0 발사 선택은 파일명이 불명확해 파형에 근거한 임시 선택이다. 이 세 선택을 원작 동작과의 확정 일치 또는 실제 스피커 청취 완료로 보고하지 않는다. 상세는 `audio/README.md` 및 `art/weapons/w350/audio/manifest.json`에 있다.

## 검증 상태

- 실제 Gradle compileJava 성공. 기존 카탈로그·프로필·손 그래프 targeted24개 성공.
- 신규 카탈로그/슬롯/탄약/27개 경로/사운드 연결 검사3개 성공. 최종 통합본 전체 JUnit에도 포함했다.
- ExoticCycle10 + SteadyHands6 + SnapshotCoverage1 = 17개 성공. 신규 9종 handling 곡선을 SteadyHands 공용 경로에 포함해 런타임 coverage 누락을 수정했다.
- 최초 실제 서버6개 검사 성공: Crimson 회복/재장전 및 소유 스택 교체, Thorn 독/회수, Whisper 정밀 탄약 회수, Sunshot 연쇄와 소스 취소, Tractor 약화/이동 정리, Pack Hunter 아군 강화.
- 확장13개 첫 시도는 Graviton 검사의 AE100 탄퍼짐 관측 방법과 SteadyHands coverage 오류로 실패했다. Graviton은 화면 반동과 별도로 실제 bloom 상태 증가를 비교하도록 fixture를 수정했다. 수정 후 실제 서버에서 **13개 필수 검사 전체 성공**(18:35:15 KST, Gradle3분8초). 로그는 QA 작업 폴더의 `gametest-thirteen-recheck.log`이다.
- 최종 전체 JUnit은2862개 중2859개 성공, 아래 기존 baseline3개 실패다. 신규 실패는 없다. 실제 Gradle jar task는 성공했으며, test task 실패 때문에 전체 명령의 종료 코드는1이다. 전체 BUILD SUCCESSFUL로 표시하지 않는다.
- 실제 팩 로드,9종 1·3인칭/ADS/자동 장전의 표시·복귀,20개 static item display 관측을 완료했다. 상세는 아래 최종 native 검수와 저장된 증거를 따른다.

이전 baseline 전체 JUnit에는 FireVariantsW98Test의 누락 QA inventory, GoldenGunHudW122AssetTest의 누락 GameTest 소스, MinorPveBalanceW342Test의 CYCLOPS 기대값 관련3개 실패가 있었다. 이번 변경으로 생긴 실패와 구분하며 전체 통과로 표시하지 않는다.

격리 QA는 `/tmp/exotic-expansion-20261109/qa`의 전용 서버·클라이언트를 사용한다. Vision은 사용자 지시대로 background=true, 정확한 로컬 서버 allowlist와 환경 변수 토큰, bounded keep_awake coordinator로 실행한다. 일반 사용자 프로필·인증·잠금 설정은 바꾸지 않는다. 원시 PNG/입력·서버 로그는 해당 QA 작업 폴더에 보관한다.

## 첫 native 팩 로드 실패와 수정

첫 native 시도에서 실제 item atlas stitch가 `destiny:item/weapon/w327/heritage`1024²를 수용하지 못해 팩 적용 및 접속이 실패했다. 이후 zip stream closed 다발 로그는 이 로드 실패 후 발생한 정리 오류다. W350의 큰 텍스처9개를 기존 SHA256 고정 무손실 atlas routing으로 items→blocks에 배치했다. 이 routing 자체는 해상도·UV·PNG 픽셀을 바꾸지 않는다. 별도의 해상도 변경은 아래 사용자 승인 정책으로 처리했다. atlas pin은 모델 변경 후 integrate_routes.py에서 함께 갱신한다. 첫 실패 로그는 client-r2-atlas-failure.log/server-r2-atlas-failure.log로 보존했다. 수정 뒤 native 팩 적용과 월드 입장에 성공했다. 첫 생성 ZIP204,871,454바이트는 팩 로드 수락을 통과한 빌드로 간주하지 않는다.

## 사용자 승인 모델 텍스처 축소

사용자의 추가 지시에 따라 authored 원본 대신 최종 배포 출력에서 큰 모델 텍스처를 최대1024px로 제한한다. 대상은 W350무기, BetterModel생성 item텍스처, class_ability모델, tutorial고스트이다. 폰트·HUD·일반UI와 minigame-lib는 정책에 포함하지 않는다. animation메타데이터가 있는 sprite sheet는 프레임 정의를 보존하기 위해 제외한다. 정규화UV와 종횡비를 유지하며, alpha가중 area필터로 투명 픽셀의 RGB가 흰 뼈·가시 경계를 어둡게 물들이지 않게 한다. sourcePNG·Downloads·봉인 QA 해시는 변경하지 않는다.

PackTextureResolutionTest3개와 PackAtlasRoutingTest4개 성공. 최종 생성 ZIP에서 실제 치수·용량을 확인하고 축소된 native모델을 검수했다. 이 축소는 무손실 압축과 별개의, 사용자가 승인한 해상도 변경이다.

## 생성 ZIP과 1차 화면 검수

1차 축소 ZIP은190,231,810바이트다. 이전 실패 ZIP204,871,454바이트와 비교해32PNG를 축소했고, 전체 PNG 픽셀 수는301,630,589→214,598,781이다. 선택32장의 픽셀 수는117,440,512→29,360,128(75% 감소)이다. Whisper 배포본1024×512, Graviton/Jötunn1024², Crimson/Thorn/Outbreak/Gjallarhorn1024×256, Tractor1024×512, Sunshot1024²를 실제 ZIP에서 확인했다. 원본 아틀라스와 모델 UV는 보존했다. 실제 클라이언트에서 팩 적용과 월드 입장에 성공했다.

1차 실제 입력 PNG로 hip/ADS/3인칭/빈 탄창 장전을 확인하면서 ADS 높이와 TWO_HAND 3인칭 방향의 결함을 발견해 담당 Sol에게 이미지를 전달했다. 처음 item-modify 직후 발사 시도는 무기 준비 시간을 기다리지 않아 발사되지 않았다. 이때의 `reload` 증거는 장전 검증으로 수락하지 않았다.25neutral ticks를 기다린 `reload-valid`만 실제 발사·탄창 복구를 server status와 대조한다. Q키를 native 입력으로 눌렀다는 증거는 아니다.

Crimson/Thorn/Outbreak HUD 누락 원인은 atlas filter의 부분 일치다.26.3 IdentifierPattern은 Pattern.asPredicate=find를 사용해 full-gun 경로가 `_hud`까지 제외했다. namespace/path 모두 ^...$로 고정하고, asPredicate에서 접미 sprite·다른 namespace를 거부하는 검사를 추가했다.2차 native에서 세 HUD 아이콘이 정상 표시되는 것을 확인했다.

1차 FPS 스냅샷은30→10이었다. 전용 QA 옵션에 Vsync=true/inactivityFpsLimit=afk가 남아 있어 최종 성능 수락값으로 사용하지 않는다.2차는 같은 QA 폴더에서만 Vsync=false/maxFps60/inactivityFpsLimit=minimized로 고정하고,1개/20개 표시를 같은 설정에서 관측한다. 최초 tutorial toast도 전용 QA에서만 껐다. 일반 프로필은 변경하지 않았다.

## 1차 검토 반환과 보정 통합

실제 캡처를 각 Sol high 담당에게 전달해 별도 검토 후 수정 delta를 받았다. Kinetic702경로(462쓰기+240옛 aim손 leaf삭제), Energy571경로, Power통합215경로를 전부 이전/이후 SHA256 검증 후 통합했다. Outbreak 조준기는 실제 열린 후드로, Thorn 가늠자는 상단 위로 조정했다. 8종 물리 조준 endpoint와 연결된 손 pose를 중앙 sight anchor로 재정렬했고 Whisper는 공용 scope overlay를 유지했다. 양손 6종의 3인칭은 실제 W327 Krait 양손 기준으로 보정했다. 손대지 않은 sourceatlas/원본 blend/재장전 타이밍은 보존했다. 아래2차 실화면으로 통합 결과를 확인했다.

## 최종 native 검수와 한계

- `native/hip.png`, `native/ads.png`, `native/third.png`는 실제2차 클라이언트 PNG9종을 모은 표다. 1차에서 발견한 조준 중심·양손 3인칭 방향·세 HUD 누락은 수정 후 재확인했다. 일반 hand cannon의 내려 든 대기 자세는 유지했다.
- 9종 실제 use 입력과 서버 탄창/예비 상태를 대조했다. 입력 후 lease 해제·heldKeys 비움·pendingSteps0·갱신 오류 없음은 `native-input-results.json`과 무기별 input JSON에 있다. Q키 수동 장전을 검사한 결과는 아니다. 화면에 보이는 장전 움직임과 복귀는 확인했으나, 가려진 손목·탄창의 정확한 접촉까지 인증하지 않는다.
- Whisper의 짧은 use pulse는 발사를 확인하지 못했으므로 그때의 reload-valid/reload-confirm 시도는 장전 증거에서 제외했다. 최종 수락 증거는 `second-whisper-fullmag-reload`이다. 정상3발/예비20에서25neutral→70use→100neutral 입력으로3발을 소비하고 자동 장전되어3발/예비17로 복구된 서버 상태를 확인했다. 짧은 pulse의 원인은 확정하지 않았다.
- `native/whisper-native-oblique-0.png`는 최종1K 적용 모델이다. `native/whisper-native-night-0.png`에서 밤에도 흰 뼈가 밝게 남고 검은 본체가 주변광에 따라 어두워지는 것을 확인했다. 추가 shader bloom을 구현한 결과는 아니다.
- `native/twenty-models-1.png`에서9종을 섞은 static item display20개를 동시에 표시했다. 서버 Count20과 실제 PNG를 대조했고 누락된 외형은 관찰하지 않았다. 같은 전용 설정의 두 스냅샷은60/55FPS였다. 20명 전투·프레임타임 백분위 벤치마크로 일반화하지 않는다.
- Vision 설정 backgroundMode/backgroundActive/backgroundGameplay=true를 확인했다. 캡처 중 windowActive=true도 기록되므로 OS 비활성 창 동작까지 별도 검증했다고 주장하지 않는다. 스피커 청취는 수행하지 않았다.

최종 팩은 **190,238,357바이트**, SHA256 `70db3742255e3ec1269fcd336c8fe960cf261726189eeb9660f8dccfce4a4d20`이다. 250,000,000바이트 목표 이내이며 콘텐츠를 제외해 달성하지 않았다.32장 선택 대상의 픽셀75% 감소는 전체 팩 메모리75% 감소를 뜻하지 않는다. Whisper R3의 추가 authored atlas 면적 때문에 앞선1차 전체 PNG 통계와 최종 전체 통계를 같은 값으로 취급하지 않는다. 최종 무기별 치수는 `pack-result.json`이다.

실제 Gradle JAR: `build/libs/destiny-guardians-0.1.0+26.3.jar`, **431,727,884바이트**, SHA256 `d5ddeadea49dabbc06e56dce4dd61cd6ea2f394f152212f06323f88d3c247124`. 원본 텍스처를 포함하는 JAR 크기와 생성 배포 팩 ZIP 크기는 다르다. `build-result.json`에 전체 테스트 실패 이름과 빌드 정보를 보관했다.

검수 종료 시 전용 display20개와 강제 로드9청크를 제거했다. 소유 client/server/coordinator 및 bounded awake가 종료됐고, Vision8102와 server25638 포트가 해제됐음을 확인했다. 일반 프로필과 사용자 scene은 변경하지 않았다.
