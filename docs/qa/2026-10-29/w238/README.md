# W238 실제 무기 PROFILE 스킨 팔 전환

## 목표와 수락 조건

기존 구현은 검증 가능한 백업으로 보존하고, 실제 무기 전체의 기본 표시를 PROFILE 스킨과 공용4팔 디스플레이 방식으로 전환한다. 기존61 pose·발사/ADS·장전/교체·원작 리그 접촉 위치·타인3인칭/인벤토리 표현·실제 탄약과 입력 경로를 유지한다. 같은 공식 Danmo4.6_263c62mods·4GB에서 구/신 팩의 ZIP/raw JSON/로드 시간/GC 후 heap을 비교하고 코어 셰이더·Iris·다른 팩·Windows 한계를 구분해 보고한다. 미검증 화면을 완료로 기록하지 않는다.

## 단계 기록

1. W237 최종commit a691041b에서 시작. 기존 live pack과 소스4개를 /private/tmp/destiny-w238/legacy-backup에 보관했고 SHA256 manifest를 기록했다. 원본 리핑/그림/61pose 데이터를 삭제하지 않는다.
2. 현재 dirty56개 기준해시 /private/tmp/destiny-w238/dirty-before.json을 저장했다. 소유 외 파일을 보존한다. live runServer를 정상 stop했다.
3. 고정slot4를 재생성하지 않고 현재통합본으로 갱신했다. worker Harvey가 ProfileArmGraph selector 컴파일/평가/테스트3파일을 맡고 master는 pack/shader/runtime을 맡는다. Epicurus는 읽기전용 호환성 조사로 같은게임창을 조작하지 않는다.
4. ProfileArmAssets가 기존wrapper의 arm pose 선택을 서버로 이동하고 client는 gun-only view route+공유PROFILE head carrier만 받도록 구현 중. nativeheld는1Pempty, GUI/관찰3P는 기존source fallback. ProfileWeaponView는 owner-only5display(총1+팔4)와 lifecycle cleanup을 구현 중이다.

## 현재 상태

기본 PROFILE 경로 구현과 아래 범위의 통합 검증을 완료했다. 각 항목의 실기/정적 검증 범위와 알려진 제한을 함께 적용한다. 픽셀 tint 방식 rollback은 destiny.weapon.legacyPixelArms=true로만 선택하며 기본은 새 경로다. source/백업에 남은 legacy데이터와 실제생성client pack을 구분한다.


5. 실제 headless Blender5.4로 에이스 원본source.blend를 열어 SHA256과 idle/ADS/reload3action의 시작·중간·끝9샘플의 손목/팔꿈치/어깨/무기 본을 평가했다. 최초 캐시 action 이름의 병합 suffix(.004)가 원본과 달라 조회 실패했고, tag ID로 원본 action을 찾아 재실행했다. 원본파일과 타이밍은 변경하지 않았다. 본좌표는 blend-review.json에 기록한다. 기존61pose를 새로 리타깃하지 않고 기존 native display matrix를 그대로 사용한다.
6. native26.3 FirstPersonHandsAndItemsRenderer의 기본손 translation(.56,-.52,-.72)과 DisplayRenderer.ItemDisplayRenderer의 내부Y180 회전을 javap으로 확인했다. 후자를 root행렬의 Y180으로 상쇄해 같은 view좌표를 사용한다. 최초compile은 worker클래스 통합 전이어서 missing ProfileArmGraph2건으로 실패했으며, 다른 master소스 오류는 없었다. 이는 아직 runtime수락을 뜻하지 않는다.

7. 최종 통합 selector 12개·asset 2개·carrier 4개, 총 18개 JUnit이 실패/오류/skip 없이 통과했다. Danmo의 GCB4.0 시점 통지를 이용하면 F5 디스플레이 제거가 가능하다. 재접속 초기 3인칭 동기화 한계는 남는다. 네이티브 ModelOffset은 NO_OFFSET, ModelViewMat은 카메라 회전뿐이어서 새 UBO 없이 F5를 판별할 수 있다는 가정은 폐기했다. 외부 셰이더팩 활성화 및 순수 바닐라 F5는 별도 호환성 한계로 다룬다.
8. R1 팩 생성은 Incompatible item shader로 중단됐다. 기존 CriticalHudShader가 출력 converter에서 패치하므로 preFinish에서 완성 hash를 기대한 것이 원인이었다. item 패치를 기존 converter 뒤에 추가하도록 수정했다. 실패한 팩은 클라이언트에 적용하지 않았다. Danmo GCB의 gcbThirdPerson 상태에서 소유자 디스플레이 5개를 제거하도록 연결했다.

9. R2 팩 생성 성공. 활성 경로 195개, 서버 포즈 66,812개, 제외 파일 101,299개. ZIP 140,164,518→85,110,780bytes(-39.28%), raw 1,059,880,007→253,644,567bytes. 기존 skin_arm 모델 0개, 전체 item graph의 픽셀 손 참조 0개, destiny 모델 참조 누락 0개. entity 160개 프로그램 컴파일·링크 모두 통과. Danmo staged/active 62개 JAR의 SHA256이 모두 일치한다. 실화면·메모리는 아직 평가하지 않았다.

10. R2 팔/entity 160개 + 총기/item 90개, 총250개 프로그램의 OpenGL/Vulkan 컴파일·링크가 모두 통과했다. 이것은 셰이더 문법/링크 검사이며 Windows/Vulkan GPU 실기 증명은 아니다. 같은 Danmo 62 JAR·4GB·Iris 외부shaderpack 미선택으로 격리 Vision 클라이언트를 기동했다.

11. R2 Danmo 4GB에서 새팩을 받고 타워 진입에 성공했다. PNG ace-hip, ace-ads-fire를 실제로 열어 총·팔 표시와 조준·발사를 확인했다. F5 직후 캡처에는 통신 지연으로 화면무기가 남았고, GCB 시점 통지 후 settled 캡처에서는 사라졌다. native sequence는 released, heldKeys=[]로 종료됐다. 사용자의 직접 Q·시점전환·무기교체 입력이 들어와 이후 자동조작은 중단했다. 에이스라는 라벨로 남은 reload2 자료의 실제무기는 Steelfeather Repeater였으므로 이를 에이스 장전 증거로 사용하지 않는다.
12. R2 한 번의 비교 측정: 이전 W237 로그 startup55.091/menu→world40.242477/total95.33348초, 새38.508/15.118286/53.626286초. 같은 Danmo62JAR·Mac·4GB 프로필의 순차 실행이며 캐시/프로세스/서버 상태까지 통제한 통계 벤치마크는 아니다. W237 GC후heap3123389KiB, R2는2191489KiB(-29.84%). 이전 runtime은 W237 독립probe가 포함된legacy경로였고 ZIP 크기기준은 별도로 보존한livelegacy140164518bytes다. Windows/Vulkan OOM해결 확정으로 쓰지 않는다.

13. R2 전체 JUnit 2121개가 실패/오류/skip 없이 통과했다. 기동 중인 QA classpath를 변경하지 않도록 이미 빌드된 R2 classes를 사용하고 compile/resource 작업을 제외했다. 의존 프로젝트 작업은 UP-TO-DATE, 실행한 작업은 test 1개다. 남은 실게임 입력은 사용자 QA 사용 여부 확인 후 재개한다.

14. 사용자 입력 중단 답변 후 R2b/R2c 캡처를 진행했다. 첫 시도는 리소스 로딩 overlay로 control_epoch_changed가 났으며 입력 성공으로 취급하지 않았다. R2b 에이스에서는 실제 reload route를 포착했다. 나머지 세 무기는 교체 직후 발사/장전 불가여서 해당 자료로 장전을 통과 처리하지 않았다. R2c 이자나기는 실제 발사 후 강화/스코프 경로를 포착했지만 후반 physical_user_input로 lease가 취소돼 완전 수락하지 않았다. 입력은 중립으로 해제했고 QA client/server를 종료했다.
15. Worker PNG 검수는 ADS 돌출을 회귀로 판정했다. 원본 bbox/cap과 새모델 bbox/cap은 일치하나 기존 shader가 뒤쪽 정점을 vec4(2,2,2,1)로 옮겨 삼각형을 화면 구석으로 늘릴 수 있었다. entity/item 모두 signed homogeneous w를 보존하고 0.025 근평면에서 z=w가 되도록 역Z식을 수정했다. 포즈·무기 위치·장전 타이밍은 바꾸지 않았다. 다음 R3 화면으로 수락 여부를 판단한다.

16. 다른 무기의 비조준 위치가 너무 오른쪽이라는 사용자 피드백을 반영해 공통 손 기준 X를 ±0.56에서 ±0.44로 줄였다. WeaponAiming.progress가 0→1로 변하면 원래 ±0.56으로 복귀하므로 완전 ADS 가늠쇠/스코프 정렬은 유지한다. 총과 네 팔 조각에 같은 행렬을 적용하고, 포즈 ID가 그대로여도 ADS 이동량이 바뀌면 팔 변환을 갱신한다. 좌주손은 부호를 반전한다. 아직 실화면 수락 전이다.

17. R3 Danmo 실제 캡처에서 ADS 피부 돌출은 사라졌고 에이스 발사 후 12→13 장전, SMG/소총/샷건/활/이자나기/월도의 실제 발사·장전 경로를 포착했다. R3 shader250개와 targeted JUnit19개 통과. 다만 hip contact sheet를 검수하니 공통0.12 이동만으로 긴 총기·SMG는 여전히 오른쪽으로 치우쳐 수락하지 않았다. R4는 무기군별 hip X(핸드캐논/보조/활0.44, SMG0.12, 자동/파동/정찰0.20, 월도0.26, 나머지0.24)로 조정하며 완전 ADS는 모두0.56을 유지한다. 좌우 주손 교체 시 총과 팔 모두 즉시 새 파지로 바꾸어 전환 순간 보간 불일치도 제거했다.

18. R4 hip은 개선됐지만 Ammit 완전 ADS PNG를 열자 여전히 중앙 정렬이 아니어서 수락을 철회했다. native26.3 javap의 charged-crossbow idle은 기본 손 이동 뒤 X=-0.641864×주손부호, Y회전=10°×주손부호를 적용한다. 기존 twohand 모델/팔 포즈는 이 행렬을 전제로 하지만 ItemDisplayRenderer는 이를 적용하지 않아 새 루트에서 누락됐다. R5는 무기군별 임시 offset을 제거하고 양손 경로에 정확한 native charged 행렬을 총·팔 공통 적용한다. 한손 hip만0.44, ADS0.56 보정을 유지한다. 원인 발견 전의 R3/R4 ADS 검증을 최종 수락 근거로 쓰지 않는다.

19. R5 실제 Danmo 4GB에서 7종(에이스·은둔자·Ammit·정신왜곡자·이자나기·살을 에는 바람·네자렉)의 hip/ADS 왕복을 캡처했다. Ammit 가늠쇠 정중앙과 SMG 본체/양손의 화면 복귀를 PNG로 확인했다. 최종 targeted JUnit20개, 생성 팩과 일치하는 shader250프로그램 통과. 최종 SMG/자동소총/샷건 발사→장전은 native use 입력 + server reload fixture를 구분해 기록했으며, 실제 탄약14→41·19→33·3/5 reserve25→5/5 reserve23을 서버 로그로 확인했다. F5 앞/뒤에서 개인overlay 제거, 1P 복귀 재생성, 빈손 전환에서 총/팔 제거 및 바닐라 손 복귀를 실제 PNG로 확인했다. 모든 lease/heldKeys/pendingSteps/nativeInput은 중립으로 종료했다.

## 최종 측정 범위

- 최종 팩85,110,858bytes(약85.1MB), 기존140,164,518bytes(약140.2MB), 39.28% 감소. raw 1,059,880,007→253,644,628bytes. weapon pose23,983개와 sound285개는 유지한다.
- 구 실행 startup55.091 + menu→world40.242477 =95.33348초. 새 팩 최초 측정 R2는38.508 +15.118286 =53.626286초. 최종 R5 반복 실행은32.778 +10.826279 =43.60428초. 같은Mac/Danmo/4GB의 단일 순차 실행이며, 반복 실행은 캐시 효과가 포함되어 독립된 속도 개선율로 일반화하지 않는다. W237 구 runtime은 독립probe가 포함되며 크기기준은 보존한livelegacy팩이다.
- 명시적 GC 후 heap used는 기존3,123,389KiB에서 최종2,189,163KiB로 약912MiB/29.91% 감소. 프로세스RSS나 최대메모리 측정이 아니다. Windows4GB OOM해결은 별도실기확인 필요.
- 최종 실행에서 OOM·shader compile/link failure·model load failure는 없었다. ModernFix perf.dynamic_resources 규칙 불일치2건은 남아 있다.
- 클라이언트의 반복 팔 geometry를 제거하는 대신 서버가66,812포즈의 선택/행렬을 보유하고 소유자당 디스플레이5개를 관리한다. 다인 부하·서버heap/네트워크 비용은 이번 단일클라이언트 측정으로 보장하지 않는다.

20. Worker Harvey가 R5 7종 hip/ADS와 장전3장 실제 PNG를 독립 검수해 nativecharged 복구·총기 framing을 수락했다. 이전 R4 판정은 폐기했다. Biting Winds의 팔이 화면 하단을 크게 가리는 잔여 구도는 남아 있어 전체 무기 무결점으로 확대하지 않는다. 정지 PNG는 장전 모든 프레임의 연속 접촉을 증명하지 않는다. worker를 종료하고 고정slot4는 삭제 없이 재사용 대기로 복귀했다. QA client/server는 입력 중립 확인 후 모두 정상 종료했다.

21. 실제 runServer를 재개했고25565에서 기동 및 새PROFILE팩 생성 완료를 확인했다. online-mode=true, allow-flight=false, andlist OP4를 유지한다. 실서버 팩85,275,750bytes(격리QA85,110,858bytes와 구분)이며 상세차이는live-pack.json에 기록했다. 독립48시간 caffeinate PID79904는 계속 유지한다.

실서버와 QA의 코어shader4개 및 destiny에셋은 동일하다. 실서버에 추가된256파일과 변경된234파일은 BetterModel 네임스페이스뿐이다. 실서버 총팩 기준으로도 기존대비39.16% 감소했다. QA용 probe 없이 실제 runServer가 새 팩을 제공하며25565 listen을 확인했다.
