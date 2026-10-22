# H16 — 실제2인·거리·환경·성능 증거

[단계별 문서23](../../../design/23_다인_거리_성능_검증.md) · [조건/원시 수치/해시](validation.json) · [실제 화면 모음](overview.jpg)

## 확인한 항목

- 실제 독립 Vision26.3 두 계정/포트/실행 폴더. [시전자1인칭](h16-owner-first-solar.png) / [상대에게 보이는 모델](h16-observer-solar.png) / [본인 QA3인칭](h16-owner-third-solar.png).
- 동시 궁극기: [시전자](h16-multi-owner.webp) / [관찰자](h16-multi-observer.webp). [발사와 관찰자 회피](h16-multi-third-observer.webp). 이 WebP는 측정한 캡처 간격이며60FPS 영상이 아니다.
- BM 거리: [47.99](h16-distance-47_99.png) / [48.00](h16-distance-48.png) / [48.01](h16-distance-48_01.png) / [64](h16-distance-64.png) / [복귀](h16-distance-return.png). 같은 이름의 JSON에 실제 클라이언트 엔티티 목록. 정밀 경계는 서버 viewer와 엔티티 수신/제거가 주 증거다.
- [늦은 실제 접속](h16-late-join-observer.png). 최초 접속의 미검증 채팅 안내 toast를 숨기지 않았다.
- 선 거리: [32](h16-single-beam32.png) / [64](h16-single-beam64.png) / [복귀](h16-single-beam-return.png).64에서 선은 렌더링되지 않지만 JSON에는 선4개가 남는다. 서버 전달 제한과 client viewRange를 혼동하지 않는다.
- 조명 비교: [낮](h16-light-day.png) / [자정](h16-light-night.png) / [차폐 방](h16-light-cave.png). 같은 카메라/HUD/옵션. [실제 Shadowshot 연결선](cave-void-links-owner.png) / [관찰자 시퀀스](h16-cave-void-observer.webp). 동적 광원/블룸 구현이 아니다.
- 실제 접속 종료: [이전](h16-disconnect-before.png) / [이후](h16-disconnect-after.png), JVM3 서버 로그에서4/4→0/0. 소유자의 단순 거리 이탈과 실제 접속 종료를 구분했다.
- [프레임 원본 해시·캡처 시각](frame-captures.json). PNG는1708×960 원본이며 overview/WebP만 축소했다.

## 성능의 주 증거 — JVM3

두 창 모두30초, 서버600표본, 클라이언트별30개의 native FPS 표본. HUD 유지,120FPS 제한, Apple M4 Pro/OpenGL/동일 장치 루프백이다.

| | 기준 | 8닻+8선 지속 부하 |
|---|---:|---:|
| Fabric END 포함 tickServer 평균 / P95 | 2.480 / 3.347ms | 2.160 / 2.883ms |
| 실제 START 진행률 | 19.9997 | 19.9989틱/초 |
| 두 클라이언트 FPS | 118~120 | 119~120 |
| 로드된 item_display, 각 클라이언트 | 15 | 47 |
| 합계 송신 패킷 / payload 바이트/초 | 44.26 / 601 | 603.01 / 13,550 |

- 서버: [기준](h16-whole_baseline.json) / [부하](h16-whole_load.json). `whole_tick_nanos`가 Fabric END 포함 호출, `tick_nanos`는 vanilla만이다.
- FPS: [기준](h16-perf-whole_baseline-clients.json) / [부하](h16-perf-whole_load-clients.json). 캡처 cadence가 아니라 `Minecraft.getFps()`를 읽었다. 모든 표본 inWorld/HUD 표시, 오류0.
- 패킷: [기준](h16-packets-whole_baseline.json) / [부하](h16-packets-whole_load.json), 원본 [JFR](server-2026-10-22-155237.jfr). 이벤트 timestamp로 각30초 구간을 필터링했다.
- 초기 `baseline/load/recovery/load_warm` 자료도 보존한다. 이때 vanilla MSPT는 END VFX 비용을 제외하며 시작 JFR 스파이크가 있다. 전체 틱 성능의 주 증거로 사용하지 않는다.
- 제한된 순차 표본이라 부하가 기준보다 빠르다는 인과 결론을 내리지 않는다. 글로벌48개 실클라이언트 성능, 최대 FPS, end-to-end frame percentile, 비동기 CPU 및 WAN 대역폭을 입증하지 않는다.

## 자동 회귀와 계측 검증

- [최종 빌드](h16-release-build-tests.txt): GameTest80/80, JUnit28/28, 실패·오류·스킵0. JUnit XML7개 동봉.
- [새9개 테스트 범위](test-coverage.md): 실제 BetterModel/Polymer 백엔드+내장 플레이어. 글로벌24+24 상한/격리/만료/정리이지 실제6인 렌더링 시험이 아니다.
- [HTTP 실패 유지 시험](h16-http-failure-check.json): 의도적으로 닫힌8199포트를 함께 폴링. 정상 포트 자료와 오류 레코드가 모두 보존됐다.
- [분리 Vision 출처/원본 options 해시](vision-source-manifest.json). 원본 저장소/옵션을 수정하지 않았다.
- 서버/클라이언트 JVM1~3 전체 로그를 함께 보존했다. 기존 HUD/particle/end_of_frame·오프라인 인증·Apple GL 경고는 신규 VFX 실패와 구별한다.
- 텍스트 로그의 줄끝 공백만 정리했다. 원본 PNG의 픽셀/색/노출은 변경하지 않았다.

## 재현 도구

서버를 중지한 뒤 Java25로 `rtk proxy ./gradlew runGameTest build --console=plain`.
격리된 평탄 개발 월드에서만 `JAVA_TOOL_OPTIONS=-Ddestiny.qa=true`를 게임 JVM에 전달해 실행한다.

서버 콘솔:
```text
destiny qa scene H16Caster
destiny qa load H16Caster
destiny qa load
destiny qa sample whole_load 30
destiny qa status
destiny qa stop
```

`load`는2400틱 제한. `stop`은 대상 소유자의 기존 효과도 정리하므로 운영 중 실전 플레이에 사용하지 않는다.
독립 비전 구성은 `scripts/qa/prepare_vision_h16.py`, FPS는 `sample_vision_h16.py`, JFR 구간 집계는 `summarize_h16_packets.py`를 사용한다.
새 destination만 허용하며 원본 options는 읽기 전용이다. 게임 실행은 계정·qaRunDir·visionPort를 다르게 지정한다.

5번 일반 총기/탄약/재장전은 미착수다. 인증 스킨·GCB 실제 전송·Vulkan·다른 해상도·청음·실제6인 이상 장기 부하는 남아 있다.
