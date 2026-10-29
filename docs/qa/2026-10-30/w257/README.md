# W257 리소스팩 로딩 최적화

## 범위와 기준선

- 원본 디테일·텍스처·애니메이션61포즈·시전시간 유지. 출력 팩의 미참조 모델과 정확 중복 모델만 정리하고 서버 그래프 복사를 줄인다.
- 이전 W256 팩: `/private/tmp/destiny-w257/before.zip` (94,066,893 bytes, 66,804 entries, JSON65,113개).
- 서버 4GB 유지. 접속자0명 확인 후 정상 stop, 25565 포트 해제 확인.
- master: 통합·중복모델공유·중앙검증·Vision. slot4 Anscombe: reachability 분석/pruner. slot5 Socrates: gunOnly 반복 deepCopy 개선.

## 진행

1. 기준선 보존 및 분석 완료.
2. 출력 모델 참조 정리 및 그래프 복사 개선 진행 중.
3. 통합 빌드·팩 통계·Danmo4GB 실화면 검증 대기.

## 분석·구현 중간 결과

- 미참조 versioned 무기 모델 9,539개 / 원본 JSON 55,461,400 bytes를 안전하게 출력 제외 가능. 외부 네임스페이스·모든 item branch·blockstate·parent·메타데이터 참조는 보존한다.
- 정확히 byte가 같은 생성 모델만 canonical ID를 공유한다. 모든 item ID와 선택 조건·순서·pose transform을 보존한다.
- gunOnly의 각 노드 전체 deepCopy 반복을 제거했다. detached metadata와 child를 한 번씩 복사하며 입력 불변·동일 출력 회귀를 추가했다. 관련 1차50/50, pruner 포함 후35/35 통과(상이한 filter 합계로 중복 포함).
- W256 client 기록: 팩 reload 시작03:58:48 → blocks/items atlas03:59:46, menu→world69.97s. 같은 Mac Danmo4GB 과거 단일 실행값이며 Windows 시간은 아니다.
- 기존 item atlas16384×16384. 예전 w30/w123텍스처가 각각63장, 각66,060,288pixels를 차지한다. 실제참조 없는 versioned weapon PNG만 출력제외하는 보강 작업 중이다.

- 텍스처 helper 통합: versioned weapon PNG만 대상으로 모든 retained JSON/mcmeta와 기타 텍스트의 명시적 참조를 보존한다. 원본 PNG 바이트는 수정하지 않는다. 신규3개 texture회귀 및 model회귀 묶음16개 통과.
- 신규 전체 build/check 실행 중. 이번 변경의 Java 게임 동작/원본 모델 파일/리소스팩 셰이더 변경 없음.

## 전체 gate 실행 범위 정정

`gradlew build --continue`가 전체 runGameTest도 시작했다. 오래된 W68 ADS·W71 selector 등 현재 설정과 다른 기대값이 대량 실패하여 master가 중단(exit130)했다. 이 실행은 통과가 아니며 이번 변경의 회귀라고도 단정하지 않는다. 게임 동작을 수정하지 않은 출력팩 최적화이므로 `test assemble --continue` 전체JUnit/산출물과 별도 대표 Vision 검증으로 범위를 정정했다.

## 실제 출력·1차 클라이언트 측정

- W123가 resource converter 단계에서 텍스처를 바꾸는 순서 문제를 첫ZIP비교가 검출했다. 첫후보에서 W123 검5종 텍스처를 잘못제외한것을 발견해 운영반영전에폐기했다. `WeaponSurfaceProjection.projectOutput`으로 최종변환된 snapshot을 기준으로 분석하도록수정하고회귀를추가했다. 명시적 legacy W115에서는 texture pruning을보수적으로생략한다.
- 최종QA팩63,149,782bytes(이전94,066,893), JSON50,888(이전65,113), models49,655(이전63,800). 미사용weaponPNG63개제외.
- Destiny item983개경로/모든selector·resolved parentgeometry동등. 남은texture/audio/shaderbyte동일. 제거texture참조0. BetterModel의서버별생성ID는QA/운영구성차이때문에이동등비교에서제외했으며직접화면확인한다.
- 서버생성04:40:52→04:41:13=21초(이전운영67초,서버구성차이있음). Danmo4GB/OpenGL reload04:41:50→itemsatlas04:42:00=10초(이전58초), 메뉴→인게임14.305831초(이전69.96626초). 단일Mac실행비교이며Windows보장아님.
- 아이템atlas는여전히16384×16384다. atlas GPU할당크기가절반이됐다고보고하지않는다.
- 서버PID48499,clientPID49119 모두MaxHeapSize4294967296 확인.
- 실제PNG 에이스·Biting Winds·Mindbender hip/ADS 확인. 체크무늬·모델누락없음. 능력검증직전physical_user_input으로취소되어중립상태확인후사용자의백그라운드재개답변을받았다.

## W257 시각 검수·정리

- 실제PNG `weapons-contact.png`: 에이스/활/샷건 hip·ADS 유지, 모델/텍스처 누락 없음. `motion-contact.png`: 에이스/샷건 장전, 수류탄 투척, 아크 후방카메라/본체 확인. 장전은콘솔fixture로요청했고발사/ADS/수류탄/궁극기는native입력이다. 이번에는음원을직접청취하지않았다.
- user가사용하지않는다고답한후native재개,궁극기종료후cameraIsPlayer=true와leaseActive=false/heldKeys=[]/pendingSteps0/이동native입력false확인.
- 문서화된232 GameTest실패는추가사용자요청에따라W258에서수정중이며W257통과로계산하지않는다.

최종정리에서는같은snapshot투영코드를별도 `WeaponSurfaceProjection` 클래스로추출했다. 기존untracked W123제품/테스트파일을이번커밋에끌어들이지않기위함이며동작은같다. 추출후targeted컴파일/회귀를다시실행했다.
