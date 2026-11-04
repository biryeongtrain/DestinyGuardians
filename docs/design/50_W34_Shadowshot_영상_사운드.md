# W34 — Shadowshot Deadfall 영상 사운드 교체

작성:2026-10-23. 사용자 지정 영상의 소리를 가공해 W33 일반 활/화살 대체음을 교체한다.

## S1 — 출처 확인

- 영상: <https://www.youtube.com/watch?v=O0uvtZMID9E&t=1050s>
- 제목: Destiny 2 All SUPER Sounds - MEGA SHOWCASE including NEW SUPERS + PRISMATIC
- 업로더: thatguyHoody, 업로드2024-06-11.
- 챕터: **Shadowshot - Deadfall**,17:25–17:44(1045–1064초). 다음 챕터 Moebius Quiver와 구분한다.
- 실제19초 영상과10fps발동구간프레임을 열어 확인했다.17:30링크보다 약간 앞의 첫발 시퀀스가 비교적 정리되어 있어 사용했다.
- 사용자 요청으로 다운로드·가공·검수 파일 제공. 재배포 라이선스를 새로 확보한 것은 아니다. 원본AAC/영상/다운로드메타데이터는 ignored `run/private-sources/w34/`에만 보관한다.
- 원본format140 AAC(m4a)20,544,115bytes의SHA256: `4a6776d942b49a8fd614927b86ca93b79a89cee22809c733b3b566b0c714dd5f`.
- 영상에는 이미 여러 게임 소리가 합쳐져 있다. **공식개별stem추출/독립청음확인을주장하지않는다.** 프레임과파형에근거한mix편집이다.

## S2 — 구간과 가공

| 이벤트 | 원본초 | 용도/제약 |
|---|---|---|
| start |1047.17–1047.48| 초반에너지상승; 발동배정은추정 |
| draw |1047.48–1047.82| 상승구간0.34초,서버0.35초당김에대응.순수시위stem아님 |
| fire |1047.82–1048.48| 강한주트랜지언트+직후감쇠.발동층이섞여있을수있음 |
| impact |1048.60–1049.20| 두번째트랜지언트/감쇠를닻착탄으로배정.화면밖착탄정체미확정 |
| end |1049.25–1049.70| **발사잔향으로만든짧은닫힘음**,원작종료음을식별한것아님 |

- 원본AAC에서직접디코드한다.프레임확인용재인코딩영상의오디오를다시사용하지않는다.
- Mono32kHz;40Hzhighpass/14kHzlowpass;보수적FFTdenoise6dB,noise-floor -46dBFS.
- RMS목표-21dBFS/샘플peak-6dBFS/증폭최대9dB중보수적인gain.impact추가-2dB/end추가-9dB.
- 2msfadein,16–60msfadeout,end150msfadeout.피치변경/시간늘이기/루프/복제연결없음.
- libvorbisquality4,bitexact.재디코드peak/clip검사.코덱패딩으로실제디코드길이가원본창보다최대약30ms길수있다.
- 실제5OGG합계37,910bytes.하위경로`destiny:w34/hunter/void/super/*`.
- 기존5이벤트키를그대로사용해게임판정·궁극기애니메이션·카메라는변경하지않는다.종료키의기존발사후호출도유지되므로end는조용한처리잔향으로구성했다.

## S3 — 재현·기존 importer 보호

```sh
rtk proxy python3 scripts/audio/import_shadowshot_w34.py
rtk proxy python3 scripts/audio/import_shadowshot_w34.py --check
rtk proxy python3 scripts/qa/verify_shadowshot_w34.py
rtk proxy python3 scripts/audio/import_sounds_w33.py --offline --reuse-existing
```

모든명령은pinnedprivateAAC가필요하다.원본SHA가다르면자동변경/재다운로드하지않고거부한다.
W33 importer는W34manifest가있으면검증후5키를overlay하여후속실행으로일반활소리로되돌아가지않는다.
W33manifest/기존파일은이전출처로보존하고`active_overlay`로현재W34를명시했다.
84event/61activeOGG참조는유지되고실제활성음원합계는1,354,962bytes.팩에는기존W33비활성5OGG도이력호환용으로남는다.

## S4 — 사용자 검수 파일

`run/deliverables/w34-shadowshot.zip`과동명폴더:

- `00_all_processed_preview.wav`:start→draw→fire→impact→end,각0.5초무음간격.실제게임타이밍재현은아님.
- `01_start.wav`–`05_end.wav`:개별검수용.
- 동명OGG5개:리소스팩에적용한파일과byte동일.
- **WAV는실제OGG의16bitPCM디코드**여서가공전master를다르게듣는문제를피한다.
- `06_source_comparison_17m27.10-17m29.75.wav`:필터전2.65초mix비교.전체원본영상/21분음원은검수ZIP에포함하지않는다.
- manifest/README/SHA256SUMS첨부.사용자가직접청음후시점·잔향·볼륨을확정한다.

## S5 — 검증

자세한최종gate/실게임팩/입력결과는[W34QA](../qa/2026-10-23/w34/README.md).
JUnit2개추가:5키의영상overlay·원본chapter·이전importeroverlay표시·SHA/길이/mono/peak/정직한end표기.
별도Python은실제OGG재디코드와WAV정수PCM일치,ZIP전파일동일성을검사한다.
