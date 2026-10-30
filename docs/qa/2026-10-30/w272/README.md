# W272 장전 전용 무음: 실제 클라이언트 진단

## 상태

사용자가 Windows에서 발사·능력은 들리지만 장전만 들리지 않는다고 확인했다. 제품 코드를 임의로 바꾸지 않고 서버 패킷 이후 실제 클라이언트 경로를 검사했다. **Windows 현상은 아직 해결로 확정하지 않았다.**

## 검증

- Minecraft26.3 Danmo 격리 프로필에 QA 전용 mixin probe를 임시 추가했다. SoundManager.play 결과, entity-bound packet 수신 시 emitter 조회, 이후 활성 상태·removed·silent·선택된 OGG를 기록했다. probe는 제품 JAR에 넣지 않았다.
- Mac 데스크톱 접근과 QA 포트 소유권 확인 후 bounded awake coordinator를 사용했다. 기존 사용자 프로필·보안 설정은 변경하지 않았다.
- 첫 probe 시도는 helper를 mixin package 안에 둬 IllegalClassLoadError가 났다. QA 클라이언트가 종료된 뒤 helper와 mixin package를 분리했다. 제품 결함으로 분류하지 않는다.
- 첫 Ace fixture는 시각 프리뷰여서 발사·장전이 거절됐다. 실전 load로 바꾸고 실제 입력 발사를 확인한 뒤 서버 명령으로 정상 장전을 시작했다. 두 번째 무기 전환도 기존 탄약 보호로 거절돼 QA에서 생성한 Ace만 비운 후 Izanagi를 다시 장착했다. 잘못된 fixture 시도를 성공으로 세지 않는다.
- Ace reload55와 Izanagi reload61 모두 클라이언트 SoundManager.play 결과 STARTED, active=true, canPlay=true, volume=0.8이었다. 패킷 도착 시 ItemDisplay가 존재했고 removed=false, silent=false. 40틱 시점에도 활성 상태였으며 장전 종료 후 제거됐다.
- 실제 PNG로 Ace 장전 화면을 확인했다. OS 키 입력이 아닌 Vision native use로 발사했으며 장전 시작은 서버 명령이다. 스피커 출력을 녹음·청취한 검증은 아니다.
- 발사·장전 native 관찰 시퀀스4개는 completed이며 lease/키/대기 입력을 중립으로 돌렸다. QA 주 손을 Ace 프리뷰로 돌리고 자기 client/server 및 임시 awake coordinator를 종료했다. QA 전용 probe JAR은 제거했다. 운영 서버는 유지했다.

## 음원 검사 (병렬 작업)

| 음원 | 길이 | PCM RMS | 피크 | 10ms RMS > -50dBFS 시작 |
|---|---:|---:|---:|---:|
| Ace reload55 | 2.750s | -28.10dBFS | -5.86dBFS | 30ms |
| Ace fire | 2.700s | -28.24dBFS | -6.79dBFS | 20ms |
| Izanagi reload61 | 3.050s | -26.04dBFS | -5.52dBFS | 20ms |

대표3개 ffmpeg PCM 디코딩 통과. 장전 전체가 거의 무음이거나 긴 선행 무음인 문제는 없다. 따라서 근거 없는 음량 증폭을 적용하지 않았다.

## 클라이언트 코드 조사 (병렬 작업)

26.3의 handleSoundEntityEvent는 emitter ID가 없으면 조용히 버린다. 정상 AddEntity는 클라이언트 조회 테이블에 즉시 등록되므로 단순 한 틱 지연은 필수가 아니다. EntityBoundSoundInstance는 !entity.isSilent()로 재생 허용을 판단하고 isRemoved()로 종료한다. 빈 ItemDisplay나 렌더 컬링 자체에 대한 바닐라 무음 조건은 확인되지 않았다.

## 남은 Windows 비교

서버 콘솔에서 아래 명령을 실행하면 같은 장전 OGG를 임시 엔티티 없이 직접 재생한다. 사용자에게 결과를 요청한 상태다.

```text
destiny sound play weapon.reload_w83.ace_of_spades.55 andlist
```

직접 재생은 들리는데 정상 장전만 무음이면 임시 엔티티 전달·제거를 우선 조사한다. 직접 재생도 무음이면 Windows에 실제 적용된 팩과 클라이언트 로그를 확인한다. 현재 Mac 관찰만으로 Windows 전체 무음을 해결했다고 주장하지 않는다.
