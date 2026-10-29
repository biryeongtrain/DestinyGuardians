# abilities / 탄도 / VFX 반환

소유 20개 파일만 수정. main·공통 TestPlayers·제품 파일은 수정하지 않았다. 기준은 원본 manifest의 현재 제품 복사본이며 HEAD diff가 아니다.

- W77/W78/W79/W80/W90/W43/W81/W82: AE100을 해당 무기 stack에 명시하고 실제 ADS 토글 및 서버 틱으로 완전 조준을 획득한 뒤 발사한다. 발사 직전 progress=1, cone=0을 검사한다. 기존 HP·탄약·범위·차폐·취소 assertions는 유지한다. 공통 onGround나 RNG를 대체하지 않는다.
- W105/W95: hip spread를 유지하고 고정 RNG 입력 두 개를 독립 disk 수학으로 해석한다. 실제 발사에는 같은 seed를 복원한다. W95가 예상 ray 계산 중 실제 발사 RNG를 먼저 소비하던 오류를 제거했다. W104/W105 ADS는 crouch 대신 현행 좌클릭 toggle API를 사용한다.
- Combat.isEnemy가 이미 ally/tamed를 제외하므로 오래된 positive precondition을 현행 분류에 맞췄다. 실제 world query 후보·적 피해·아군 무피해 검증은 유지한다.
- Hunter: 등록 grenade ID, grenade contact T+6 / melee T+4, GrenadeThrow 별도 소유 타임라인, HUNTER_HIGH vy=.62, 서로 다른 서버 틱의 triple jump 입력을 반영한다. Shadowshot은 native physics가 lift를 적용한 T+3에 실제 air-jump 입력을 준다.
- AbilityVisual: 현재 GrenadeModels의 Arc/Solar 공유 prop 및 Void prop 경로를 명시하고 정확한 4개 고유 모델과 clone independence를 검사한다.
- W43 damage-number: 같은 레벨 alive respawn에서 동일 UUID의 다른 객체 소유권 보존을 확인한다. death respawn도 추가 실행하여 old holder 제거와 타 owner 보존을 확인하고, 실제 타워 level transfer가 있다면 replacement의 이전 레벨 holder·watcher 제거까지 확인한다.
- H20: BetterModel 내부 globalState cache 대신 EquipmentDisplaySamples가 기록한 실제 DisplayTransformer position/scale/rotation을 관측한다. staff support에 display scale도 적용한다. gap .025, attack >60°, deploy >90°, ready endpoint .001 기준은 변경하지 않았다. 이 3개는 runtime 재검증 필요이며 통과를 주장하지 않는다.

## Profile HUD 준비 경로와 한계

ClassAbilityW255 및 AbilityW252 HUD 시나리오는 실제 profile graph가 게시된 뒤 시작한다. autohost 모드/프로필 view 활성 조건이 없으면 즉시 실패한다. 임의 graph 주입이나 테스트 내부 팩 빌드는 없다.

확인한 headless 경로: DestinyGuardians.onInitialize → StartupPackCoordinator.init → SERVER_STARTED에서 BetterModel 성공 관측 → AutoHost.startResourcePackGeneration → WeaponPackOptimizer.compact → ProfileArmAssets.compact → poses/graphs volatile map 게시. ProfileWeaponView.tick은 그 graph가 없으면 HUD를 제거한다.

aborted-broad-gametest.log 123행 startup deferred, 133~134행 04:30:45 generation released/start 기록으로 headless 경로 진입을 확인했다. 2855~2884행 ProfileArmAssets.compact의 heap OOM이 있었고 완료 게시 로그는 없었다. master가 setup_early=true 및 autohost enabled도 확인했다. 최신 W257 생성 약21초와 가속 GameTest 틱의 관계 때문에 maxTicks=1200은 실제 실행 확인이 필요하다. 시간 초과 시 master 공유 readiness gate 검토 대상이며 timeout 증가만으로 해결됐다고 보고하지 않는다.

## 검증과 중앙 실행 요청

20개 Java tree-sitter 문법 파싱 통과. 기존 GameTest 이름과 개수를 전부 보존했다. main 소유파일 20개 해시가 최초 baseline와 일치한다. patch는 main-baseline 기준이다. 컴파일·JUnit·GameTest·Vision은 worker에서 실행하지 않았다.

master 중앙 compile 후 소유 클래스 targeted GameTest를 실행해야 한다. 특히 H20 실제 전송 pose 3개, HUD graph 준비/복원 4개, ADS 준비 이후 정확 hit 및 W105/W95 seeded oracle를 확인해야 한다. H20 기준을 계속 위반하면 제품의 source grid / 전달 pose / 설치 모델 일치 여부를 조사해야 한다. 제품 수정은 하지 않았다.
