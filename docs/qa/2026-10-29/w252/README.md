# W252 능력 투척과 선택형 직업 점프

상태: W252 구현·관련 검증 완료. 기존 전체 gate 자산 불일치 4건은 아래 기록 유지.

## 범위
- 원본 shared_grenade_throw/source.blend 실제 평가 → 플레이어 스킨 FP 팔·3P 투척 → 접촉 시점에 발사.
- 기존 8종 수류탄의 원작 외형 근거와 모델 개선. 리핑 모델을 찾지 못하면 재설계와 원본 사용을 구분.
- 헌터/타이탄/워록 점프 선택 UI·고유 공중 이동·자원/종료 처리.

## 배정
- 슬롯1 Lovelace: 점프 물리·옵션·관련 테스트.
- 슬롯4 Ramanujan: 수류탄 자산·출처.
- master: Blender 투척 평가, 공유 UI/등록/실행 연결, 중앙 검사와 Vision 취합.

## 진행
1. 기존 경로 조사: 타이탄/워록 수류탄 즉시 발사, FP 팔 투척 경로 부재, 메뉴 JUMP 누락 확인.
2. 고정 슬롯1·4를 8e6cfbb4 통합본으로 갱신(기존221632파일 기준선 보존).
3. 원본 Blender 72본, 3클립 각61pose 평가.80A8A67C 왼팔 투척·회복 확인. 원본 event에 프레임 정보가 없어 release는 동작을 바탕으로6틱으로 환산. 원작 확정 이벤트라고 간주하지 않음.

4. master 공통 수류탄 windup/release/recovery와 1P 스킨 팔·3P 왼팔 retarget, 점프 메뉴 7번째 항목 연결.
5. 실제 수류탄 8종의 자산 미리보기 검수. 이 PNG는 자산 프리뷰이며 Vision 실게임 증거가 아님.

## 검증
1차 중앙 targeted gate: ThrowTimeline 4 + JumpPhysics 22 + CharacterScreen 2 = 28/28 PASS, compileGametestJava PASS.

1차 격리 보통 dev server에서 W252 신규3개·W247 캐릭터4개 GameTest 모두 PASS. 처음 test command의 잘못된 좌표 인자는 문법 오류로 종료했으며 실행 결과로 세지 않는다. 정확한 test ID만으로 재실행했다.

Danmo4GB OpenGL + Vision8102에서 원본 native swap_offhand로 3직업 투척을 실행했다. 준비/발사/회복과 각 사운드 이벤트가 발생했고, 실제 PNG에서 FP 팔이 카메라에 지나치게 가까운 문제가 보여 z 보정과 복귀 blend를 추가했다. 3P 투척 PNG도 확인했으나 기존 유색 placeholder 몸체는 W250 미완료 범위이며 이번 유저 스킨 완료로 간주하지 않는다.

캐릭터 탭→점프→균형 활공을 native 회전 포인터/attack 입력으로 선택했다. 실제 PNG에서7번째 점프 카드와 옵션이 표시됐다. 카드의 변경하기 텍스트가 하단에 닿아 높이116에 맞춰 위치를 조정했다.

헌터 high/triple, 타이탄 리프트 on/off/restart를 native Space로 실행. Warlock은 상승 관성을 잃는 결함을 발견해 worker에 실제 trajectory를 전달했고 수정 대기. 점멸은 native Space 입력으로 glass wall 앞 z1003.625에서 멈춰 z1004 벽을 관통하지 않았다. 이 검증은 단위 predicate 검사가 아닌 실제 블록 충돌 실행이다.

1차 증거: /private/tmp/destiny-w252/qa/{gametests.json,native/,frames/,server.log}. 최종 수정 후2차 확인과 최종전체 gate는 아직 대기.

## 재현 자료
- `scripts/animation/sample_throw_w252.py`: 별도 headless Blender에서 원본 평가.
- `scripts/animation/build_grenade_throw_w252.py`: 평가 FK를 61pose FP 자료와 BetterModel 클립으로 변환.
- 원본 카메라가 추출된 것은 아님. FP 위치는 카메라 좌표로 별도 보정했고, 팔은 손가락 없는 플레이어 스킨을 재사용.
- 원작 이동 방식은 Bungie 공식 업데이트 1.1.4의 Lift/Glide 설명과 DDC를 대조. 정확한 MC 가속/속도는 원작 실측값으로 표시하지 않음.

## 플레이어 조작

- `/메뉴` 또는 인벤토리 열기 → 캐릭터 → 점프에서 현재 직업·하위직업에 허용된 점프를 선택한다.
- 헌터: 공중에서 Space를 다시 눌러 높이/제어 도약. 삼단 점프는 공중에서 두 번 더 누를 수 있다. 아크에서는 점멸도 선택 가능하다.
- 타이탄: 공중 Space로 리프트 시작, 다시 누르면 중단. 남은 연료 내에서 재시작할 수 있다. 높이/제어/탄도 리프트를 선택한다.
- 워록: 공중 Space로 활공 시작·중단. 상승 중 사용하면 기존 상승을 이어가고, 하강 중 사용하면 하강만 완화한다. 제어/폭발/균형 활공 및 공허 점멸을 선택한다.
- 점멸은 두 충전과 회복 대기 시간을 가지며 벽·천장·월드 경계를 통과하지 않는다. 착지나 메뉴·직업 전환으로 충전을 즉시 복구하지 않는다.
- 수류탄은 기존 F 키로 준비 → 발사 → 복귀가 이어진다. 실제 투사체는 준비 후 6틱에 한 번 생성되고 전체 동작은 20틱이다. 이 타이밍은 원본 모션을 보고 맞춘 MC 보정값이다.
- 현재 실제 리핑 모델은 Explosion/Pulse 두 종류다. 전용 모델이 없는 능력의 대용 관계는 [ripped-grenades.md](ripped-grenades.md)를 따른다.

6. 사용자 후속 지시: 없는 리핑은 추가 추출 대기 없이 스킵. 묶음에 있는 수류탄을 임시 대용한다. 큐브 재구성을 원본 사용으로 표시하지 않고, Explosion/Pulse 실제 메시·UV·Diffuse 변환을 슬롯4에 배정했다.

7. 사용자 임시 대용 지시에 따라 실제 Explosion/Pulse FBX를 headless Blender로 import·원본 world transform/UV/Diffuse 평가 후 decimate했다. 원본 삼각형846/1032→474/475, 실제 native 출력948/950요소. source UV diffuse 베이크와 적군 변형을 통합하고 --check 13산출물 재현 일치를 확인했다. 원본/제품 preview를 직접 검수했다. 이 자산 프리뷰를 Vision 증거로 세지 않는다. 자세한 provenance/대용 표는 ripped-grenades.md를 우선한다. 기존8종큐브는 비활성 보존.

8. R2 워록: 수직 관측과 수평 관측의 freshness를 분리해 패킷 공백·Y=0 수평 패킷이 상승 관성을 지우지 않게 수정. active GlideCarry는 자체 유한 상승 예산을 가지며 반복 관측으로 재충전하지 않는다. R2 standalone35와 중앙 targeted42(Throw4+Jump35+Pose1+Character2)/42 PASS, compileGametestJava PASS. 팔의 native head Y=-.5..0에 맞춘 관절·손목 연결 검사도 통과. 이 시점의 2차 실게임은 대기.

9. R2 실제 Danmo4GB/OpenGL 팩 로드와3직업 native투척·헌터triple·타이탄lift·워록rise/fall을 확인. 신규3+W247기존4 GameTest 7/7 재통과. 상승Glide는R1 즉시추락은 개선했으나 .018/tick감쇠로최고Y101.65735에그쳐수락보류. native screenshots와servertrace를담당자에전달해R3튜닝을요청했다. falling 첫시도 neutral10은착지경계라 falling증거로세지않고 fall-too-late-r2에보존, neutral7로재실행한낙하감속/재상승금지증거만사용한다.

10. R2 PNG에서투척중총잔상이남아 cosmeticgun만EMPTY로숨기고recovery시복원하도록보강. gameplayinventory교체없음. 모든 R2lease중립확인후client종료-2,server save-all/stop종료0. R3검증대기.

11. 모델담당읽기리뷰에서nativehead cap/sideUV 방향반전을확인. decl.fsh의내부cap제외조건과측면V를수정. FP시작/복귀는행렬직접lerp대신관절끝점·twist보간후직교팔행렬로재구성해shear를줄였다. 원본손목twist전체리타깃은아니며그립의미세회전은남은한계다. 이셰이더는기존FP팔에도적용되어R3에서대표무기hip/ADS/장전도함께확인한다.

12. R3 jump delta3파일을R2frozen기준해시와main일치검사후통합했다. 상승감쇠상수 .006/tick(MC초기튜닝),활성후작은양수관측으로carry를거듭깎지않고유한내부carry를사용. freshnegative와천장중단·하강시재상승금지는유지. worker standalone37/37. 중앙최종test build·R3Vision검증중.


## 전체 검사에서 발견한 기존 자산 불일치

최종 전체 `test build` 시도는 **2,198개 중 5개 실패**했다. W199 설치 버전명을 고정했던 검사 한 개는 W252의 새 모델 이름과 수류탄 전용 오버레이를 검증하도록 갱신했고, 이후 관련 **46/46 검사 + assemble + compileGametestJava는 통과**했다. 같은 전체 검사를 숫자만 맞추기 위해 반복하지 않았다.

다음 네 검사는 이번에 변경하지 않은 무기 자산과 과거 고정 해시·형상 계약의 불일치로 남겼다. 관련 입력 6개는 W252 시작 시 별도 워크트리에 복제한 기준선과 현재 main의 SHA-256이 모두 같았다. 원본 결과는 `/private/tmp/destiny-w252/full-gate-failures.json`, 비교 결과는 `unrelated-asset-baseline.json`에 보존했다.

- `WeaponSilhouetteW112AssetTest.currentSourceInputsAndAllOutputBytesMatchManifestHashes`: W123 manifest 고정 해시 불일치.
- `WeaponSurfaceW115Test.everyExistingAimGripInspectAndReloadPoseResolvesToExactlyOneReplacedGeometry`: W151 조준기 원본 고정 해시 불일치.
- `ReloadW168AustringerTest.exactSourceElementsAndUvPartitionWithoutDuplication`: 현재 본체와 과거 장전 분할 형상 불일치.
- `InsertW179MindbenderTest.canonicalBodyAndUvsExactAndConnectedHiddenShellBudget`: 현재 본체와 과거 쉘 삽입 자산 불일치.

이 네 건의 자산을 임의로 되돌리거나 검사를 제외·약화하지 않았고, 이번 능력 작업의 전체 검사 통과로 표현하지 않는다.


13. R3 실제 입력에서 상승 활공 최고 Y107.5333, 수평 상한 .63, 유한 연료 종료·착지 확인. 낙하 중 활공은 기존 낙하를 완화하고 재상승하지 않았다. R3 신규3+W247기존4 GameTest 7/7 재통과. 실제 수류탄 원본2종·적군2종을 나란히 표시해 native 팩의 기하/UV/붉은 구분을 확인했고 소유 fixture4개를 제거했다.

14. R3 투척 준비 때 실제 grenade가 손에 표시되고 발사 후 사라지며, cosmetic gun 숨김은 작동했다. 팔이 떠 보이는 현상을 원본 FK 투영과 직접 비교한 결과 관절이 끊긴 것이 아니라 **원본 어깨 끝까지 화면 안에 들어온 현상**이었다. native head down축은 유지한다. R4는 손목·팔꿈치 경로를 유지하고 FP 상완의 시작점만 화면 밖 카메라 어깨로 조정한다. 3P 원본 리그는 변경하지 않는다. 원본 FP 카메라 복원으로 표현하지 않는다.

R3 대표 Austringer의 hip/ADS/장전 캡처는 실제 PNG에서 메뉴가 남아 있었으므로 무기 검증으로 인정하지 않았다. R4는 영문 inventory close와 EquipmentScreen closed ACK를 확인한 뒤 다시 검증한다. Vision v1의 native Q 지원이 없으므로 서버 fixture 장전 시작을 실제 Q 입력 검증이라고 부르지 않는다. 음원은 이벤트 기록이며 실제 청취 검증은 하지 않았다.

15. R4 최종 FP 어깨 anchor는 (±.32, -.80, -.72)이며 손목/팔꿈치 FK 경로는 유지한다. 변경 후 GrenadeThrowPoseTest 2/2 PASS. QA 서버가 준비되기 전에 먼저 시작한 클라이언트는 Connection refused로 종료했고, 서버 팩 생성 완료 후 같은 소유 프로필로 다시 시작했다. 이 접속 실패를 렌더 검증으로 세지 않는다.

16. R4 Danmo4GB/OpenGL actual PNG에서 Titan/Warlock prepare→release→recovery와 원본 수류탄 prop, gun 숨김/복귀를 확인했다. 어깨 끝은 화면 밖이고 팔꿈치/손목은 연결돼 있다. Hunter 첫 연속 캡처는 일부 자세가 고정돼 보여 별도 50틱 neutral 재검수했다. 재검수에서 준비/투사체 비행/팔 회복/총 복귀 및 server throw=false age=20을 확인했으며 최초 캡처를 원인 확정 자료로 삼지 않았다.

17. R4 inventory close ACK와 실제 PNG를 확인한 뒤 대표 Austringer의 hip, 좌클릭 ADS toggle, 우클릭 발사, 서버 fixture 장전 시작·회복을 확인했다. 장전은 native Q 입력 검증이 아니다. side UV/cap 변경으로 관찰한 대표 무기 팔에 새 깨짐은 없었다. 전 무기·전 스킨 검증으로 확대 해석하지 않는다.

18. R4 actual framebuffer에서 Explosion/Pulse 및 붉은 enemy 4종의 기하·UV·구분을 확인하고 소유 item_display 4개를 제거했다. 최종 leaseActive=false, heldKeys=[], pendingSteps=0, native movement 중립을 기록한 뒤 QA client 종료 -2, QA server save-all/stop 종료 0을 확인했다. 새 점프 코드는 R3 이후 변경하지 않아 R3 원본 trajectory와 수락 결과를 유지한다.

19. 모델 담당자에게 R4 PNG와 Hunter 재검수 이미지를 전달했고 최종 FP anchor·기하/UV·normal/enemy 구분을 수락받았다. 추가 형식 수정 없이 freeze 유지. 점프 담당자도 R3 원본 trajectory와 동결 소스7개를 수락했다. 두 worker를 종료하고 슬롯1·4는 idle-needs-refresh/W252로 전환했다. 워크트리는 보존했다.

20. 최종 anchor를 포함한 assemble PASS. 최종 QA 캡처는 [투척 준비](throw-ready-r4.png), [투척 회복](throw-recovery-r4.jpg), [원본/적군 모델](ripped-normal-enemy-r4.png), [대표 ADS](weapon-ads-r4.png), [대표 장전](weapon-reload-r4.png)에 보존했다. 물리 수치는 MC 초기 튜닝이며 원작 절대속도·모든 스킨·모든 무기·청취 검증 완료를 뜻하지 않는다.
