# W335 기본 클라이언트 궁극기 우클릭 전달

W333의 실제 서버 Fabric EVENT.invoker 검사는 통과했지만 W334 native에서는 궁극기 중 mainItem=air가 되어 우클릭이 전달되지 않았다. 지상3좌클릭/우클릭/좌클릭이4번 공격만 만들었고 공중 우클릭 단독은 공격이 없었다. 실패 증거는 W334/pre-transport에 보존한다.

## 원인과 수정

실제26.3 Minecraft.startUseItem은 air/block/entity 처리 중 공기 우클릭에서 main stack이 비면 MultiPlayerGameMode.useItem을 호출하지 않는다. 서버 handleUseItem도 실제 손이 비면 Fabric item callback 이전에 반환한다. 단순 서버 callback 호출은 이 두 경로를 검증하지 못한다.

기존 SwordHandPackets 보호 수명에 Arc/Spectral 전용 모드를 추가했다. 소유자의 선택 슬롯에만 실제 인벤토리와 분리된 보이지 않는 STICK을 마지막 패킷 표시 단계에서 보낸다. 소스 스택/오프핸드/커서/관찰자 장비는 소유하지 않으며 실제 아이템을 넣지 않는다. 메인 손 입력이 offhand로 빠지지 않도록 기존 무기 표시 계약의 무음·NONE-animation consumable만 사용한다. FOOD/탄약/Polymer 무기 소유 정보는 복사하지 않는다.

활성 자세·선택 슬롯·GUI/메뉴 변경을 main thread에서 캡처하고 Netty는 불변 snapshot만 읽는다. 경계에서만 현재 소스 슬롯을 갱신한다. 종료/취소 때 캡처해 둔 과거 무기를 되살리지 않고 현재 소스로 복귀한다. 일반 sword/능력 hand 보호 경로는 유지한다.

실제 서버 손까지 빈 경우를 위해 기존 packet listener mixin의 thread/load 검사와 ackBlockChangesUpTo 이후에만 MAIN_HAND+empty+opt-in secondary를 처리한다. 지원하지 않는 평소 빈손은 vanilla를 따른다. 강공격60틱/회피40틱/피해/모션 길이/사운드에는 변경이 없다.

## 검증

최종 실제 Gradle assemble/compileGametestJava 후 별도 fresh single-use Gradle 단위31개가 통과했다. 재사용 compiler가 invalid header field를 낸 초기 로그를 보존했고, JAR 생성과 test를 단계별 분리해 성공했다. 수동 javac 패키지가 아니다. JAR CRC 및 세 animation 리소스와 source 일치 확인은 build-validation.json.

패킷 단위14개는 기존12+새2이며 실제 empty/food/gun 스냅샷 보존, 선택 슬롯/GUI/상태 ID/오프핸드/커서/관찰자 격리를 확인한다. 실제 서버 회귀와 native 입력 결과는 최종 수락 후 아래에 추가한다.

실제 서버: 제품2개+프레임워크1개3/3통과(`gametest.xml`). 기존 강공격T60 경로에서 authoritative main hand를 비운 뒤 실제 connection.handleUseItem 패킷을 호출하고, 반복 패킷에도 단일 접촉과 실제 아이템 미생성을 확인했다. 보통 빈손/다른 궁극기/기존 block·entity·GCB 입력 경로도 유지한다. 최종 native 수락: wire mainItem=STICK/item_model=weapon_sword_hand_empty가 실제 클라이언트에 보존됐다. 실제 입력으로 Arc/Spectral 각각 지상5공격(3LMB/RMB/LMB), 공중RMB1공격을 확인했다. 종료 뒤 실제 crossbow 모델·self camera·usingItem=false·입력lease해제·HUD복귀를 확인했다. server clear maxCount0은 활성 super 중 실제STICK 없음으로 답했다. 상세 증거는 ../w334-articulated-super-motion/native-acceptance.json과 native/.

원본 배속·모션 길이·접촉 타이밍·사운드·강공격60틱·회피40틱은 변경하지 않았다.
