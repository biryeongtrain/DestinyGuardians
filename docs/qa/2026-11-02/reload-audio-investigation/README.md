# 장전음 무음 조사 — 2026-11-02

사용자 보고: Fabric Danmo에서 발사음은 들리지만 모든 장전음이 무음. `destiny sound play weapon.reload_w63.weapon.auto_rifle.reload.44` 직접 재생은 들린다.

## 확인

- 로컬 Danmo (1) 프로필: Minecraft26.3, Fabric0.19.5. 플레이어/마스터 음량1.0.
- 최신 JAR, 격리 서버 팩, 해당 프로필 캐시 팩의 sounds.json 모두 장전 이벤트98개와 참조 OGG 존재. 원격 사용자 팩의 동일성을 확인한 것은 아니다.
- 소리를 실제 듣는 검사는 사용자 직접 재생 응답만 근거다. 아래 client STARTED는 오디오 엔진 수락이며 스피커 청취 증거가 아니다.

## 격리 재현

Danmo (1)의 모드·설정을 /tmp/destiny-reload-probe/run에 복제했다. 일반 프로필은 변경하지 않았다. QA 전용 Vision 및 임시 진단 mixin으로 수신 sound-entity 패킷, SoundEngine.play 반환값, emitter remove 시간을 기록했다.

- 격리 서버25600, 클라이언트Vision8102. GCB4.0.0 모드 handshake 확인.
- native attack 입력으로 Gnawing Hunger 탄약41→33. GCB 환경의 use 입력은 이 테스트에서 발사하지 않아 attack으로 검증했다.
- 서버 `execute as MinigameQA run destiny weapon reload`: 장전 시작, 실제 entity-bound 이벤트 `.35`가 PLAYERS/STARTED/canPlay=true로 실행됨.
- sound 패킷의 ItemDisplay가 존재하고 silent=false, removed=false였다. 약1.73초 뒤 emitter remove 및 sound stop. 탄약41로 회복.
- 직접 `.44` 이벤트는 SimpleSoundInstance로 STARTED. 사용자 직접 재생과는 길이가 다른 변형이므로 동일 음원 바이트라고 주장하지 않는다.
- 로컬 복제 구성에서는 보고된 무음을 아직 재현하지 못했다. EntityCulling이나 임시 emitter 소실을 확정 원인으로 간주하지 않는다.

## 다음 판별

문제가 나는 실제 서버의 위치/실행 JAR 및 무기를 확인해야 한다. 동일 클라이언트에서 장전 명령과 실제 Q 입력, 실제 전송 이벤트, start→stop 간격을 비교할 필요가 있다. 현재 제품 동작은 수정하지 않았다.
