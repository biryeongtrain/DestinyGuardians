# Destiny Guardians

최신 [W114 용광로·망치머리 재장전](docs/design/128_무기별_재장전_용광로와_망치머리.md): **독립 Git worktree2개**에서 원본 모델 부품·게임플레이 기반 모션과 회귀를 병렬 구현했습니다. 중앙 **913JUnit/947GameTest 통과**, 통합 Vision에서 두 무기·두 파지의 빈 탄창 재장전4개와 용광로 장전 후 발사를 확인했습니다. 실제192PNG를 보존했고 최초 파지변경 직후 사격 실패1개는 미확정으로 남겼습니다. **Q 수동장전·왼손/3인칭·청취·전체 원작 fidelity는 후속**입니다. [화면·근거·한계](docs/qa/2026-10-25/w114/README.md).

이전 [W110 근접 연계 특성](docs/design/125_근접_연계_무기_특성.md): **독립 Git worktree2개**에서 무뢰한/묘지 도굴꾼 제품·테스트를 병렬 구현하고 master가 통합했습니다. **874JUnit/915GameTest 통과**. 취합 Vision에서 실제 x1/x5 HUD, 비치명적 강화근접의 특수탄1/2→3/0, Primary 탄창보충·버프만료를 확인했습니다. [실제화면·실패·한계](docs/qa/2026-10-25/w110/README.md). 전체 무기 목표는 진행 중입니다.

데스티니 가디언즈의 직업·무기·레이드를 마인크래프트 야생에 옮기는 **Minecraft 26.3 / Fabric 서버사이드 모드**입니다. 플레이어는 바닐라 클라이언트로 접속하고, 커스텀 외형은 Polymer 서버 리소스팩으로 받습니다.

최근 [W109 다중 대상 피해 특성](docs/design/124_다중_대상_피해_특성.md): **제품 기능2개를 독립 Git worktree에서 병렬 구현**했습니다. 모두를 위한 하나(35%/10초)·포위(15m/40%, 검35%)를 각8개의 정확 소켓·유료 검·파동·HUD에 연결했습니다. 최종 강제 **832JUnit/900GameTest** 통과. 취합 Vision 세션에서 두 버프의 실제 활성/만료 HUD를 확인했습니다. [기록·화면·한계](docs/qa/2026-10-25/w109/README.md). 전체 무기·기존 입력/탄약 이상·다인성능·청취 완료는 아닙니다.

이전 [W108 먹이 쟁탈전](docs/design/123_먹이_쟁탈전_특성.md): 정확13무기의 실제 처치→최대5중첩·장전가속·실제 HUD를 구현했습니다. **783JUnit/884GameTest 강제2회**, worktree 운영27tests 통과. Vision에서 실제5처치 x5/타이머·빠른 장전/만료·미선택 대조를 확인했습니다. **Git worktree3개 병렬 작업**으로 전환했고 [반환/통합 규칙](docs/qa/WORKTREE_BATCH.md)을 남겼습니다. [실제 화면·실패·한계](docs/qa/2026-10-25/w108/README.md). 전체 무기·다인성능·실청취 완료는 아닙니다.

이전 [W107 native 송수신·탄약 동시 진단](docs/design/122_무기_native_송수신과_탄약_동시_진단.md): 기본 꺼짐·4096행 한도의 읽기 전용 관측기를 서버/Vision에 추가했습니다. **869 GameTest/760 JUnit 강제2회**, Vision **52 JUnit/31 Node** 통과. 실제 **7sequence/15PNG**에서 같은 stack 빈장전 후 재발사(native0→41→40, two-hand0→41→37)를 제한 확인했습니다. **W106의41→39·후속 발사 이상 원인은 여전히 미확정**이며 이번 계측 실험의 성공으로 이전 실패를 지우지 않습니다. [QA·로그·화면](docs/qa/2026-10-25/w107/README.md). 앞으로도 QA 중 [잠자기방지 wrapper](docs/qa/KEEP_AWAKE.md)를 필수 사용하고 종료 시 해제하며, 보안 잠금/인증은 변경하지 않습니다.

이전 [W106 실제 준비 진단·reticle particle 보강](docs/design/121_실제_무기_준비_진단과_HUD_리소스_보강.md): **869 GameTest/754 JUnit 강제2회**·독립감사 통과. 실제 **128PNG**에서 준비 전 거절·양파지 빈장전0→41·샷건4조준선/경고해소를 제한 확인했습니다. 당시 **준비 후 single-fire는 기대40 대신39로 실패했고 원인/장전 후 fresh-fire는 미확정·미수락**이었습니다. [불변의 당시 QA·실패·화면](docs/qa/2026-10-25/w106/README.md).

이전 [W105 샷건 프레임별 고정 산탄·조준선](docs/design/120_샷건_프레임별_산탄과_조준선.md): 역사적 S19의4패턴을 실제12ray/HUD에 연결했습니다. **865 GameTest/750 JUnit 강제2회**, 실제 **192PNG**에서 샷건5정·두파지 탄창분리·로켓잠금/정지표적 피해를 제한 수락했습니다. **장전 후 단발 사격 기대불일치·실청취·다인성능은 남습니다.** [QA·화면·실패/한계](docs/qa/2026-10-25/w105/README.md). 향후 인게임QA는 [잠자기방지 wrapper](docs/qa/KEEP_AWAKE.md)를 필수 사용하며 암호·인증은 변경하지 않습니다.

이전 [W96 위험 체력 HUD 연속 alpha](docs/design/111_위험_체력_HUD_연속_alpha.md): 기존 모델·시계를 유지하고 critical HUD에만 선택적으로 셰이더 cutout을 우회해 딱딱한 타원 경계를 부드럽게 했습니다. **818 GameTest/699 JUnit 강제2회**, 실제 **1708×960/854×480·113PNG**, 팩·두 캐시 감사 통과. **당시 W96-N1은 미해결이었으나 W99의 layer6→0 수정으로 수락된 범위에서 해결했습니다. 전체 HUD 완성을 뜻하지는 않습니다.** [QA·화면·한계](docs/qa/2026-10-25/w96/README.md).

이전 [W93 기존 장전·조준·활 전송](docs/design/109_기존_무기_표현의_inventory_전송.md): legacy 모델의 실제 inventory/direct-use 패킷 경계와 소유권·지연 정리·첫 frame diff를 보강했습니다. **809 GameTest/681 JUnit 최종 강제2회**, 실제 Vision **135PNG·원본25개 직접검사**, 6무기 장전/ADS/당김·10sequence 중립·팩/캐시 감사 통과. **활 nock 중 상단 피부색 사각형 W93-N1은 미해결**로 보존했으며 전체 시각 완료는 아닙니다. [QA·실제 화면·한계](docs/qa/2026-10-25/w93/README.md).

이전 [W92 inventory wire 모델 투영](docs/design/108_inventory_wire_모델_투영.md): W91 신규 장전·교체 모델이 packet 복사에서 소실되던 경계를 원본 권한을 유지한 채 수정했습니다. **799 GameTest/681 JUnit 최종 강제2회**, source/JAR/팩/실제 캐시 감사와 Vision **46PNG·원본15개 직접검사**로 이자나기 탄창 장전·강화 총신/ADS·양방향 수납/꺼내기를 확인했습니다. 첫 SDL 시작 실패와 gate1/2 실패는 보존했습니다. **W91 대상만 수락했으며 기존 다른 모델 경계·원작 손 IK·청취·전체 무기 완료는 후속**입니다. [QA·실제 화면·한계](docs/qa/2026-10-25/w92/README.md).

이전 [W91 이자나기 장전·무기 교체 모션 후보](docs/design/107_이자나기_장전과_교체_모션.md): 총괄→L1리드→asset자식으로 병렬 구현·리뷰했습니다. **791 GameTest/681 JUnit 최종 강제2회** 통과했으나, 취합 Vision에서 서버 상태와 실제 모델 표시가 다른 결함을 발견해 **시각 완료 처리하지 않았습니다**. 실제 packet snapshot 경로가 다음 우선순위입니다. [원본 화면·실패·한계](docs/qa/2026-10-25/w91/README.md).

이전 [W90 계층형 위임·테스트 종료 정리·스폰 격리](docs/design/106_테스트_종료_정리와_스폰_격리.md): 총괄→분야 리드→구현/시험 child 구조와 단일 통합 Vision 운영을 문서화했습니다. timeout 예약이던139정리를 실제종료에 연결하고 격리환경을 통합했습니다. **773 GameTest/668 JUnit 최종 강제2회**, 제품 JAR/팩은 W89와 동일합니다. HUD softness는 오프라인 후보이며 새 Vision 수락은 아직 없습니다. [QA·작업 큐·한계](docs/qa/2026-10-25/w90/README.md).

이전 [W89 위험 체력 주변부 가시성](docs/design/104_위험_체력_주변부_가시성.md): 활성 pulse가 shader cutoff로 사라지지 않도록 새 그래픽 bank를 추가했습니다. **759 GameTest/668 JUnit 최종 강제2회**, Vision HP6/5/1 실제48PNG와 회복 제거를 확인했습니다. **당시 타원 경계의 부드러움과 fixture 정리/스폰 격리는 후속이었고, 정리/격리는 W90에서 별도 수리했습니다. 경계 부드러움은 남습니다.** [실제 화면·검증·한계](docs/qa/2026-10-25/w89/README.md).

이전 [W88 Vision 실화면·피격 방향 보정](docs/design/103_Vision_실화면_재개와_피격_방향_보정.md): 실제 화면에서 발견한 좌우 반전을 수정했습니다. **755 GameTest/662 JUnit 전체 강제2회**, 수정 전후 각각 Ace5·Salvo2 native 시나리오와 방향4개 PNG를 확인했습니다. **위험 체력 주변부 가시성은 별도 결함으로 남아 있습니다.** [실제 화면·검증·한계](docs/qa/2026-10-25/w88/README.md).

이전 [W76 HUD 정리·보조 손 가독성](docs/design/91_W76_바닐라_HUD_정리_조사.md): 허기·핫바 프레임·XP바/레벨을 전용sprite14개와143locale overlay로 숨겼습니다. offhand가 능력·탄약 패널을 가리면 left HUD만 손 위에 표시합니다. **615 GameTest/559 JUnit 최종 강제2회 통과**, Vision English/Korean 실제 화면·상자 아이콘/수량·입력중립을 확인했습니다. **핫바 아이템·숫자와 tutorial toast는 아직 남습니다.** [QA·실제 화면·한계](docs/qa/2026-10-24/w76/README.md).

이전 [W75 ADS 지상 이동](docs/design/90_W75_ADS_지상_이동.md): 일반0.75·보조무기0.85·정밀HC0.775 상대 배율을 native attribute pair에 연결했습니다. 지상 대각선 포화를 피하고 조준 해제/스킬/수납 때 자기 modifier만 복구합니다. **공중 ADS 배율·원작 절대속도는 미구현**, Vision 실게임 대표7시나리오에서 이동·수납 복구와 HUD 화면을 확인했습니다. client FOV-effect 설정별 합성·전체 무기 실검증은 남습니다. **612 GameTest/551 JUnit, 최종 강제2회 통과.** [QA·실제 화면·출처](docs/qa/2026-10-24/w75/README.md).

이전 [W74 활 최적 발사창 HUD](docs/design/89_W74_활_최적_발사창_HUD.md): 일반활2종의 실제 승인 당김에 맞춰 조준선이 좁아지고 최적 구간/기한 경과를 표시합니다. 창9/14틱은 고정 커뮤니티 계산식과 공식 기본 안정성 기반이며, **피로 강제발사·기한 뒤 피해/정확도 감소는 아직 미구현**입니다. [QA·출처·경계](docs/qa/2026-10-24/w74/README.md).

최근 [W73 활 정밀 적중 가속](docs/design/88_W73_활_정밀_적중_가속.md): 선정 Whispering Slab의 공식 소켓으로 Archer’s Tempo를 선택하면 실제 정밀 적중 후 다음 당김이12→9틱으로 줄고, HUD에3초 버프가 표시됩니다. 실제 수납/동일틱 offhand 복귀·취소·소유권을 검증했습니다. [QA·출처·미구현](docs/qa/2026-10-24/w73/README.md).
W73 당시 최적 발사창/피로는 미구현이었으며, W74에서 정보성 창만 추가했습니다. 피로 강제발사·late 피해 감소는 여전히 없고, 도중 발동·만료 snapshot은 프로젝트 정책입니다. 새 실게임 클라이언트 검증 없이 서버 회귀 테스트를 사용했습니다.

이전 [W72 3인칭 장비 매핑](docs/design/87_W72_3인칭_장비_매핑.md): BetterModel의 장비 갱신이 활·지팡이를 실제 손 아이템으로 덮어쓰는 경로를 재현하고, native display 기록 시점의 소유권으로 방지했습니다.
**570 GameTest /526 JUnit**, 최종 동일 JAR 전체 강제 빌드2회 통과. 늦게 도착한 갱신·해제 후 옛 prop·양손 교체·외부 tracker 비인수를 검사했습니다.
모델/텍스처/사운드/탄약은 보존했고 리소스팩은 W71과 동일합니다. [QA·재현·한계](docs/qa/2026-10-24/w72/README.md).
기존 W71의 한 번뿐인 실패 당시 정확한 비동기 순서를 알아낸 것은 아닙니다. 실게임 픽셀/입력·청취·성능 검증과 전체 목표는 진행 중입니다.

이전 [W71 Long Arm 반복 재장전](docs/design/86_W71_Long_Arm_반복_재장전.md): 총 올림→기울어진 자세에서 반복 삽입→복귀의 몸체 모션을 실제 2발씩 장전에 연결했습니다.
**564 GameTest /526 JUnit**, 최종 동일 JAR 전체 강제 빌드2회 통과. 원래256큐브·탄약·장전 시간·소리는 보존하며 복귀 모션이 사격을 늦추지 않습니다.
[단계 미리보기](docs/qa/2026-10-24/w71/long-arm-phases-contact.jpg) · [출처/한계](art/weapons/w71/reference-notes.md) · [QA](docs/qa/2026-10-24/w71/README.md).
손·카트리지·레버 동작은 아직 없고, 미리보기는 Blockbench 렌더입니다. 첫 실행의 기존 공허 활 테스트1회 실패는 이후 재현되지 않았으나 원인 미확정으로 기록했습니다. 실게임 화면/입력·청취·성능 검증과 전체 목표는 진행 중입니다.

이전 [W70 원거리 ADS 전환](docs/design/85_W70_원거리_ADS_전환.md): 원거리57종의HIP→ADS를 실제 조준 진행도에 따른 **21샘플**로 연결했습니다.
활의시위/화살동작은독립축으로유지하고저격스코프·LFR·기존3인칭파지/탄약/소리는보존했습니다.
**555 GameTest /518 JUnit**, 최종동일JAR전체강제빌드2회통과.
[단계 미리보기](docs/qa/2026-10-24/w70/ads-transition-contact.jpg) · [출처/한계](art/weapons/w70/reference-notes.md) · [QA](docs/qa/2026-10-24/w70/README.md).
Blockbench렌더는실게임화면이아닙니다. render-frame연속보간/손IK가아니며실게임시야·팩bake메모리/FPS·입력/청취는미검증입니다. 전체목표는진행중입니다.

이전 [W69 Ammit AR2 개별 재장전](docs/design/84_W69_Ammit_AR2_재장전.md): 총 올림→하부 탄창 당김/삽입→체결/복귀를 실제 재장전 phase에 연결했습니다.
원본 정적 메시와 플레이 영상을 대조한 **작성 모션**이며, 원작 애니메이션 rip/손 IK는 아닙니다. 원형 액체 창은 고정하고 **199큐브·기본 texture를 보존**했습니다.
**546 GameTest /510 JUnit**, 최종 동일 JAR 강제 빌드2회 통과. 기존 탄약·41tick 장전·소리·HUD 정책은 그대로입니다.
[모션 단계 미리보기](docs/qa/2026-10-24/w69/blockbench-pose-contact.jpg) · [출처와 차이](art/weapons/w69/reference-notes.md) · [QA](docs/qa/2026-10-24/w69/README.md).
Blockbench 렌더는 실제 게임 화면이 아니며 실게임 시야/손/소리 검증은 남아 있습니다. 개별 장전은 현재 Beloved·Duke·Ammit 3종, 전체 목표는 진행 중입니다.

이전 [W68 스냅샷 조준경·ADS](docs/design/83_W68_스냅샷_조준경과_ADS.md): 실제 소유 무기의 정확한 base 소켓에 조준 진입 가속을 연결했습니다.
**540 GameTest /502 JUnit**, 동일 JAR 전체 강제 빌드2회 통과.
`/destiny perk select snapshot_sights` · [QA](docs/qa/2026-10-24/w68/README.md). 모델 selector·조준경 HUD·FOV가 같은 실제 조준 진행도를 사용합니다.
Primary0.5/Special0.8은 커뮤니티 측정 채택 정책이며 역사 공식Special0.75와의 차이는 미해결입니다. Heavy2종은 공식 소켓이 있어도 배율 근거가 없어 제외합니다.
기존 이탈 시간·탄약·Handling·모델/음원은 보존했습니다. 추가 client 기동·일반QA배포는 하지 않았고 실게임 화면/입력/청취·전체 목표는 계속 진행 중입니다.

이전 [W67 정밀 타격 탄약 반환](docs/design/82_W67_정밀_타격_탄약_반환.md): 공식8무기9소켓의 Triple Tap/FTTC를 실제 정밀 피해에 연결했습니다.
연속 정밀3/4회당 탄창1/2발 생성, 각 타격 사이40tick 제한. 예비탄을 소비하지 않으며 기본 탄창 용량·실제 발사 비용을 지킵니다.
Aisha의 두 특성이 독립 집계되고 기존 탄약 HUD에 실제 반환이 나타납니다. Kill Clip용 재장전으로 취급하지 않습니다.
`/destiny perk select triple_tap` · `fourth_times_the_charm` · [QA](docs/qa/2026-10-24/w67/README.md).
모델/음원/client asset은 보존했습니다. 원작 reset 세부 규칙·실게임 화면/입력/청취·전체 무기 시스템 목표는 계속 진행 중입니다.

이전 [W66 광란 스택·HUD](docs/design/81_W66_광란_스택과_HUD.md): 공식 base 소켓이 확인된21종에 선택형 광란을 연결했습니다.
실제 무기 처치로 x1/x2/x3, 피해1.10/1.21/1.331배,90tick마다 한 스택 감소. 수납 중 시간과 발사체 원본 귀속을 보존합니다.
HUD는 현재 무기의 스택과 다음 감소까지의 시간을 표시합니다. 기본 자동 부여·무기/탄약 지급은 없습니다.
`/destiny perk select rampage` · [검증 결과](docs/qa/2026-10-24/w66/README.md) · [오프라인 HUD 미리보기](art/hud/w66-rampage/offline-preview.png).
실게임 화면/입력/청취 검증은 남아 있으며 추가 Vision/일반 QA 기동·배포는 하지 않았습니다. 전체 무기 시스템 목표는 계속 진행 중입니다.

이전 [W65 장전 보충·복귀 분리](docs/design/80_W65_장전_보충과_복귀.md): **512 GameTest /465 JUnit**, 동일 JAR 전체 강제 빌드2회 통과.
명시 자료가 있는 핸드캐논3종·기관총3종은 탄약이 먼저 보충되고 장전 바·소리·모션은 기존 완료 시점까지 이어집니다.
Duke 기본42/59tick·Outlaw24/33tick(보충/전체). 실제 예비탄 지불·보충 뒤 취소 보존·중복 방지·Kill Clip 시간 감소를 검증했습니다.
비율 없는57종은 추정하지 않았습니다. 원작 정확한 조기 발사·취소 입력·개별 모션·손/IK·실게임 화면/청취 검증은 남습니다.
[출처와 적용 정책](art/weapons/w65/reference-notes.md) · [QA](docs/qa/2026-10-24/w65/README.md). 추가 Vision/일반 QA 기동·배포 없음. 전체 목표는 진행 중입니다.

이전 [W64 Duke 실린더 재장전](docs/design/79_W64_Duke_실린더_재장전.md): **503 GameTest /455 JUnit**, 동일 JAR 전체 강제 빌드2회 통과.
Duke에 총구 올림→왼쪽 실린더 열림→장전 대기→닫기/복귀를 실제 phase로 연결했습니다.
원래232큐브/UV를 보존하고 요크2개 추가, 총234큐브입니다. Beloved W47·기존 탄약/HUD/황금총 방향·음원은 유지했습니다.
[Blockbench 모델 단계](docs/qa/2026-10-24/w64/blockbench-pose-contact.jpg) · [원작 프레임/차이](art/weapons/w64/reference-notes.md) · [QA](docs/qa/2026-10-24/w64/README.md).
Blockbench 렌더는 실게임 화면이 아닙니다. W64 당시 보충 뒤 복귀 tail은 미구현이었고 W65에서 자료 있는6종에 분리했습니다. 손/IK·다른 무기 장전·실게임 재검증은 아직 남습니다.
W64 당시 개별 장전은 Beloved와 Duke 두 종류였고, W69에서 Ammit를 추가했습니다. 전체 목표는 진행 중입니다.

이전 [W63 재장전 음향 시간·취소](docs/design/78_W63_재장전_음향_시간과_취소.md): **496 GameTest /446 JUnit**, 동일 JAR2회 통과.
50기본 full-magazine+11무법자 가속의61행을53개 pitch보존 파생 Ogg에 연결했습니다.
실제 캡처 장전 시간에 맞추고, 고유 client-only source entity로 수납·스킬·완료 시 해당 소리만 끊습니다.
동일 event로 장전 중인 다른 플레이어는 유지하며 event-global StopSound를 사용하지 않습니다.
기존99음향정의/112Ogg·황금총방향/탄창·예비탄HUD·모델/탄약계산은보존했습니다. 자료에없는bow장전음은계속무음입니다.
[음원 비교](docs/qa/2026-10-24/w63/audio/audition.html) · [출처·팩·초기 fixture 실패·검증 경계](docs/qa/2026-10-24/w63/README.md).
자료의family대표음원을모든총의정확한원작음원으로표현하지않습니다. W63당시 개별장전모션은Beloved만이었으며 원작clip/손·IK/음향endpoint·실게임HUD/audio는남습니다.
`/destiny perk select outlaw` · `kill_clip` · `auto_loading_holster` · `/destiny perk list|status|clear`.
동일소켓배타·다른소켓공존,기본부여/무기·탄약생성없음.전체무기시스템목표는진행중입니다.
이전 [W62 무법자/승인된 로딩 화면 진단](docs/qa/2026-10-24/w62/README.md) · [W61 살상 탄창](docs/qa/2026-10-24/w61/README.md) · [W60 자동 장전 총집](docs/qa/2026-10-24/w60/README.md) · [W59 사격 회복](docs/qa/2026-10-24/w59/README.md) · [W58 Handling](docs/qa/2026-10-24/w58/README.md) · [W56 검 사운드 미리듣기](docs/qa/2026-10-24/w56/audio/audition.html).

## 구성

| 의존성 | 버전 | 역할 |
|---|---|---|
| Fabric Loader / API | 0.20.1 / 0.164.0+26.3 | |
| Polymer | 0.18.4+26.3 | 서버사이드 아이템·엔티티, 리소스팩 생성·호스팅 |
| BetterModel | 3.5.1 | 플레이어 limb·적·보스 모델과 애니메이션 |
| minigame-lib | 2.0.0+26.3 (`libs/minigame-lib` submodule) | DisplayHud, ShaderFX, FOV, 시네마틱, 음악 |
| Java | 25 | |

## 시작하기

```sh
git clone --recurse-submodules <repo-url>
# 이미 받은 경우
git submodule update --init --recursive

./gradlew build        # build/libs/destiny-guardians-*.jar
./gradlew runServer    # run/server. 첫 실행 시 run/server/eula.txt 에 eula=true 필요
./gradlew runClient    # 개발 클라이언트 (싱글플레이 테스트)
```

minigame-lib은 Maven 저장소 대신 submodule 소스를 `includeBuild`로 직접 빌드합니다. 새 버전을 쓰려면:

```sh
cd libs/minigame-lib && git fetch && git checkout <tag> && cd ../..
git add libs/minigame-lib && git commit -m "chore: bump minigame-lib to <tag>"
```

## 서버에 설치

`build/libs/destiny-guardians-<버전>.jar`와 함께 다음 모드를 서버에 넣습니다: Fabric API, Polymer(core·resource-pack·virtual-entity·autohost), BetterModel(+ Fabric Language Kotlin), minigame-lib.

## 헌터 시작하기

서버에서 리소스팩 수락 후 실행합니다. 아래 명령은 본인 대상으로 쓸 수 있고,
OP는 마지막에 플레이어 이름을 붙일 수 있습니다.

```text
/guardian class hunter
/guardian subclass arc          # solar / void 도 선택 가능
/guardian info
```

| 동작 | 바닐라 입력 | GCB-mod 선택 설치 시 |
|---|---|---|
| 공중 점프 | 공중에서 Space 다시 누르기 | 동일 |
| 회피 | Shift 두 번 (7틱 이내) | C |
| 수류탄 | F | Z |
| 근접 능력 | Shift + 좌클릭 | V |
| 궁극기 | Shift + F (게이지 100%) | X |
| 궁극기 공격 | 좌클릭 | 좌클릭 |

헌터는 F 손 교환을 능력 입력으로 사용합니다. `/guardian class none`으로 해제하면 바닐라 동작이 유지됩니다.
일반 총기·탄약·HUD는 아래 W33 이후에 구현했습니다. 명사수 회피는 W57에서 전체 장착 무기 재장전·주변 개인 탄약 수집과 연동했습니다.
수류탄3종·태양 단검·공허 연막탄은 Blockbench 소품으로 표시합니다.
H12에서 칼·섬광탄을 실제 Destiny 시각 자료에 맞춰 재제작했습니다. 소이·소용돌이·연막은 원작 외형 미확인 잠정 모델입니다.
[능력 모델·레퍼런스](docs/design/14_헌터_능력_모델.md) · [편집 원본](art/blockbench/hunter/)

H13 기반/H14 디테일 개정: 수류탄·근접6종에 **BetterModel 애니메이션 VFX4종**을 연결했습니다. Arc 분기 전격·겹친 곡선 화염·Void 나선/필라멘트·텍스처 연무로 표시합니다.
32→128 아틀라스, Arc/Solar/Vortex 메시720~1024삼각형+19~45카드, 연막30빌보드 카드, 렌더본4~8개를 사용합니다.
[시각 레퍼런스](docs/design/15_헌터_VFX_레퍼런스.md) · [구현·한계](docs/design/16_헌터_VFX_구현.md) · [H14 디테일·비용](docs/design/17_헌터_VFX_디테일_개정.md) · [VFX 원본](art/blockbench/vfx/)
연막과 근접 파생 효과는 잠정 해석입니다. H15에서는 궁극기 전용 장비4종, BetterModel 버스트·닻,
Polymer 화염 궤적·움직이는 공허 연결선과 화면 펄스를 추가했습니다.
방향별 회피와 궁극기 준비/공격/회복 클립도 연결했습니다.
[고도화 로드맵](docs/design/18_헌터_고도화_로드맵.md) · [장비](docs/design/20_헌터_궁극기_장비.md) · [궁극기 VFX](docs/design/22_궁극기_VFX_구현.md)

BetterModel 기본 리그에서 `config/bettermodel/players/guardian_hunter_h15.bbmodel`을 최초 생성하며,
기존 파일은 덮어쓰지 않습니다. 방향별 `h15_roll_*`, 속성별 `h15_super_*`·`h15_super_*_attack` 및
아이템 bone 계약은 [애니메이션 명세](docs/design/19_헌터_애니메이션_개정.md)를 따릅니다.
구형 `guardian_hunter`와 기본 리그는 폴백입니다. 오프라인 QA 계정은 limb 재생 중 기본 템플릿 색으로
바뀌는 현상이 남으며, 인증 계정 개인 스킨은 미검증입니다.
바닐라는 본인 limb를 숨기며, GCB 시점 이벤트가 있어야 본인 3인칭 표시를 구분합니다.

GCB 어댑터는 빌드 시 `gcb_server_dir`(기본 `../GCB-server`) 소스가 있어야 포함됩니다.
없어도 바닐라 입력 빌드는 가능하지만, 그 JAR에 GCB-server만 나중에 추가해도 어댑터가 생기지는 않습니다.
빌드 의존성 모드들은 JAR에 내장되지 않으므로 서버에 별도 설치해야 합니다.

## 일반 무기 모델 프리뷰 — W32

저격총·산탄총·융합소총·활·검·글레이브 등을 포함한 **18개 분류 / 전통 프레임 대표 63종**을 추가했습니다.
W30 초판은 공유 원본의 3D 볼륨을 51~128개 큐브로 재구성하고 원본 diffuse 표면을 베이크했습니다.
기준 `Ace.bbmodel`(87큐브) / `izanagi.bbmodel`(79큐브)의 규모를 참조한 편집 가능한 `.bbmodel`입니다.
최신 모든 프레임·경이 고유 프레임의 완전 목록은 아니며, PBR 셰이더와 곡면은 원작 그대로가 아닙니다.

리소스팩 수락 후 OP가 주 손을 비우고:

```text
/destiny weapon list sniper_rifle
/destiny weapon equip beloved
/destiny weapon pose ads
/destiny weapon pose inspect
/destiny weapon pose hip
/destiny weapon grip two_hand
/destiny weapon grip native
```

`equip`/`pose`/`grip` 마지막에 플레이어 이름을 붙일 수도 있습니다. 일반 아이템은 덮어쓰지 않습니다.
**장착·정적 포즈만 구현한 시각 프리뷰**이며 사격·탄약·피해·재장전·입력 기반 ADS/스코프는 미연결입니다.
[선정표·63종 출처](docs/design/45_W30_무기_선정표.md) · [구현·제약](docs/design/44_W30_무기군_프레임_모델.md) · [편집 원본](art/blockbench/weapons/w30/) · [실제 화면·QA](docs/qa/2026-10-23/w30/README.md)

[W31 기본 안료 복원](docs/design/46_W31_무기_기본안료_복원.md)은 light.gg 기본색을 목표로 63종을 다시 생성·적용했습니다.
전 모델 148~256큐브(평균 228.22), 1024² atlas·모델 단위당 14픽셀이며 기존 경로/ID와 3포즈를 유지합니다.
생성기 318파일 검증과 전체 자동 gate를 통과했고, 새 리소스팩의 native 229장을 촬영·검수했습니다.
[W31 전후 비교](docs/qa/2026-10-23/w31/native-comparison.jpg) · [검증·남은 아트 제약](docs/qa/2026-10-23/w31/README.md).

[W32 컴포넌트 양손 그립](docs/design/47_W32_컴포넌트_양손_그립.md): 장총 46종은 기본적으로
3인칭 양손 자세를 사용합니다. 권총 9종도 `grip two_hand`로 선택할 수 있습니다.
활·검·글레이브는 기존 자세입니다. 서버 아이템은 비발사 Polymer 프리뷰이며,
클라이언트 복제본에만 석궁+장전 컴포넌트를 사용합니다. **1인칭 양팔 생성은 포함하지 않습니다.**
W30/W31 저장 프리뷰는 `grip` 명령 또는 재장착으로 전환할 수 있습니다.

공유 리핑 자료와 파생 에셋의 공개·상업 배포 권한은 별도 확인이 필요합니다. 이 작업에서 commit/push하지 않았습니다.

## 전투 HUD

- 상단 중앙: 흰 체력 바(실제 HP), 30% 이하는 빨간색. 실제 흡수량이 있을 때만 청색 보조 바.
- 좌하단: 능력 실루엣 3개와 충전 밑줄, 궁극기 다이아몬드·가로 게이지. 준비/활성은 황금색.
- H17: 새 충전 완료에 `SUPER CHARGED` 배너·황금 확산/스윕, 준비 아이콘 채움과 속성별 발동 액센트. 재접속100%는 정적 준비 상태만 표시합니다.
- [궁극기 준비 연출](docs/design/24_궁극기_준비_HUD_연출.md) · [H17 실제 화면/검증](docs/qa/2026-10-22/h17/README.md).
- 필수 팩은 하트 44변형을 숨깁니다. 직업 none 플레이어에게도 대체 체력 바가 표시됩니다.
- 기본 핫바·배고픔·방어구·경험치는 아직 유지합니다. 전투 무기의 실제 탄창·예비탄·재장전 진행을 표시하며 미소유 무기 수치는 만들지 않습니다.
- H17 배너/발동 그래픽은 `scripts/generate_super_hud_assets.py`(Pillow)로 재생성합니다.
- 직접 제작한 HUD 에셋 재생성: Pillow 설치 후 `scripts/generate_hud_assets.py` 실행(26.3 로컬 클라이언트 JAR 필요).

## 자동 검증

과거 W52: **GameTest366/366 · JUnit358/358**, 최종 동일 JAR로 전체 강제 gate2회 통과.
검 약공격 다중 타격·대상 돌진·공중 속도 보존을 검사했습니다. 기존 황금총 조준과 탄약 HUD/모델은 유지합니다.
현재 Vision 실화면/native 검증은 초기 SDL 출력 문제로 보류이며 아래 과거 native 결과를 최신 빌드 인증으로 쓰지 않습니다.
[W52 설계·원작/authored 구분](docs/design/67_W52_검_다중타격_대상돌진_공중회귀.md) · [W52 QA](docs/qa/2026-10-24/w52/README.md).

W30 당시: **GameTest175/175 · JUnit142/142**, build 성공. 카탈로그·네이티브 codec·해시·활 연결성·손 원점과
OP 전용 프리뷰 명령/기존 아이템 보호를 검사합니다. [W30 검증 범위·실제 화면](docs/qa/2026-10-23/w30/README.md).

W31 당시: `runGameTest test build --rerun-tasks` 20 tasks 성공, **GameTest175/175 · JUnit146/146**입니다.
63종 큐브 증가·256 상한·1024 atlas·안료 회귀·3포즈 보존을 검사했습니다. [W31 실제 화면·provenance](docs/qa/2026-10-23/w31/README.md).

W32: 같은 전체 gate **GameTest179/179 · JUnit149/149**. 비발사·Polymer 왕복·권한·오프핸드·
1인칭 좌우 idle 역변환을 검사합니다. [W32 실제 화면·입력·제약](docs/qa/2026-10-23/w32/README.md).

H19 당시: **GameTest104/104 · JUnit59/59**, build 성공. 공허 활 당김→단발 릴리스와
연결 wrapper를 거친 카메라 이동 회귀를 포함합니다. 실제 native 입력·PNG와 저속 틱 한계는
[H19 QA](docs/qa/2026-10-22/h19/README.md)에 분리했습니다. 아래 H17/H16 수치는 당시 기록입니다.

Java 25에서:

```sh
rtk proxy ./gradlew runGameTest build --console=plain
```

H17 필수 GameTest **90/90**, JUnit **37/37**(실패·오류·스킵 0), build 성공.
실제 렌더링은 별도 Copper Golem Vision26.3에서 검증했습니다. H17은 준비 배너·좌하단 확산/스윕·세 속성 발동 액센트와 정리를 확인했습니다.
아래 성능 수치는 H16 당시 측정이며 H17에서 다시 계측하지 않았습니다.
로드맵1~3 구현에 이어4번은 실제2인·거리·야간/차폐 공간·성능 검증 완료입니다.
2인8닻+8선 fixture에서 전체 tickServer P95 2.883ms, 두 클라이언트119~120FPS(120 제한).
실제6인 이상/글로벌 최대 부하 성능 보증은 아니며,5번 일반 총기·재장전의 기본 구현은 아래 W33에 이어서 기록합니다.
원작 블룸·볼류메트릭·GCB 실제 통신을 검증했다고 간주하지 않습니다.
개발 서버 실행 중 소스 재컴파일은 하지 말고, 서버를 중지한 뒤 빌드하고 새 JVM에서 검증하세요.

## W33 무기 전투·사운드

63종 모델을 18개 무기군의 서버 PvE 동작에 연결했습니다. 기존 `equip`은 비발사 프리뷰이며,
아래 `load`로 지급한 별도 `[전투]` 아이템만 공격합니다. 지급·청음 명령은 OP 전용입니다.

```text
/destiny weapon load cold_denial
/destiny weapon status
/destiny weapon reload
/destiny sound list
/destiny sound play hunter.arc.super.start
```

현재 일반 총기는 우클릭 발사/유지, 활은 유지 후 놓기, 웅크리기 유지 ADS, Q 재장전입니다.
검은 좌클릭 약공격/우클릭 강공격/웅크리기 가드이며 Q로 재장전하지 않습니다. 검 탄약은 예비탄 없는 단일 유한 pool입니다.
월도는 W41에서 좌클릭 무료 근접·웅크리기 방패·우클릭 방패사격·Q 재장전으로 변경했습니다.
W33 당시에는 모두 유한 탄창·예비탄이었고, 현재 W40에서는 **Primary 무한 예비탄 / Special·Heavy 유한 예비탄**으로 변경했습니다. 원작 퍽·경이 효과·정확한 RPM의 완전 재현은 아직 아닙니다.
84개 사운드 키/61개 모노 OGG를 연결했습니다. **숫자 파일명 궁극기 후보는 임시 매핑**이고,
Shadowshot은 [W34](docs/design/50_W34_Shadowshot_영상_사운드.md)에서 사용자 지정 Deadfall 영상의 5구간 가공음으로 교체했습니다. 개별 stem이 아닌 영상 mix 편집이며 사용자 청감 검수가 남아 있습니다.
전체 gate: **GameTest199/199 · JUnit162/162**, build 성공. 최종 native19시나리오를 추가 확인했습니다.
[무기 구현](docs/design/49_W33_무기_전투_연결.md) · [음원 출처·제약](docs/qa/2026-10-23/w33/audio/README.md) · [W33 QA](docs/qa/2026-10-23/w33/README.md)

## W40 실제 무기 3슬롯과 탄종 HUD

소유한 전투 무기를 손에 들고 일반 유저 권한으로:
- /destiny loadout equip — 1 물리·2 에너지·3 파워 슬롯에 실제 아이템을 장착. 기존 탄약 보존.
- /destiny loadout select kinetic|energy|power — 장착된 슬롯 선택. 일반 1/2/3·휠 선택도 사용 가능.
- /destiny loadout status — 실제 장착 상태 확인.

슬롯과 탄종은 별개입니다. 에너지 슬롯에도 Primary가 있고 물리 슬롯에도 Special이 있습니다.
Primary의 탄창은 유한하며 재장전이 필요하지만 예비탄은∞입니다.
HUD는 큰 현재탄/작은 예비탄, 실제 속성/탄종색과 실제 보유한 다른 2슬롯의 총탄약을 표시합니다.
미장착 행은 만들지 않습니다. 장비모드를 활성화하면 다른 보관슬롯의 총으로 사격을 우회할 수 없습니다.
OP의 standalone QA 경로는 /destiny weapon standalone [player]이며 아이템/탄약을 바꾸지 않습니다.

[W40 설계·전체 목표 잔여표](docs/design/56_W40_탄종_3슬롯_장비_HUD.md).
[W40 실제 화면·검증 결과](docs/qa/2026-10-24/w40/README.md): GameTest213/JUnit180, native10시나리오.
원작 전체 무기 시스템은 계속 진행 중입니다. ammo meter·brick은 아래 W42에서 구현했고,
개별 무기 밸런스/정밀·반동·애니메이션·고유 프레임/경이 특성은 남아 있습니다.

## W42 탄약 획득·진행 미터

장비 모드에서 실제 적 처치/피해 지원으로 특수탄·중화기 미터가 진행합니다.
녹색/보라색 개인3D상자를 몸으로 주우면 **장착 원거리 무기의 예비탄만** 늘어나며 탄창/재장전 상태를 보존합니다.
W51 이후 검은 예외로 별도 예비탄 없이 사용 가능한 단일 탄약 pool에 직접 더합니다.
만탄·미장착/벽 너머에서는 소모하지 않고, 낭떠러지·생성 한도에서는 지급을 다음 안전한 처치로 이월합니다.
HUD에 두 생성 미터를 추가했습니다. 정확한 원작 stat곡선·모드 전체가 아닌 명시적인 Minecraft 튜닝입니다.

**GameTest242/JUnit198 · native48시나리오 통과.** 실제35처치와 걸어서 월도6/20→6/28·로켓1/5→1/6 획득 확인.
이전에 보류된 월도0/0 무료3연계/방패/방패 사격/1·3인칭 화면도 이번 통합 빌드에서 확인했습니다.
황금총 기존 방향과3→2→1탄약HUD 복귀도 재검증했습니다.
[설계·수치 경계](docs/design/58_W42_탄약_미터_드롭_획득.md) ·
[실제 HUD 모음](docs/qa/2026-10-24/w42/ammo-economy-states.jpg) ·
[실제 상자](docs/qa/2026-10-24/w42/frames/ammo_bricks_on_floor.png) ·
[QA/제한](docs/qa/2026-10-24/w42/README.md).

## 문서

W41 월도 무료 근접3연계·실제 적중 방패 충전·중앙 에너지 리티클 구현:
[설계·입력](docs/design/57_W41_월도_근접_방패.md) · [QA](docs/qa/2026-10-24/w41/README.md).
GameTest223/JUnit189 통과. W41 당시 Vision 초기화 정지로 실화면/native 검증은 미완료였고,
**W42에서 빈 탄약 콤보·방패·방패 사격과 실제 화면을 후속 확인**했습니다. 실제 Q 키/실게임 피해감쇄 비율 측정은 아직입니다.
W40에서 검증한 황금총·월도 방향/기존 탄약 HUD는 보존했습니다.

- [기획서](docs/Destiny_Guardians.md)
- [세부 문서 안내](docs/design/00_문서_안내.md)
- [작업 계획 – 기본 시스템](docs/design/11_작업_계획.md)
- [헌터 구현 로그·검증 범위](docs/design/13_헌터_구현_로그.md)
- [헌터 QA 증거](docs/qa/2026-10-22/README.md)
- [H16 다인·거리·전체 틱/FPS/패킷 결과](docs/design/23_다인_거리_성능_검증.md)
- [H19 공허 활 사격 연출·출처·제약](docs/design/28_H19_궁극기_활_연출.md)
- [H19B 활 3인칭 방향·당김 모델 보정/실제 화면](docs/qa/2026-10-22/h19b/README.md)

## 작업 규칙

- 브랜치: `main`에 직접 커밋하지 않고 `feat/<이슈ID>-<설명>`, `fix/...`, `docs/...`에서 작업
- 커밋: [Conventional Commits](https://www.conventionalcommits.org/) + 이슈 ID. 예: `feat(input): W2-03 input router`

| 패키지 (`kim.biryeong.destiny`) | 역할 |
|---|---|
| `data` | JSON 데이터 등록부 |
| `guardian` | 수호자 상태(직업·능력·쿨타임·게이지) |
| `input` | 바닐라 입력 → 능력 이벤트 |
| `ability` | 능력 실행 |
| `weapon` | 사격·반동·재장전·정조준 |
| `hud` | DisplayHud HUD·UI |
| `fx` | VFX, 포스트 이펙트 |
| `enemy` | 적·보스 |
| `mixin` | Mixin |

공허 Shadowshot: 발동만으로 준비·시위 당김→7서버틱 후 자동1발→착탄 시 닻 활성화. [W35 설계](docs/design/51_W35_Shadowshot_자동_시전.md).

Shadowshot 음원은 [W36](docs/design/52_W36_Shadowshot_연속_사운드.md)의2.23초단일연속본을발동시1회재생합니다. W34분할preview는이전검수본입니다.

월도Nezarec’sWhisper는[W37](docs/design/53_W37_월도_1인칭_파지.md)의전방1인칭파지를사용합니다.다른총기/3인칭은유지합니다.

### W44 조준/반동 입력
- live 총기: **웅크리기 유지 ADS · 우클릭 발사/충전 · Q 재장전**(Ctrl+Q 포함 무기 드롭 금지).
- 월도: 웅크리기는 기존 방패, Q 재장전. 검/월도는 일반 ADS 제외. Guardian 스킬 조합은 유지.
- Q는 Vision v1 native 키가 아니므로 GameTest packet route 검증이며 실제 키보드 검증으로 세지 않음.
- 배율은 minigame-lib의 `config/minigame-lib/shaderfx.json` → `"dynamic-fov-shader": true` 후 팩 재생성/재접속 필요. 이 로컬 QA 서버는 활성화해 검증.
- [W44 구현/경계](docs/design/60_W44_ADS_반동_리티클.md): fixed70 기준 FOV, 스코프 화면·정확원작반동/바닐라잔여HUD는 후속.

- [W77 잠자리 정밀 처치 폭발](docs/design/92_W77_잠자리_정밀_처치_폭발.md): 공식4무기 소켓·속성 폭발·구면거리/벽/아군 보호·원본 귀속. 최종 결과는 W77 QA에 기록.

- [W78 파동 프레임 지면 전파](docs/design/93_W78_파동_프레임_지면_전파.md): Deafening Whisper·Dimensional Hypotrochoid의 지면 착탄/전진 파동·실제 지형/차폐·검증 경계.

- [W81 피해 숫자 가독성](docs/design/96_피해_숫자_가독성_배치.md): 폭발탄약·자동연사 개별피해의 owner-only 화면투영 배치·상대상승 sweep·원작영상과 로컬정책 구분.


## W83 — 스페이드 에이스 (2026-10-25)

기존 전설63종에 첫 경이 Ace of Spades를 추가했습니다. 메멘토 모리6발·정밀 처치 Firefly·잔여발수 HUD·원본87큐브 모델·전용 발사/재장전 음원을 연결했습니다. 최종 동일 JAR로 **717 GameTest / 624 JUnit 전체 강제검증2회** 통과. Vision 클라이언트는 첫 SDL 화면 출력에서 멈춰 이번 빌드의 실제 입력·모델/HUD framebuffer 검증은 보류입니다. 생성팩 검증을 실게임 성공으로 간주하지 않습니다.

[설계](docs/design/98_스페이드_에이스_경이_무기.md) · [현재 검증/한계](docs/qa/2026-10-25/w83/README.md)

## W84 — 이자나기의 짐 (2026-10-25)

두 번째 경이 `izanagis_burden`을 추가했습니다. **Q 일반 장전 / Ctrl+Q 연마된 칼날**, 유료2~4탄 합치기·교체/저장 후 강화탄 유지·실제 xN HUD·원본79큐브·일반/연마 전용 음향을 연결했습니다. 장전/탄약 경계의 원작 미확정 부분은 로컬 정책으로 구분합니다. 동일 JAR로 **729 GameTest /638 JUnit 전체 강제검증2회** 통과. JSON 저장 시 강화탄을 잃는 정수폭제한 버그도 수정했습니다. Vision 실화면·실입력·실청취는 아직 보류입니다.

[설계](docs/design/99_이자나기의_짐_연마된_칼날.md) · [검증/한계](docs/qa/2026-10-25/w84/README.md) · [음원 미리듣기](art/weapons/w84/audio/audition.html)


## W85 — 피격 플린치 / No Distractions (2026-10-25)

실제 HP·흡수 피해 뒤 서버/클라이언트 상대 회전을 연결했습니다. 이자나기는 **1초간 사격 없이 ADS → No Distractions35% 저항**, 활성 후 발사 유지·조준 종료/실제 수납으로 해제하며 **타이머 없는 활성 HUD**를 표시합니다. 카메라 소유권·장전/handling·피치 한도/예산·중첩 피해를 보호합니다. 흔들림 각도/보간은 명시적 로컬 조정값입니다.

동일 JAR **740 GameTest /650 JUnit 전체 강제검증2회** 통과. 기존6537asset/162sound는 전부 보존했습니다. 실화면·실입력·체감검증은 아직 보류입니다.

[설계](docs/design/100_피격_플린치와_No_Distractions.md) · [검증/한계](docs/qa/2026-10-25/w85/README.md)

## W86 — 피격 방향 / 위험 체력 HUD (2026-10-25)

실제 HP·흡수 피해를 받은 방향에 compact red wedge, 현재 HP30% 이하에 주변부 경고를 추가했습니다. 최대4origin snapshot+1경고로 제한하고 적 live tracking 없이 현재 자기 위치/시야로만 회전합니다. 원작 영상은 정성적 참고이며 수치·silhouette는 로컬 조정입니다.

최종 동일JAR **750 GameTest /662 JUnit 전체강제2회** 통과. 기존6540asset·162sound를 보존했습니다. 과정 중 기존Ace거리시험의간헐실패(원인미확정)와시네마틱chunkcontext경고는QA에보존했고실화면검증은보류입니다.

[설계](docs/design/101_피격_방향과_위험_체력_HUD.md) · [검증/실패/한계](docs/qa/2026-10-25/w86/README.md) · [오프라인 schematic](art/hud/w86/assets/offline-full-hud.png)

## W87 — 청크 경고 원인 분리 / 사격 진단 (2026-10-25)

시네마틱 청크 경고는 실제 서버 코드가 아니라 로그인 단계를 생략한 embedded 테스트 접속의 registry context 누락이었습니다. 테스트 접속만 보완하고 실제 chest 청크·BE·codec 검증을 추가했습니다. Ace 진단도 실제 사격 직전의 동일 조준/충돌 경로를 관측하도록 수정했습니다.

**755 GameTest /662 JUnit 전체강제2회**, Polymer context 경고0건. 생산 무기/HUD/음원/JAR·팩은 그대로입니다. 과거 Ace 간헐 실패의 유일 원인은 아직 미확정이며, 실화면 검증도 보류입니다.

[설계](docs/design/102_접속_Context와_사격_진단.md) · [검증/한계](docs/qa/2026-10-25/w87/README.md)

W94: [일반 활 근접 파티클 격리 진단](docs/qa/2026-10-25/w94/README.md). 제품8452pin/7013asset불변·기본/차단/복원18native·341PNG. 큰중앙sprite의trail기여확인,특정W93상단solidrectangle및제품수정은미해결로분리.

W95: [일반 활 발사자 근접 궤적 보정](docs/qa/2026-10-25/w95/README.md). 관전자 원래샘플을 유지하고 발사자 근접 샘플만 제외. 815GT/689JUnit 강제2회·8native/161PNG. 대표 중앙방해 감소만 수락하며 작은dust/특정W93상단사각형은 남습니다.

W97 진행: [저체력 탄약 HUD 레이어 진단](docs/qa/2026-10-25/w97/README.md). 최소 depth 후보와 회귀2GT 컴파일까지 준비했습니다. QA 첫 화면 출력 정지로 실제 가역 비교는 미완료이며 HUD 레이어 설정은 검증된 W96 그대로입니다.


W98: [명명된 발사음 변주3종](docs/qa/2026-10-25/w98/README.md). 기존 Fire_1을 보존하고 같은 무기 폴더 Fire_2/3을 추가했습니다. 820GT/704JUnit 강제2회와 실제 서버 생성팩 감사를 통과했고, 검토용 WAV3개를 제공합니다. 실게임 재생·청취와 W97 HUD 가림은 미확인입니다.

W99: [저체력 탄약 HUD 레이어 복구](docs/qa/2026-10-25/w99/README.md). W97/W96-N1의 가림을6→0→6 실화면으로 분리하고 critical layer0만 적용했습니다. 822GT/704JUnit 강제2회·probe-free 두 해상도85PNG·HP6/1/ADS/회복 확인. W98 음원 실청취와 전체 무기 목표는 미완료입니다.

W100: [은둔자 개별 탄창 재장전](docs/qa/2026-10-25/w100/README.md). 기존217큐브·41발43tick을 보존하고 몸체/탄창 proxy 표현을 추가했습니다. 829GT/715JUnit 강제2회·Vision82PNG/양grip0→41·ADS/발사복귀 확인. **탄창 교체가 화면 하단에 가리는 W100-N1은 미해결**이며 전체 시각 완성도/실청취는 아직 수락하지 않습니다.

W101: [은둔자 장전 구도 후보](docs/qa/2026-10-25/w101/README.md). 기존217큐브를 재사용해 active 장전 위치/roll/분리 경로를 조정했습니다. 829GT/721JUnit 강제2회와 실제 서버팩은 통과했습니다. **Mac 잠금으로 native0·PNG0이며 탄창 가시성 W100-N1은 미해결**입니다.

W102: [무기별 발사·장전 원음 연결](docs/qa/2026-10-25/w102/README.md). 6무기의 발사·4무기의 장전을 동일 무기 이름 폴더 원음으로 연결하고 기존6장전 duration key를 유지했습니다. 831GT/725JUnit 최종강제2회·실제팩12359 entry의 정확16Ogg 추가 감사 통과. [확인용 WAV6개 묶음](docs/qa/2026-10-25/w102/review-audio-w102.zip). 첫 gate/QA 설정 불일치 팩은 보존했고 **native 재생·실청취·W100-N1 가시성은 미완료**입니다.

W103: [폭파 전문가·수류탄 연계](docs/qa/2026-10-25/w103/README.md). 정확11무기 기본 특성·유료 최종 처치의 baseline 에너지·실제 수류탄 release 이후 예비탄 장전/원본 귀속을 추가했습니다. 841GT/731JUnit 전체강제2회·실제팩12359entry 보존. **현재D2 능력/stat 보정은 근사 범위, native 검증은 Mac 잠금으로 보류**입니다.

W104: [로켓 표적 잠금·유도](docs/qa/2026-10-25/w104/README.md). Pyroclastic Flow 고유 기능·Bad Omens/Bellowing Giant 기본 Tracking Module 명시 선택·실제 ADS/유료 발사 snapshot/속도 보존 회전·기존 레티클 획득/잠금 피드백을 추가했습니다. 852GT/744JUnit 전체강제2회·실제팩 byte동일. **유도 수치는 서버 조정값이며 native 시각/청취·전체 목표는 미완료**입니다.

### W112 — individual silhouettes / charge feedback

65 original-derived weapon silhouettes now route the selected/two stowed HUD rows;
7 fusion/LFR profiles expose their real accepted charge/paid-burst reticle state.
Final central regression:887JUnit/927GameTest,0failed/skip. Native visual
acceptance is pending Mac unlock, not claimed from the offline contact sheet.
See [design126](docs/design/126_무기별_실루엣과_충전_조준선.md),
[W112 evidence](docs/qa/2026-10-25/w112/README.md),and
[native queue](docs/qa/NATIVE_QUEUE.md).

### W113 — independent product worktrees

Two real dirty-snapshot worktrees delivered scoped full-auto firing settings and ten new authored swap directions (four weapons /twelve total). Master integrated charged repeats and input lifecycle, then passed898JUnit/939GameTest. Native remains pending currentMacunlock; no headless-as-native claim. [Design127](docs/design/127_자동_사격과_무기_교체_확장.md) · [W113 evidence](docs/qa/2026-10-25/w113/README.md).


### W184 — 원소 축전지 / Distant Relation·Farewell 장전

원작영상 기반 두 개별 통탄창 장전(89/118요소)과 실제 장착SUPER속성의 원소축전지2소켓을 통합했습니다. 최종fresh1754JUnit/actualFabricGT16, JAR175리소스·실제생성서버팩174자산을 확인했습니다. CU잠금반환으로 native/새PNG는0이며 전체목표는진행중입니다. [QA·한계](docs/qa/2026-10-27/w184/README.md).


### W185 — 빠른 무장 / 저격·융합 개별 장전

3개 독립 dirty-CoW worktree의200경로를 SHA 통합했다. 실제 교체 후20틱 handling100/ready-only0.95·실제 ADS 입력 취소의 Quickdraw16공식소켓과 Apostate115/Hollow Words97요소의 원작영상 기반 개별 장전을 추가했다. whole-mag37라우트이며 기존UV/ADS/음원/실탄권한을 유지한다. freshJUnit1777/251classes·actualFabricGT16·JAR175리소스/실제서버팩174자산 통과. freshCU잠금반환으로 native/새PNG0이고 전체목표는 진행중이다. [검증·원작·한계](docs/qa/2026-10-27/w185/README.md).


### W187 — 황금 탄약 / 로켓 개별 장전 / 실게임 취합

3개dirty-CoW worktree의198경로를통합해Code Duello219/Bellowing Giant130요소개별장전과공식6소켓Lead from Gold실제Heavy픽업예비탄지급을추가했다. fresh전체JUnit1798/actualFabricGT16통과후실화면에서Codeoffscreen구도를수정,targeted5+jar와새팩/native두파지재검증을마쳤다. 두실행총150nativeoperation/1361rawPNG로W182–185대표대기·AceADS빨간홀로그램·Gold수납Special0/0→0/8을확인했다. 원작Gold반올림/HIR공식·실청취·손IK·새3P·unfocused수락은별도이며전체목표는진행중이다. [결과·실제GIF·한계](docs/qa/2026-10-27/w187/README.md).


## W188 — 선형 융합 장전 · 참선의 순간
Line in the Sand/Stormchaser 개별 battery장전(최대81/96요소,기존5탄/49틱·UV·음원보존),공식10base소켓 ZenMoment 실제paid-hit·incomingflinch합성을추가했다. 사용자지정DDC수치기준을프로젝트지침/설계162에등록,미확정flinch율/상한은임시튜닝으로구분한다. actualFabric13/13·통합full1825중기대map누락1개는test만수정후focused2+jar통과. 한Vision세션에서두파지4장전/4ADS·교체취소2·16display·3Pcanonical·Zen실제HP/만료확인. [전체 기록·실제 GIF·제한](docs/qa/2026-10-27/w188/README.md). 전체무기goal은진행중.


## W189 — DDC Firmly Planted / 융합소총 개별 장전

DDC Weapon Perks97행의 기본 crouch20/30/.6/.83/.2·Fusion10/15/.8/.915/.6를 공식8소켓에 반영했다. 에렌틸136/코리올리104요소 개별 cell장전과 합쳐3dirty-CoW196경로를통합했다. fresh전체JUnit1845/actualFabric17통과, 한Vision세션29completed/releasedop·434rawPNG로 비활성 창의 장전4/ADS4·실제crouch/paid4발·16display/3Pcanonical을확인했다. 실제handIK/새3P장전·실청취·다인FPS와기존전체수치소급검증은완료주장없음. 소유fixture/lease/runtime/port/relay/awake정리완료,전체goal진행중. [근거·실제GIF·제한](docs/qa/2026-10-27/w189/README.md).

최근 무기 작업: [W208 5무기 장전 확장](docs/design/182_W208_5무기_장전과_손_연속성.md), [W209 기관단총·핸드캐논 파지](docs/design/183_W209_기관단총과_핸드캐논_파지.md). 실행·실패·시각 수락 범위는 각 날짜 QA 문서에 기록한다.
