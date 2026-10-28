# W229 사운드 설치용 fragment

메인에 설치하지 않은 복사 가능한 산출물이다. 18 event definition / 17 unique mono OGG.

1. `assets/`를 프로젝트 `src/main/resources/assets/`에 병합 복사한다.
2. `sounds-additions.json`의 top-level 18개 키를 프로젝트 `src/main/resources/assets/destiny/sounds.json`에 병합한다. 기존 전체 sounds.json을 이 fragment로 덮어쓰지 않는다. additions 파일 자체는 Minecraft가 자동으로 읽지 않는다.
3. `provenance-mapping.json`, `listening-table.md/csv/html`은 master가 선택한 QA/출처 문서 위치로 보관한다. provenance는 JSON 주석 대신 별도 파일에 둔다.

키는 `ClassAbilityEffects.sound`의 `<class>.<element>.<action>` 규약이다. sound resource는 `destiny:classes_w229/<name>`이며 `.ogg` 확장자를 JSON name에 넣지 않는다. 모든 sound entry는 `stream:false`, `attenuation_distance:32`; runtime은 현행 `.65` volume을 사용한다. 별도 gain/normalization/trim/resampling을 하지 않았다.

- 12개 super.start/fire 중 numeric 11개는 `tentative_folder_family_only`다.
- `titan.solar.super.fire`는 `titan.solar.melee.cast`와 동일한 `Hammer_Throw_1` OGG를 의도적으로 공유한다. 정확한 원작 super Wwise/media 대응은 미확정이다.
- `titan.solar.melee.impact`는 `Hammer_Impact_1`, Titan VOID grenade는 Suppressor, Warlock VOID grenade는 Vortex의 명명 원본이다.
- 현재 Warlock ARC melee는 Chain Lightning이므로 `Ball_Proj_1`을 포함/연결하지 않았다.
- `Hammer_Ground_Impact_1`은 기존 processed/ogg에 보존되어 있다. 현재 공통 melee.impact hook에는 충돌 종류 구분이 없어 generic impact만 선택했다.
- 원본 범위는 source file 전체(청취표의 0–duration). game event 발생 시 상대 0초 재생 선택이며 원작 animation onset 검증값이 아니다.

통합 시점 유의: 읽은 TitanSuper snapshot은 `super.impact`를 호출하며 `super.fire` 호출은 없고, shared ClassAbilityEffects.attack도 sound dispatch가 없다. 이번 3개 Titan fire key는 준비했으며 실제 fire hook 연결은 master의 코드 통합 범위다. 이 조사에서는 Java를 변경하지 않았다. `super.end`, class ability, 이동 등 미식별 cue는 추가하지 않았다.

검증: 18 key/path resolve, 17 OGG Vorbis 실제 decode(1ch/샘플레이트/프레임 수/유한값), 원본 processed SHA256 동일, 기존 sounds.json 키 충돌 없음(기록된 스냅샷 기준). 게임/build/청취/완전한 pack load는 실행하지 않았다. standalone pack이 아니므로 pack.mcmeta를 임의로 만들지 않았다.
