# W192 Well-Rounded

- 사용자 지정 DDC Perks 행 246: 수류탄 사용/강화 근접 적중 1중첩, 궁극기 사용 2중첩. 15초, 최대 2중첩, 중첩당 사거리·안정성·핸들링 +10. 추가 유효 이벤트가 시간을 갱신하며 무기 교체 중에도 유지된다. 강화 버전 제외.
- `source.json`에 정확한 HTML 행·입력 SHA256·Bungie 기본 특성 정의와 5개 무기의 실제 소켓/랜덤 풀 증거를 보관한다. 전체 manifest를 새로 수집한 것으로 주장하지 않는다.
- 생성: `rtk proxy python3 scripts/build_well_rounded_w192.py --root <repo>`.
- Minecraft 대응: AbilityService의 성공한 수류탄/궁극기 활성화·자원 지불 뒤에 반영. 시도/실패/쿨타임 거부는 제외. 강화 근접은 실제 직접 HP/흡수 체력 감소가 확인된 대상마다 인정하며 DoT·일반 근접·월도는 제외. 동일 접촉 token/대상 중복은 무효.
- 원본 ItemStack·소유자·월드·GuardianData/runtime/class·선택 소켓을 검증한다. 보통 stow/궁극기는 타이머를 보존하고 사망·분리·드롭·소켓 변경은 폐기한다. query는 상태를 생성/갱신하지 않는다.
- 핸들링은 기존 W43/W46 역사적 근사식이다. 합법적으로 동시 선택 가능한 Pugilist/Adrenaline Junkie/Frenzy/Threat Detector의 활성 보너스를 합산한 뒤 100 상한, 원시 초 계산, scalar, tick 올림 1회. Mindbender의 Snapshot entering scalar .8 보존. 들어오는 무기는 실제 selection 경계에서 원본 소유 스택의 Threat Detector 범위를 샘플링해 ready 계산에 보존한다. query는 스캔하지 않고 나가는 무기의 상태를 빌리지 않는다.
- 단순 수치별 테스트를 신설하지 않는다. 상태 만료/발동은 묶음 검사, 수치는 출처와 실제 사거리·안정성·핸들링 적용 경로를 확인한다. Vision/실제 키 입력 검증은 이 배치의 수치 변경에 요구하지 않는다.
