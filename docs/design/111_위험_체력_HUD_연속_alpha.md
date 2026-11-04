# W96 — 위험 체력 HUD의 연속 alpha

**주변부 경계 부드러움만 한정 수락. 전체 HUD/무기 목표와 저체력 탄약 패널 가림은 미완료다.** [QA](../qa/2026-10-25/w96/README.md)

## 문제와 선택

W89 텍스처의 alpha1..25/255가 vanilla item `ALPHA_CUTOUT=0.1`에서 잘려 중앙에 딱딱한 타원 경계가 보였다. W90 대형 dither 후보를 채택하지 않고 기존 텍스처·모델·pulse24tick·HP30%진입·8bank 선택·배치·회복 제거를 그대로 둔다.

`IncomingDamageHud`는 critical ItemDisplayHud에만 brightness **block2/sky3**을 부여한다. native metadata3145760→UV2(32,48), 기존 above-hand1/2→(16,32)와 다르다. cache로 같은 모델을 재사용해도 marker가 없으면 설정한다. 다른 피격 arc/체력/흡수 HUD와 일반 무기는 이 marker를 받지 않는다.

`CriticalHudShader`는 Polymer pack converter와 preFinish task를 등록한다. 설치된 DisplayHUD vertex와 vanilla26.3 fragment의 전체 SHA를 검증하고, 실제 없던 fragment를 `getDataOrSource`→`addData`로 명시 materialize한다. 두 source를 먼저 검증하며 기존 override 우선권을 지킨다. 두 stage의 vacant location7 flat int로 `displayhud_is_hud(Position) && UV2==(32,48)`만 표시한다.

표시된 fragment는 **raw sampled alpha0만 discard**, 그 외에는 기존0.1 texture-cutout만 우회한다. 일반 branch는 원래 ALPHA_CUTOUT 조건과 비교식을 유지한다. 이후 color modulation/glint/fog/OIT와 geometry/depth설정은 변경하지 않는다. exact패치bytes만 반복 적용을 인정하며 unknown/partial/위조bytes는 거절한다.

## 실패와 출판 경계

Polymer는 converter예외를 catch해 null을 반환할 수 있고 path build는 옛 ZIP를 먼저 지울 수 있다. transactional publish가 아니다. 실제 최종 생성 ZIP의 shader SHA와 전체 entry delta를 검사해야 한다. vanilla `OIT_DEPTH_BOUNDS`의 calculated alpha<0.01 discard와 additive alpha-only discard는 그대로다. 모든 nonzero 최종pixel 보존이라고 표현하지 않는다.

최초 headless 비교는 오래된 normalserver BetterModel sample재고와 새 disposable fixture재고가 달라 거절됐다. [원본 실패/비교 기준](../qa/2026-10-25/w96/headless-baseline-review.md). 최종 native는 실제 W95nativepack에 대해 **item.vsh변경+item.fsh추가만** 허용한다. headless는 같은 native reference의 pinned optional projection제거까지 정확3entry 차이만 허용한 명시적 cross-mode 비교다. namespace 전체를 무시하지 않는다.

## 시험과 실제 화면

최종 강제gate2/3각 **818GT+699JUnit**, 기존815GT/689JUnit 보존·fail/error/skip0·20task강제실행·동일JAR. 신규10JUnit은 exactsource/64define interface/guard/preFinish, 신규3GT는 실제 HP6/5/1·cache/lifecycle·native PLAYencoded metadata/resend/다른HUD marker음성을 검증한다. 처음 새GT의 GameRules import오류는 실패 원본과 함께 보존했다.

별도 adapted glslang15pair compile/link도 통과했다. include확장, GLSL450/SPIRV OpenGL 및 gl_VertexIndex호환alias/자동binding변경을 명시하고 실제 engine OIT상수8/2/2를 사용한다. 처음 누락engine define에 의한6/15→9/15 실패는 보존했다. 이는 engine/nativeGPU 전variant 수락이 아니다.

취합 Vision은 의도적 headlesspackserver1+nativeFOVserver1, default/small serialclient2로 진행했다. 실제 **1708×960/854×480**, PNG113(86/27), master원본13+historicalW89원본1 직접검사. HP6/5/1/.01·darkHP1·native ADS/look1·회복20을 확인했다. 원래 bank0..7은 서버bracket에 나타났으나 exactrenderphase와 같다고 단정하지 않는다. 큰 딱딱한 inneroval 대신 부드러운 주변부/clearcenter·reticle·중앙ADS·회복제거를 수락한다. 원작D2정량/모든frame/ultrawide/다인/청취/성능 수락은 아니다.

## W96-N1 — 탄약 패널 가림 유지

저체력 대표에서 왼쪽 탄약 아이콘/숫자가 사라지고 패널 outline만 남는다. W89원본에서도 같은 질적 현상이 보이며, W96 회복 뒤에는 양해상도 모두13이 보인다. depth ordering은 가설일 뿐 원인을 분리하지 않았다. **이번 softness수정이 전체 HUD layer문제를 해결했다거나, 새회귀원인을 확정했다고 하지 않는다.** 다음 우선은 별도 가역 격리로 critical overlay와 ammo HUD의 render/depth관계를 확인하는 것이다. W93-N1특정상단활사각형/N3전용원음/N4피로정량/원작손IK/다인성능도 그대로 남는다.

일반 프로필/월드·전역MCP·영구전원·사용자앱은 보존하고 ownclient/server/caffeinate·lease·nativekeys·forceload를 정리했다. source8472pin/7013asset·JAR/생성pack/두 실제cache 감사는 시각검사와 별도 근거다.
