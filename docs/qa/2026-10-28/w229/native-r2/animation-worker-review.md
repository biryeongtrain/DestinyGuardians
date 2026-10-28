# W229 최종 native R2 아트 검수

판정: 제공된 이동·복귀·짧은 점프 시나리오에서 확인된 잔여 아트 결함 없음. 추가 animation delta 없음. 기존 fullbody hold로 이동 중 다리가 고정되던 문제와 Daybreak cast-frame-28 준비 자세로 돌아가던 문제는 이번 화면에서 재현되지 않았다. 형식적인 pose/키프레임 수정은 하지 않았다.

검수 입력은 `/private/tmp/destiny-w229-native-r2/frames`, `reviews/locomotion-review.jpg`, 해당 sequence JSON과 `oracles/*locomotion-during.json`, `*airloop-during.json`이다. 대상 sequence PNG 40장과 ready/returned-idle 8장, 총48장을 직접 이미지로 확인했다. 각 PNG SHA256·client tick 전후 bracket, oracle의 clip/ground/body 기록은 [evidence.json](/private/tmp/destiny-w229-animation/review/final-native-r2/evidence.json)에 보존했다. 원본 픽셀을 crop한 검수표는 같은 폴더에 있다.

배치 이름은 native R2지만 실제 설치 식별자는 `guardian_classes_w229_r3`이다. `server.log:138`의 21:32:39 설치 로그에서 `config/bettermodel/players/guardian_classes_w229_r3.bbmodel`을 확인했다. 리타깃 리소스는 parent-fix 기준이며 full JSON SHA256은 `c37d9e0ad7d6aac7fef19c3e2723e7c3d8fb9b360362aa0a00d9121279dfc1f8`이다. 이번 검수 시작/마감 시 최초 R2 동결6파일과 parent-fix 동결6파일의 해시 일치를 확인했다. 게임·서버·중앙 build·CU 실행이나 프로젝트 코드/animation 변경은 하지 않았다.

| 대상 | 직접 확인한 정확 구간 | 판정 근거 |
|---|---|---|
| Titan Arc | `titan-arc-super-locomotion-sample-00..08.png`, client874..899; ready866, returned909..910 | 02~04와06~08에서 앞으로 나온 다리가 바뀐다. 상체는 authored ready를 유지하며, 정지 후 양다리 ready로 돌아온다. 붙박이 하체·독립적인 팔/다리 이탈·뚜렷한 회전 반전 없음. |
| Titan Solar | `titan-solar-super-locomotion-sample-00..06.png`, client1148..1174; ready1137..1139, returned1189..1191 | 01/04의 통과 자세와02/03/05/06의 stride 자세가 달라지고 좌우 다리가 교대한다. source recovery에서 취한 기울어진 상체는 유지되지만 하체가 그 자세에 고정되지 않는다. 오른손/팔에 대한 망치 shaft·head 관계가 이동 내내 유지되며, 정지 후 같은 carry로 복귀한다. |
| Titan Void | `titan-void-super-locomotion-sample-00..06.png`, client1451..1477; ready1442..1444, returned1489..1491 | 01/02와03/04에서 들린 무릎·종아리 방향이 교대하며05/06에서도 움직인다. 원본 Sentinel sprint 하체의 큰 knee flex가 보인다. 방패는 왼팔 carry에 유지되고, 정지 후 양다리가 ready로 돌아온다. 하체가 torso와 별개로 떠서 따라오는 현상이나 한쪽 다리의 고정은 확인되지 않았다. |
| Daybreak 지상 | `warlock-solar-super-ready.png`, client2157..2159; locomotion00..06, client2168..2194; returned-idle2207..2209 | 준비 cast의 팔을 머리 위로 든 f28 hold로 돌아가지 않는다. 팔꿈치를 굽힌 별도 sword carry를 유지하며 다리는 통과/앞뒤 stride로 바뀐다. 오른손 부근의 grip/guard와 세운 칼이 상체에 함께 붙어 있고, 지상 이동 뒤 returned-idle이 ready와 같은 carry로 돌아온다. |
| Daybreak 공중/착지 | `warlock-solar-super-airloop-sample-00..09.png`, client2216..2253; 실제 체공 핵심01=2220..2222, 02=2224..2226 | 01/02는 body Y가65보다 올라간 상태에서 접힌 glide 다리와 sword carry가 함께 보인다. 칼만 남거나 몸체/하체가 분리되는 현상, overhead cast pose의 재등장은 없다. 03은 이미 착지하는 경계이고04는 지상 이동 회복,05~09는 원래 carry idle로 안정된다. |

다섯 oracle 모두 대응하는 loop 선택을 확인했다. Titan3종과 Daybreak 지상은 `_idle → _move → _idle`이며, 이동 중 body Z가 실제 증가한다. 입력이 해제된 뒤에도 관성 변위가 남는 동안 move가 이어지고 정지하면 idle로 돌아오므로, 이 구간을 입력 해제 즉시 idle로 돌아오지 않는 결함으로 분류하지 않았다.

Daybreak air oracle은 21:35:08의 `ground=false`, `limbClip=w229_warlock_solar_air`, body Y66.176759 기록을 포함한다. 같은 수집 구간의 점프 직후에는 ground=false/idle 한 행도 있지만 다음 행에서 air가 확인된다. 별도 clock의 oracle 수집 순서로 정확한 selector 지연 tick을 추정하지 않는다. 이어 ground=true/move를 거쳐 21:35:09~10의 idle로 복귀한다. client 측 player는 camera/vehicle 구성 때문에 onGround=false가 계속 기록되는 구간이 있으므로, 모든 airloop PNG가 실제 체공이라고 판정하지 않고 서버 ground/body Y와 이미지의 자세를 함께 봤다.

`warlock-solar-super-returned-idle.png`는 client2207..2209로 airloop 시작2216보다 앞선다. 따라서 이 PNG는 **지상 이동 뒤 복귀** 근거다. **공중 뒤 복귀** 근거는 airloop05~09 및 air oracle 후반 idle 기록이다. 이 둘을 혼동하지 않았다.

맨 뒤에서 본 블록형 팔/다리의 회전 경계, Sentinel의 깊은 무릎 굽힘, Daybreak 칼이 머리 옆으로 지나가는 실루엣은 보이지만, 확인한 프레임 사이에 갑자기 분리되거나 뒤집힌 별도 결함으로 판정할 근거는 없다. Hammer 오른손·Shield 왼팔·Sword 오른손의 장비 관계도 유지된다. 이 후면 화면에서 손가락 단위 파지나 숨은 면의 정밀 접촉까지 인증하지는 않는다.

이번 수락은 제공된 pose·carry·이동 전환의 시각적 결과에 한정한다. Daybreak의 source는 여전히 **전용 Daybreak idle로 확인되지 않은 일반 sword_catch_idle80A8B370의 임시 적용**이며, air는 일반 Warlock glide 하체 조합이다. TitanSolar/Daybreak ground 다리 및 TitanArc idle/move의 명시 authored provenance도 유지한다. 화면이 양호하다는 이유로 이들을 전용 super 원본 rip으로 재분류하지 않는다.

공중 선택은 짧은 점프의01/02 두 핵심 프레임으로 확인했으며, 2초짜리 air source 루프 전체를 장시간 체공으로 한 주기 검증한 것은 아니다. PNG는 대체로3~4clienttick 간격이므로 61pose가 native60fps 연속 보간과 같다는 주장도 하지 않는다. 기존 start/attack의 최대 약8.7도 midpoint 근사 한계, contact:null/미해독 이벤트와 product provisional 적용값, Hammer audio frame15 타이밍 근거는 이번 이동 검수로 변경되지 않는다.

잔여 결함의 정확 구간: **확정된 수정 대상 없음**. 위 짧은 체공 범위와 후면 시야는 검증 범위의 제한이며 신규 결함으로 등록하지 않는다. 기존20clip과 companion metadata는 추가 변경 없이 유지한다.
