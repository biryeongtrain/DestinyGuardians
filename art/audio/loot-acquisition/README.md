# 희귀도별 아이템·엔그램 획득음

2026-11-09 사용자가 직접 제공한 WAV와 희귀도 지정에 따른 공용 획득음이다. 원본 위치·SHA-256·오디오 정보와 변환 결과는 `manifest.json`에 기록한다. Downloads의 원본 WAV는 수정하지 않는다.

| 원본 | 적용 희귀도 | 이벤트 | 전체 길이 |
| --- | --- | --- | --- |
| File0040.wav | 일반·고급·희귀 | destiny:loot.acquire.basic | 2.644초 |
| File0041.wav | 전설, 최상급 엔그램 | destiny:loot.acquire.legendary | 1.278667초 |
| File0042.wav | 경이 | destiny:loot.acquire.exotic | 6.148초 |

Minecraft용 OGG Vorbis(quality 6)로 변환했다. 세 파일 모두 원본 48kHz·스테레오·전체 granule 길이를 보존하며 자르기, 음량 정규화, 믹싱, 재생 속도 변경을 적용하지 않는다. 변환된 전체 파일의 디코딩도 확인한다. 세 OGG의 합계는 **209,927바이트**다. 재생은 획득자에게만 보내고 pitch=1, volume=1, PLAYERS 카테고리를 사용한다.

`python3 scripts/art/build_loot_acquisition_audio.py`로 변환한다. `--sources`와 `--ffmpeg`를 지정할 수 있다. 기존 프로젝트에 보관된 libvorbis 지원 ffmpeg를 기본으로 사용하며, 빌드 도구 해시도 manifest에 남긴다. 이 Mac의 기본 Homebrew ffmpeg에는 libvorbis 인코더가 없으므로 그 바이너리를 그대로 대입하면 변환되지 않는다.

장비는 신규 획득 공용 경로인 `GearAcquisition.store`가 성공한 경우에만 재생한다. 엔그램은 실제 보관 후 획득 알림 경로에서 재생하고, 기본 무장 중 바로 장착되는 무기도 개별 희귀도를 사용한다. 보관함의 정렬·장착 교환·이동은 기존 `WeaponStorage` 경로를 유지하므로 획득음을 추가하지 않는다. 엔그램 해독, 보관함 초과의 엔그램 대체, 우편 수령, 관리자·안내 연습용 장비 지급에도 같은 희귀도 규칙이 적용된다. 기존 임시 pickup/decode 소리는 제거해 중복 재생을 피한다.
