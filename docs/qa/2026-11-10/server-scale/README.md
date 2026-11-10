# 30명 이상 서버 부하 최적화 — 진행 기록

목표는 30명 이상이 접속해도 네트워크와 서버 틱이 안정적인 시스템이다. 기준 통합본은 `9d0d1e9d9c`다. 무기·HUD의 중복 갱신 제거, 제한된 무기 데이터 캐시, 소유 월드의 거리 상한, 관전자 장비 패킷 경량화를 통합했다. 40개 네이티브 TCP 연결·18개 활동 인스턴스의5분 지속 시험과 단일 실제 클라이언트의 대표 화면 회귀를 확인했다. 운영13600KF / 8GiB 및 WAN의 최종 수용 검증은 남아 있다.

## 운영 사고 근거

사용자 환경은 i5-13600KF / RAM32GB / JVM 최대8GB다. 제공된 로그와 크래시 리포트는 원본을 변경하지 않았고, SHA256·숫자 요약은 `incident-evidence.json`에 보존했다. 개인 채팅·IP·전체 사용자 목록은 보고서에 복제하지 않았다.

- 11월8일14:45:13 Watchdog는 한 틱61초를 보고했다. 스냅샷의 서버 스레드 최상단은 당시 `ClientControls.java:70`이었다. 한 장의 스택은 그 메서드가61초를 전부 소비했다는 증거가 아니다.
- 힙은8141/8192MiB,14개 월드에서 로드 청크 합계67,262였다. 한 플레이어의 개인 월드에도8281개, 일부 빈 월드에도8천개 이상이 남았다. 메모리 압박과 과한 로딩 반경을 우선 조사한다. 소유 객체/GC 정지 시간은 힙/JFR 추가 측정 없이는 확정하지 않는다.
- `moved too quickly`는684회다. 초과 이동 판정이며 회선 스로틀링의 직접 측정값은 아니다. 서버 틱 지연·텔레포트 경계와 분리해서 해석한다. 이동 검증 기준을 완화해 증상을 숨기지 않는다.
- Spark1.10.187의 Windows WMI 출력 대기, 내보내기 처리 지연과 `ProtoTimeEncoder: No index for key` 오류가 별도로 기록됐다. [공식 WMI 구현](https://github.com/lucko/spark/blob/master/spark-common/src/main/java/me/lucko/spark/common/monitor/WindowsWmi.java), [공식 시간 배열 내보내기 구현](https://github.com/lucko/spark/blob/master/spark-common/src/main/java/me/lucko/spark/common/sampler/window/ProtoTimeEncoder.java)과 대응하는 경로다. 현재 master 소스와 운영 버전의 정확한 바이트 동일성을 주장하지 않는다. Spark 오류만으로 서버 정지의 원인을 확정하지 않는다.

## 검증할 범위

1. 정지한 무기 표시의 중복 변환/아이템 패킷이 사라지고, 조준·반동·장전·투척과 마커 변경은 유지되는지 확인한다.
2. HUD의 도형만 바뀌는 업데이트가 아이템 데이터를 다시 보내지 않으며, 치유 보간·즉시 피해·색/모델/오프핸드 전환을 보존하는지 검사한다.
3. 무기 데이터 캐시는 크기가 제한되고, 같은 틱의 컴포넌트/모델/아이템 교체·잘못된 NBT·슬롯 선택을 즉시 반영해야 한다.
4. Destiny 월드만 기본 view8 / simulation6 상한을 적용한다. 전역 설정·외부 월드는 보존하고, 전역 재설정·입장·리스폰·퇴장 후 서버 티켓과 클라이언트 캐시/시뮬레이션 패킷이 일치해야 한다. 카메라·로딩 준비·1인칭 culling도 같은 실제 거리를 써야 한다.
5. 네이티브 TCP30명 및40명 부하를 비교하고, 활동 월드가 여러 개일 때와 퇴장 후에도 청크/힙이 계속 누적되지 않는지 확인한다. 목표 측정 기준은 안정 구간20TPS, whole-tick p95<50ms / p99<100ms이며, 기준을 초과하면 원인을 계속 조사한다. 짧은 공유 월드 시험만으로 다중 활동/운영 PC 전체 수락을 선언하지 않는다.

## 부하 도구의 증거 경계

`ScaleLoopbackClient`는 실제 loopback TCP와 바닐라26.3 codec·압축을 사용한다. 독립 접속/keepalive/텔레포트/청크 배치 ACK를 처리하고 실제 압축 프레임 수신 바이트와 디코드된 패킷 종류를 집계한다. 서버와 JVM/CPU 및 레지스트리 스냅샷을 공유하며, 그래픽 클라이언트·계정 인증·WAN·동시 리소스팩 다운로드 시험은 아니다. 팩은 서버에서 생성·검증한 캐시 보유 상황을 가정한다.

부하 도구는 별도 opt-in QA 모드 `destiny-scale-qa`로만 등록하며 일반 GameTest 목록에 부하 시나리오를 넣지 않는다. 기본 GameTest 가속을 전용20Hz wall-clock pacing으로 바꾸고, 게임 팩/서버 pose 캐시가 실제 SAVED/HIT 상태가 된 뒤 시작한다. QA 옵션은 기존 팩 키에서 제외되는 `destiny.gametest.scale.*`에 둔다. 캐시 해시를 고쳐 강제 수락하지 않는다.

1-peer 연결 검증 후40-peer 기준 측정을 통과했다. 앞선 실패는 manual-only 테스트 선택, 팩 발행 이전 시작, 합성 클라이언트의 tick-end 패킷 누락, 큰 청크 창에 비해 짧았던 수신 제한 시간이었으며 성능 통과로 사용하지 않는다. 가상 서버의20Hz pacing은 절대 마감 시각을 사용해 외부 루프 비용과 spurious wakeup을 보정한다. 중력 없는 합성 플레이어는 onGround=false를 보내 바닥 복구 패킷을 유발하지 않는다.

## 기준40연결 결과

`baseline-shared-40.json`: Apple M4 Pro12CPU / RAM24GiB, Java25, 서버와 TCP peers가 공유하는 최대 힙8GiB. 전역/요청 시야32, 모든 실제 추적 청크 수신 후260틱씩 측정했다. MSPT는 처음60틱을 제외한 전체 서버 틱이며, TPS는 별도 wall-clock 관측이다. 청크 준비78.15초는 안정 구간에서 분리했다.

| 구간 | 관측TPS | MSPT p95 | 수신 압축 프레임 | 로드 청크 |
|---|---:|---:|---:|---:|
| 대기 | 20.00 | 23.60ms | 0.60MB | 8,281 |
| 회전·ADS·발사 | 19.99 | 33.23ms | 138.91MB | 8,281 |

발사 구간에서 실제 탄약 감소480발을 관측했고40개 연결 모두 유지·정리됐다. 짧은 공유 월드 측정이며 운영 PC/인터넷/다중 활동의 수락 결과가 아니다. 최적화 후 동일 조건 비교와 다중 인스턴스·퇴장 검증은 이어서 기록한다.

최적화 후40연결도20TPS를 유지했다. 대기 메타데이터는22,129→1,323개(약94% 감소), 로드 청크는8,281→1,849개, 청크 창 준비는78.15→7.61초였다. 발사 구간 p95는약33→19ms, 압축 프레임은138.91→52.93MB였다. 짧은 관측 창에서 탄약 감소가480→440발로 달랐으므로 바이트/관측 발수도 함께 보존했다(약289→120KB/발). 단일 실행의 CPU 수치를 정밀한 인과 효과나 운영 PC 보증으로 일반화하지 않는다.

별도30연결 검증은 대기/발사 모두20TPS, 발사 p95약15ms였다. 원시 틱·패킷 카운터는`optimized-shared-30.json`, `optimized-shared-40.json`, 비교 계산은`shared-40-comparison.json`에 있다.

## 장비 전송 경로

기준 JFR에서 장비 패킷168,480개가 비압축281,742,718바이트(평균1,672바이트)를 차지했다. 최적화 후 장비 패킷은159,120개 / 32,643,851바이트(평균205바이트)였다. 관측 패킷 수 차이를 제외한 평균 크기가약88% 줄었다(`jfr-equipment-summary.json`). 회전 패킷은 두 종류 합계 약1.9MB로 훨씬 작았다. 장비 변경 감지 자체를 바꾸거나 장전·조준 프레임을 생략하지 않는다. 전송 시 정상 Polymer 외형을 만든 뒤, 다른 플레이어의 정규 무기에 한해 복원용CUSTOM_DATA와LORE를 제외한다. 자기 장비·인벤토리·컨테이너·표시 엔티티·비정규 아이템은 기존 경로를 사용한다.

캐시된 실제 팩의3,776개 item 그래프에서CUSTOM_DATA/LORE를 조건으로 사용하는 참조는 없었다(`observer-render-dependency-audit.json`). 실제 인코딩 검사에서 모든 다른 컴포넌트의 동등성과 원본 스택 보존을 검사한다. 렌더링 PNG는 별도 증거다.

## 검사 상태와 재현

### 임시 월드의 주기 저장

운영 설정은 사용자 확인으로view-distance32 / simulation-distance6이다. 공격전·캠페인은 이미Fantasy temporary level을 사용하고 있었다. 다만 [Fantasy0.8.4+26.3 구현](https://github.com/NucleoidMC/fantasy/blob/v0.8.4%2B26.3/src/main/java/xyz/nucleoid/fantasy/RuntimeLevel.java#L82)은`style == PERSISTENT || !flush`이면 부모 저장을 호출하므로`flush=false`인 자동 저장도 실행한다.

첫5분 시험은약20TPS / p95약16ms였지만최대1,268ms 틱이 있었다. 자동 저장과 동일한`saveEverything(true,false,false)`를40연결/18임시월드에 호출해814ms를 재현했고,18임시월드의 부모 저장 합계는693ms였다(`instances-40-save-before.json`). 한 장의 스택이나 시간 정렬만으로 원인을 단정하지 않고 실제 저장 경계를 계측한 결과다.

공용`TemporaryActivityLevel`을 캠페인·공격전·튜토리얼·시련의 장 생성자에만 연결해 주기적인 월드 전체 저장을 생략한다. 영구 탑과`PlayerList.saveAll`은 기존 경로를 유지한다. **`noSave=true`로 설정하지 않는다.** 그 플래그는 네이티브 청크 언로드 처리도 막으므로, 개별 청크의 언로드 시 저장과 같은 인스턴스 내 재방문을 보존해야 한다. 실제 dirty gold block의 자연 언로드·새 청크 객체로 재로드·블록 유지 및 체크포인트 디스크 복원을 포함한 네이티브3개가 통과했다(`temporary-save-native.json`).

언로드 검사 중 가상 GameTest 서버의 시간 예산 문제를 수정했다. 외부에서20Hz로 기다리기만 하면 네이티브 가속 시계의오래된시간 예산 때문에 작은 unload callback 큐가 처리되지 않을 수 있었다. opt-in QA는 같은 실제50ms 마감 시각을 네이티브 tick에 전달한다. 초기 공유/다중 시험은 이전 예산 버전이며, 최종 지속 시험은 이 수정 이후의 결과로 구분한다.

### 퇴장 티켓 판정

Fantasy는 월드를 서버/차원 레지스트리에서 제거할 때 네이티브`UNKNOWN` 티켓 일부를 남긴다. 원래의`hasTickets()==false` 판정으로 실패했던 시험은 전체 유형을 기록해 다시 조사했다.18개 모두`UNKNOWN`만 남았고 dimension keep=false / forced columns0이었다. 수정된 판정은 서버에 월드가 없고,강제/keep 티켓이 없으며,남은 유형이 정확히네이티브UNKNOWN뿐일 때만 허용한다. 다른 활동 소유/플레이어 티켓은 계속 거부하며 티켓을 강제 삭제해 검사를 통과시키지 않는다. 원시 실패는`instances-40-first-cleanup-failure.json`과`instances-40-soak-original-oracle-failure.json`에 보존한다.

### 기존 검사와 빌드

소유 월드 반경/클라이언트 패킷 복원, 무기 표시 dirty-data, HUD 변화, 캐시 무효화의 네이티브9개가 통과했다(`native-core.json`). 장비의 실제 Fabric 인코딩·디코딩2개도 통과했다. 첫 no-context 검사의 원본=디코드 기대값은 기존 Polymer 재작성 규칙과 맞지 않아, 독립된 일반 item codec 결과를 기준으로 고쳤고 제품 코드는 바꾸지 않았다.

첫 전체JUnit은2,873개 중5개 실패였다.3개는 기존 파일/기준값 문제이며,2개는 캐시 도입으로 달라진 코드 본문을 고정하던 검사다. 후자의 호출 경로와 읽기 전용·크기 제한 검사를 갱신한 후 targeted15개와 위 native2개를 포함한 실제 Gradle build가 통과했다(`targeted-build.json`). 전체JUnit 통과로 보고하지 않는다. 기본 build의 GameTest 자산 준비120초 제한으로 한 번 중단됐으며, 명시적 전용 run-dir/600초 준비 제한으로 재실행했다. 최종 JAR과 포함된 minigame-lib accessor 검사는`artifact.json`에 있다.

```sh
python3 scripts/qa/run_server_scale.py --run-dir /tmp/destiny-scale-owned --players 40 --phase-ticks 600 --jfr
```

새 전용 디렉터리 또는 이 도구가 만든 소유 표식이 있는 디렉터리만 사용한다. Java25가 필요하며 결과는 전용 디렉터리에 보관한다.30명 시험은`--players 30`, 장시간 시험은`--phase-ticks 6000`을 사용할 수 있다. 일반 GameTest 실행에 부하 fixture를 자동 등록하지 않는다.

다중 인스턴스는`--scenario instances --players 40`이다. 실제 운영 기본값인 캠페인 활성화를 명시한다(일반 GameTest는 레거시 튜토리얼 때문에 기본 비활성).4악마의 소굴 파티×3명 +2엑소더스 파티×3명 +12개 개인 캠페인 +10명 탑, 총18개 임시 활동 월드를 사용한다. 캠페인의 등록된 QA 명령을 통한 전투 단계 이동은 fixture 준비이며 자연 진행 검증이 아니다. 실제 ZIP/해시를 확인한 warm-cache ACK만 사용하고 팩 다운로드·외부 회선은 측정하지 않는다. 재접속 유예는 변경하지 않으며 정상 명시적 퇴장과 구분한다.

운영 Windows의 Spark 독립 CPU/GC 캡처는 [WINDOWS_CAPTURE.md](WINDOWS_CAPTURE.md)를 따른다. Windows 실행 자체는 미검증이며, macOS JDK25 프로브로 명령 파일·공백 경로·민감 이벤트 제외 구문만 확인했다.

### 최종40연결·18인스턴스 지속 시험

수정된 실제20Hz 시간 예산에서6000틱(약5분) 지속과정상퇴장을 통과했다(`instances-40-final-soak.json`, `final-soak-summary.json`).40개 실제TCP연결,18임시활동월드+탑,144생존NPC,55,415로드청크에서20.0007TPS / p95 14.27ms / p99 16.14ms / 최대63.97ms였다. 종료시힙사용4,703MiB는강제GC없이읽은사용량이며live-retention수치가아니다. 전체GC누적450ms였다.

정확히같은자동저장플래그의명시호출은52.04ms, 실제서버6000틱의주기저장은47.36ms였다. 계측된부모월드저장은기본3차원과영구탑뿐이었고18임시월드는해당일괄경로에들어가지않았다(의도적으로호출을생략한것이며0ms실행으로표현하지않음). 플레이어저장은기존전역저장호출에포함됐다.18개임시월드는정상퇴장후1틱내에레지스트리에서제거됐고강제/keep티켓과활동소유권이남지않았다. 재접속유예120초경로와실제인간/WAN/운영13600KF/장시간메모리누수인증은이시험의범위밖이다.

월드·시련의장·캠페인·빌드와캐시/관찰경계의targeted219개JUnit및Gradle assemble이통과했다(`final-targeted-assemble.json`). 전체JUnit의기존3문제는별도잔여항목으로유지한다.

## 실제 화면 검수와 종료

[화면 검수 기록](visual-qa.md)과 `visual-qa.json`에 대표 ADS·자동 장전·수류탄·관전자 장비·HUD·궁극기 카메라의 실제 PNG와 네이티브 입력을 보존했다. 단일 렌더링 클라이언트 검수이며 전체 무기/궁극기 아트 수락이나 다중 그래픽 클라이언트 성능 검증으로 확대하지 않는다. 소유 입력 lease·client/server·bounded awake를 정리했다.

## 연결 종료와 동시 재접속 보완

후속 [lifecycle 검증](lifecycle.md)에서 동시 재접속의 좌석 교착과 서버 스레드 밖 disconnect 이벤트로 인한 빈 월드 잔존을 재현했다. 정확한 현재 플레이어와 연결을 소유하는 공용 `PlayerPlacementBatch`로 복귀 목적지를 함께 계획하며, Fabric server-play disconnect를 native CAS 이전에 소유 서버 스레드로 넘긴다. 의도적12개/전체52개 연결 종료가 한 번씩 서버 스레드에서 관측됐고,6명 동일 run 복귀와 원래120초 유예 후 삭제,40개 계정의18월드 입장/퇴장 두 회차가 통과했다. 초기 실패와 강제 종료한 진단 시도는 별도 보고서에 보존했다.

`artifact.json`과 `final-soak-summary.json`은 첫 통합 커밋5e5b7e48 당시의 기록이다. 후속 빌드와 검증은 r2 artifact 및 lifecycle 보고서를 사용한다. 첫 전달 JAR의 안정 사본은 Downloads의 `DestinyGuardians-server-scale-20261110` 폴더에 보존한다.

후속 네이티브14개 회귀도 통과했다. 현재 전달 빌드는 `artifact-r2.json`에 있으며, 전체JUnit 기존3실패는 `lifecycle-full-unit.json`에 그대로 기록했다. 운영 진단은 사용자가 직접 실행해 전달하기로 했다.
