# W232 타워 스폰 월드

## 목적과 배포

`destiny:tower`는 바닐라 클라이언트가 접속하는 서버 전용 Fantasy 영구 월드다. Fantasy `0.8.4+26.3`을 고정하고 배포 JAR에 중첩 포함한다. 기존 Overworld/다른 차원의 지형·월드 스폰·규칙·시계·플레이어 게임 모드를 바꾸지 않는다. 런타임 GLB 해석, 외부 모델 경로, 임시 바닥 플랫폼 생성은 없다.

일반 서버에서는 기본 활성화한다. 관련 없는 QA/GameTest 실행은 **서버 JVM**에 `-Ddestiny.tower.enabled=false`를 전달한다. 비활성화 시 타워를 열거나 플레이어를 이동하지 않으며 `/tower`는 한국어로 비활성 상태를 알린다. 등록된 generator codec은 유지된다. 통합 서버 JVM 옵션과 Gradle 데몬 JVM 옵션은 서로 다를 수 있으므로 master가 실제 실행 JVM을 확인한다.

Fantasy 정확 버전의 Maven 아티팩트와 sources JAR을 검토했다. OLD26.1 로컬 Fantasy checkout은 API 근거로 사용하지 않았다. 배포 원본: https://maven.nucleoid.xyz/xyz/nucleoid/fantasy/0.8.4+26.3/

## 데이터 계약과 생성

번들 입력은 `/data/destiny/tower/courtyard.vox.gz`, `/data/destiny/tower/courtyard.json` 두 파일이다. geometry/변환·원본 provenance·스폰의 최종 값은 master가 생산하는 manifest가 결정한다. 문서나 코드에 현재 좌표를 중복 고정하지 않는다.

바이너리는 gzip 내부 big-endian으로 다음을 담는다.

1. ASCII `DGTWR001` 8바이트.
2. int32 palette 개수. 각 항목은 uint16 UTF-8 바이트 길이와 바닐라 전체 block state 문자열.
3. int32 voxel 개수. 각 항목은 int32 절대 x/y/z와 uint16 palette index.

기록 없는 좌표는 공기다. 닫힌 면 채우기나 높이 기반 지면 생성 없이 기록된 블록만 배치하므로 원본의 문·창·난간 사이·중정 빈 공간을 보존한다. 팔레트는 바닐라 비공기 상태만 허용하고 실제 상태/속성은 26.3 `BlockStateParser`로 검증한다. 범위 밖·잘린 gzip·중복 좌표·잘못된 palette index·manifest 개수 불일치·후행 데이터는 거부한다. sparse map은 청크별 primitive 배열로 변환 후 외부에 배열을 노출하지 않는다.

Fantasy 기본 차원은 minY=0/height=256이므로 음수 Y 계약과 맞지 않는다. 타워는 바닐라 `BuiltinDimensionTypes.OVERWORLD`의 -64~319 범위에 독립 Fantasy 시계를 사용한다. 이 범위를 넘는 manifest는 로드 실패한다. generator의 `buildTerrain`은 해당 청크의 원본 복셀만 넣고 높이맵을 갱신한다. 구조물·장식·몹·맵 외부 청크는 Fantasy VoidChunkGenerator 경로에서 비활성화된다. 전용 등록 codec `destiny:tower_voxels`는 번들 맵을 다시 해석할 수 있다.

## 수명주기와 이전 월드 보존

서버 시작 때마다 `Fantasy.get(server).getOrOpenPersistentLevel(destiny:tower, config)`를 호출한다. Fantasy는 영구 월드를 자동 복원하지 않으므로 이 재개 경로가 필요하다. 기존 ID가 타워 전용 RuntimeLevel/generator 소유가 아니면 기존 월드를 변경하지 않고 치명적 오류로 중단한다.

타워는 Minecraft 정상 저장·종료 경로를 사용한다. stop에서 `delete()`나 `unload()`를 호출하지 않는다. 서버가 완전히 멈춘 뒤 Java 소유 참조와 재시도 표만 비운다. 저장된 Creative 관리자 편집은 재접속/재시작 시 유지되며, 기존 저장 청크를 최신 복셀로 덮어쓰거나 재생성하지 않는다. 번들 갱신은 아직 생성되지 않은 청크에만 반영되므로 지도 교체/마이그레이션은 별도 운영 작업이다.

맵 누락·손상·알 수 없는 블록 상태·ID 충돌·안전한 스폰 부재는 **치명적 시작 실패**다. `타워 맵을 읽을 수 없습니다`, `타워 스폰 주변에 안전한 바닥과 머리 공간이 없습니다` 등의 원인과 함께 서버 시작을 중단한다. 안전 스폰 검증 전에 RuntimeLevel 소유 state가 설정될 수 있지만 시작 실패 이후 정상 운영으로 계속하지 않는다. 자동으로 원본을 수리하거나 이전 월드로 대체하지 않는다. 원인 자산을 수정하거나 관련 없는 QA에서는 JVM 비활성 옵션을 사용한다.

## 이동과 보호

`/tower`는 일반 유저도 사용할 수 있고 플레이어 전용이다. 성공·비활성·안전 지점 부재·콘솔 실행 결과는 한국어다. 로그인 시 PLAY_TIME 통계가 0인 신규 플레이어 또는 타워에 저장된 재접속 플레이어만 타워로 이동한다. 기존 플레이어의 다른 월드 로그인 위치는 유지한다. 통계 파일이 삭제된 이전 플레이어는 신규로 판정될 수 있다. 실제 사망 후 respawn은 타워로 보내고, 살아 있는 End 복귀는 이 경로에서 강제 이동하지 않는다. 기존 개인 침대/앵커 respawn 설정 자체는 덮어쓰지 않는다.

타워 플레이어가 manifest의 returnBelowY 아래 또는 월드 경계 밖에 있으면 서버 시작 틱에서 귀환한다. 월드 경계 중심은 `(min+max+1)/2`로 계산하여 음수 Z 외곽을 포함한다. width는 manifest worldBorder 값이다. 귀환 실패는 100틱 간격으로 재시도하고 안내한다.

전송 전 목적 청크를 로드하고 실제 저장 블록의 단단한 바닥, 비유체 지지대, 비위험 블록, 발·머리의 공기, 몸 충돌과 월드 경계를 확인한다. 정확한 manifest 스폰이 막혔다면 수평 반경 8블록/수직 ±8블록 안에서만 안전한 대안을 찾는다. 없으면 전송을 거부한다. 블록을 삭제하거나 바닥을 생성하는 보정은 없다.

전송 직전에 `AbilityService.cleanup`, `WeaponRuntime.cleanup`, `CameraViews.stop`, 기본 camera 복원·탑승/아이템 사용 해제·낙하거리/속도 정리를 수행한다. 게임 모드는 바꾸지 않는다. 일반 사용자의 타워 블록 파괴·좌클릭·블록 사용과 공중 bucket 사용을 이벤트로 막는다. Creative **동시에** `COMMANDS_ADMIN` 권한인 사용자에게만 편집 override를 허용한다. 이 권한은 사망/피해/폭발 방지와 별개다.

타워 플레이어 피해는 월드 한정 ALLOW_DAMAGE listener에서 거부한다. 타워 전용 RuntimeLevel의 정확한 26.3 `explode` override가 바닐라 폭발 블록 파괴·발화·넉백을 차단하고 `canSpreadFireAround`가 항상 false를 반환한다. 독립 규칙에서 시간·날씨 진행, random tick, 몹/스포너/습격, mob griefing, TNT, 발사체 블록 파괴, PvP를 막는다. 몹 ALLOW_LOAD도 타워에 한정하여 거부한다. 관리 명령이나 외부 모드가 직접 setBlock을 호출하는 것까지 일반 플레이어 이벤트가 막는다고 주장하지 않는다.

현재 제품 Java 전체에서 `setBlock*`, `destroyBlock`, `removeBlock`, `ServerExplosion` 호출을 검색했으며 타워 생성기 외에 능력·무기의 직접 지형 변경 경로는 발견하지 못했다. Firefly의 동명 explode는 일반 Minecraft 지형 폭발 호출이 아니다. 일반 능력 사용을 전역 금지하지 않는다. 향후 직접 지형 변경 능력 추가 시 타워 소유 정책을 함께 반영해야 한다.

## 검증과 남은 시나리오

추가한 JUnit 디코더 테스트는 sparse/음수 청크·공기·속성·불변 팔레트와 주요 손상 입력 거부를 다룬다. 숫자별 테스트는 추가하지 않았다. TowerW232GameTests는 영구 open 재사용, 이전 월드 규칙/스폰 분리, 유한 생성, 실제 안전 도착, 전송 cleanup/모드 보존, 블록/피해/폭발/화재 보호, 막힌 머리 공간을 수리하지 않는 동작을 다룬다.

타워 GameTest는 `manualOnly=true`다. 관련 없는 전체 gate에서 비활성 타워를 억지로 열지 않도록 한 선택이다. master가 활성화된 별도 서버에서 명시적으로 이 테스트를 실행해야 한다. 다른 GameTest와 공유 타워를 동시 변경하지 말고 순차 실행한다. 플레이어/편집 fixture는 종료 시 정리한다.

worker는 사용자 지시대로 빌드·Gradle 테스트·Minecraft/Vision을 실행하지 않았다. Minecraft 26.3 캐시 JAR의 javap, 정확 Fantasy 소스와 Fabric API 시그니처 대조만 수행했다. **컴파일 성공이나 live 성공으로 간주하지 않는다.** master의 중앙 compile 및 JUnit/GameTest 실행이 필요하다.

실제 첫 접속·기존 타 월드 로그인 유지·respawn·void 귀환·Creative 관리자 override·능력/카메라 진행 중 전송·실제 바닐라 클라이언트 화면/리소스팩·종료 후 persistent reopen·청크/관리자 편집 디스크 보존·무음/몹 부재는 live 미검증이다. 특히 restart 디스크 보존은 단일 프로세스 open 재사용 테스트와 구분해야 한다. 최종 geometry의 정확 스폰은 master가 PNG/인게임으로 확인한다.

## Master 통합과 지형 산출물

사용자 SSD의 `Tower-Courtyard-Assets-2026-10-28/maps/tower_courtyard.textured.glb`를 별도 headless Blender 장면으로 직접 가져와 조감·중앙광장을 확인했다. live Blender와 SSD 원본은 변경하지 않았다. GLB Y-up crop `[-85,-48,-125]`~`[110,70,45]`, scale2, offset `[0,40,0]`을 적용했다. 사용자도 이 크기를 승인했다.

배치16,436개 중13,776개가 crop과 교차했다. 11,266,738개 삼각형 표면에서 1,151,116블록을 생성했다. 바닐라 팔레트18개, 실제 bounds는 `[-170,-56,-250]`~`[219,136,58]`이다. 압축 바이너리는2,938,201바이트, Sponge schematic은285,426바이트다. 원경 전체, 격납고·시장·별관은 포함하지 않는다. `exports/tower-w232/`에 schematic·최종manifest·provenance·실제Vision미리보기를 둔다.

변환은 인스턴스 계층과 원본 루트축변환을 한 번 적용한다. 작은삼각형 단축 경로와 배치 단위 dominant-axis/triangle-box 피복으로 큰바닥의 구멍을 방지한다. 재질별 median색을 바닐라 블록에 대응시켜 미세 색상 노이즈를 억제한다. 천막 아래나 아치 전체를 기둥으로 채우지 않는다. 원작 dye/shader/PBR, navmesh, NPC·동적 장식은 복원하지 않는다.

첫 충돌안전 후보는 실제PNG에서 외벽 안쪽 빈 공간으로 확인되어 거부했다. 노천 최상부 표면을 고르는 검사와 회귀 fixture를 추가하고, `70.5,75,-19.5` yaw150을 최종스폰으로 확정했다. 재변환 설정은 `scripts/tower/courtyard-config.json`에 기록한다. 런타임의 충돌검사도 계속 적용하며 이미 저장된 관리자의 편집은 자동으로 수리하지 않는다.

최종 assemble과 nestedFantasy·binary/manifest일치를 확인했다. Python변환/노천스폰검사16/16, JUnit디코더3/3, 최종 좌표의 수동GameTest3/3이 통과했다. 정확FAPI 소스상 headless는manualOnly를 제외하므로 일반 격리dev서버+GameTest classpath에서 정확/test run명령을 순차 실행했다.

Vision R2에서는 최종스폰·onGround·selfcamera, native40틱 보행8.6306블록과 서버Pos, 다른차원에서/tower귀환, y=-62낙사fixture에서health20귀환을 확인했다. 실제PNG를 열어 검수했으며 촬영용 HUD숨김은 복원했다. 입력lease/native키를 중립으로 해제했다. 이 기록은 실제OS키보드 입력이나 소리청취·장기성능 인증을 뜻하지 않는다.

전체 JUnit은2079개 중2069통과/10실패였다. W231에서도 있던6실패와 별도로 과거/tmp plugsets원본 누락으로4개가 실패했다. W232는 해당 pin·consumer를 변경하지 않았고 관련3개는통과했다. 전체gate성공으로 표시하지 않는다. 상세한 실패·비교·근거는 `docs/qa/2026-10-29/w232/`에 있다.

R3 새 JVM에서 동일 저장 폴더를 다시 열고, 저장한 시험용 gold_block이 유지되는 것을 확인했다. 시험 블록을 원본 smooth_stone으로 복원·저장한 뒤 임시 forceload ticket을 해제했다. 서버와 Vision 클라이언트 모두 종료했으며8102/25611/25565포트가 닫혀 있고 Java프로세스가 남지 않았음을 확인했다. 사용자 요청의48시간 잠자기 방지는 유지했다. `persistence-final.json`, `cleanup.json`에 근거를 보관한다.

## W245 머테리얼 전달본 적용 (2026-10-29)

`Destiny-Tower-Materials-2026-10-29`의 DDS/HLSL/cbuffer를 이용해 24개 shader·98개 머테리얼의 정적 basecolor를 합성했다. 원본 GLB를 별도 Blender에서 전후 비교한 뒤, 기존 노출면의 색을 바닐라 블록 팔레트에 대응했다. 새 클라이언트용 대형 텍스처·모델은 추가하지 않는다. 원본 지형·크기·동선·중앙 나무와 기존 소품은 유지한다.

Charm STATIC export의 UV에는 scale/translation이 이미 적용되어 있어 PS UV는 `(U,1-V)`로 변환한다. 중복 scale/offset 적용을 피했다. TEXCOORD8 vertex buffer와 원본 조명·일부 engine 입력은 없어 대표값 근사이며 원작 색 완전 복원은 아니다.

서버는 W243 재질 pass 완료 후 별도 W245 ledger로 96,577개 후보를 128 operations/tick 상한으로 적용한다. 실제 블록이 expected와 일치할 때만 바꾸므로 저장된 사용자 편집은 보존한다. 최종 QA에서는 96,550변경/27보호 skip을 확인했다. 자세한 근거와 Blender·Danmo 비교는 [W245 검수 기록](../qa/2026-10-29/w245/README.md)에 있다.
