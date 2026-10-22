# H17 — 데스티니식 궁극기 준비/발동 HUD 검증

- **GameTest90/90 · JUnit37/37**, 실패/오류/스킵0. [빌드 전체](automated_build.txt) · [JUnit 집계](junit_summary.json).
- [실제 화면 모음](overview.jpg) · [조건/한계/해시](validation.json) · [단계별 구현](../../../design/24_궁극기_준비_HUD_연출.md).
- Minecraft26.3 / Fabric0.20.1 / BetterModel3.5.1 서버와 Copper Golem Vision26.3/Loader0.19.5.
  Apple M4 Pro/macOS26.1/OpenGL, **실제1708×956**, HUD표시/1인칭, 20TPS 목표,
  VSync off/120FPS제한/render10. H16(1708×960)과 해상도가 다르다.
- 최종 아트는 **서버JVM3**만 근거로 사용했다. 새 리소스54개(18 PNG+18 model+18 item)는
  촬영 서버 생성 팩과 byte 동일하다. [검사 해시](runtime_pack_assets.json).

## 실제 프레임버퍼

| 조건 | 원본 PNG | 측정 간격 WebP |
|---|---|---|
| Arc 낮 충전 완료 | [대표](final_arc_ready_day/020.png), [만료 후](final_arc_ready_day/046.png) | [전개/스윕/유지/정리](final_arc_ready_day/sequence.webp) |
| Solar 밤 충전 완료 | [대표](final_solar_ready_night/020.png) | [준비/정리](final_solar_ready_night/sequence.webp) |
| Arc 발동 | [대표](final_arc_cast/015.png) | [발동](final_arc_cast/sequence.webp) |
| Solar 발동 | [대표](final_solar_cast/014.png) | [발동](final_solar_cast/sequence.webp) |
| Void 즉시 발사/세션 종료 | [짧은 발동 유지](final_void_release/014.png) | [발사/정리](final_void_release/sequence.webp) |
| 실제100% 재접속 | [초기](final_rejoin_full/001.png) | [준비 상태](final_rejoin_full/sequence.webp) |
| 직업/서브클래스 변경 후100% | [정적 준비 상태](ready_settled.png) | 배너 재생 없음 |
| 직업none | [체력만 유지](class_none.png) | 능력 HUD정리 |

`guardian super99.8` 설정 후 실제 수동 발동 없이 수동충전이 아닌 **패시브 충전 tick**으로100%를 넘었다.
궁극기 발동은 `guardian action super`, 공허는 같은 콘솔 제출에서 `primary`를 이어서 호출했다.
실제 키보드/GCB 전송 검증이 아니다. [서버로그](server_jvm3_final.txt)에 명령/시간/접속 기록이 있다.

WebP는 캡처 간격을 측정해 만든 검토 자료다. 10/12.5fps 요청 간격은 실제 게임 FPS가 아니다.
[시간 배열](frame_captures.json)과 각 폴더 `frames.json`에 실측을 남겼다.
PNG14장만 선별 보존했고 원본 전체 프레임은 임시 캡처 폴더에 있다. 원본 PNG에는 합성/보정이 없다.
모음은 원본의 축소+제목일 뿐이다. 재접속 초기 Minecraft 리소스팩/서명 안내 토스트는 제거하지 않았다.

## 자동 검증/한계

- 신규GameTest10개: 초기100%/새충전/56틱만료/동일틱재사용/owner격리/none/관전자·죽음/
  실제Arc발동·post보존/직업·로드아웃/공허12틱발동 유지(일부 항목을 한 테스트에서 함께 검사).
- 신규JUnit9개: 순수 상태7개(중복·재충전·변경·래핑·즉시종료), 에셋2개(18경로/가운데70%투명).
- 20노드 예산: 상시15(흡수16), 준비+3=최대19, 발동+1. 새 월드/BM 트래커 없음.
  이는 설계상 노드 수이며 이번에 패킷/전체 틱 성능을 다시 계측한 것은 아니다.
- 테스트 레이아웃 검사 성공. 구형 도구가26.3 GameTest fixture를 탐지하지 못하는 경고1개는 남았다.
- 초기빌드에서 아직 생성 전인 테스트 클래스 등록 때문에 실패한 로그도 보존했다.
  이후 등록/클래스 통합 후90개 통과했다. JVM1은 stdin닫힘→SIGTERM143이며 화면 검증으로 집계하지 않는다.
  JVM2검토 뒤 밝은하늘 가독성을 수정했고 재빌드/새JVM3로 촬영했다.
- 최종로그에서 새18모델/텍스처/쉐이더 누락은 관찰되지 않았다. 기존HUD/장비 particle참조,
  Apple GL shader/end_of_frame/오프라인 인증 경고는 유지된다. 신규18모델 particle참조는 명시했다.
- 원작의 정확한 폰트/모션 시간/음향, 진짜 블룸/볼류메트릭/동적광원은 구현하지 않았다.
  다인/성능은 H16의 한정된 증거를 유지하며 H17실클라이언트 다인/성능 재검증은 하지 않았다.
  인증스킨/GCB 실제 통신/Vulkan/다른해상도/청음 미검증, 오프라인limb색 폴백은 미해결이다.

## 종료/보존

서버JVM2/3정상종료(JVM1 stdin문제로SIGTERM), 자신의클라이언트4회만 종료했다.
효과0/빔0, Arc/first/스폰/에너지0/낮/맑음 복원.25565/8102/8103비점유.
원본Vision프로젝트 Git clean, options SHA256동일. 일회용 `/tmp/destiny-h17-vision`만 사용했다.
일반총기/탄약/재장전(로드맵5)은 미착수다.
