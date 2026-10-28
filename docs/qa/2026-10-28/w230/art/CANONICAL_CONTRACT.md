# W230 최종 canonical / R1 frozen

모든 item ID는 `destiny:class_ability/<class>/<super-or-extra>`이며 enemy는 마지막에 `_enemy`를 붙입니다. 이 문서가 EARLY_CONTRACT의 초안 치수보다 우선합니다. `16 raw units = 1 block`, NONE context에서 display center `(8,8,8)`가 holder origin입니다. 실제 bbox는 integration-manifest의 models.*.bounds / evidence/model-summary.json 참조.

**손장비 허용:** hunter의 기본4종, titan/burning_maul, warlock/well_of_radiance_sword_hand. base well/ward/chaos/nova/thundercrash는 field 전용입니다. ClassAbilityEffects.item(well)의 field 의미는 유지하고 equip만 별도 `_sword_hand`로 선택하세요.

| path (class_ability/ 뒤) | 역할 | 요소 | anchor / axis / scale |
|---|---|---:|---|
| hunter/blade_barrage | hand/projectile | 66 | palm(8,8,8), +Y blade, +Z broad face; NONE raw length .733 block; thirdperson scale1 |
| hunter/spectral_blades | hand | 66 | same palm and axes; one knife per hand, do not equip a pair into one hand |
| hunter/gathering_storm | hand/projectile | 140 | center palm(8,8,8), +Y length, endpointsY=-4.6903..20.6903; raw length1.5863block, displayscale1 |
| hunter/gathering_storm_embedded | field | 140 | lower tip(8,8,8), +Y, topY31, scale1 ->1.4375block. Distinct ground anchor |
| hunter/storms_edge | hand/projectile | 68 | palm(8,8,8), +Y blade,+Z broad face; raw length .7366block |
| titan/burning_maul | hand | 85 | lower palm(8,8,8), +Y shaft,+X head long axis,+Z broadface; model length1.802block |
| titan/burning_maul_wave | field | 38 | floor root(8,8,8), +Z advance,+Y flame height; footprint includes back toZ6.15 and reachesZ23.316; raw width.619,height.631,length1.073block. Scale(1,1,1) initially, translate along aim separately |
| titan/ward_of_dawn | field | 176 | floor center(8,8,8), nominal XZ radius8raw and height8raw. NONE scale(2R,2R,2R) -> approx radius/heightR; outer panel corners extend1.9percent beyond nominal. Visual does not define collision |
| titan/thundercrash | field body aura | 69 | center(8,8,8), +Y body up, branching arc shell. NONE scale1..1.4, holder center player.position+(0,.9,0). No sphere radius contract after replacing lattice with discharge |
| warlock/well_of_radiance | field | 156 | floor center(8,8,8), nominal XZ radius8raw. NONE scale(2R,1,2R)->radiusR; thin field with real open interior |
| warlock/well_of_radiance_sword | field planted sword | 211 | lower blade tip=(8,8,8), +Y from blade tip to hilt; rawheight23.2/16=1.45block. NONE scale1; scale1.2 ->1.74block, tip remains ground anchor. Do not share well radius scale |
| warlock/well_of_radiance_sword_hand | hand | 211 | palm=(8,8,8), blade+Y,broadface+Z. W229 right/left thirdperson display rotation0,translation(0,2,0),scale1. Hand variant not inverted; different geometry anchor from planted sword |
| warlock/chaos_reach | field beam | 50 | beam origin=(8,8,8), +Z nominal16raw=1block. NONE scale(width,width,lengthBlocks), aim quaternion rotates +Z to direction. Core radius.31raw, outer knot radius.774; extrema slightly overlap nominal endpoints by .011raw |
| warlock/nova_warp | field charge aura | 69 | center(8,8,8), broken tilted orbit ribbons and charge arcs; nominalvisual radius~7.3raw. NONE scale2R produces roughly.91R displayed radius. Not a collision sphere |

## 조합 / 예산

- 빛샘 field156 + planted sword211 = 동시367요소 / 2개 display. 시전 중 hand sword211은 대체 시점이며 필요시 동시 표시해도578요소.
- 스펙트럼 쌍칼: 같은66요소 모델을 각 손에1개, 총132요소. _enemy는 관전자 선택용 대안이므로 일반색과 중복 합산하지 않음.
- Gathering hand140과 embedded140은 phase 대안. Maul hand85와 wave38을 같이 표시해도123요소. 모든 단일 모델50..211(groundwave38 포함)로1000미만.
- 최소 갱신은 display 전체 교체보다 holder transformation/translation을 이용. 애니메이션·타이밍·시전·피해·관전자별팀분기는 master/runtime 소유.

## HUD

정확10종: `destiny:gui/hud/w230_<super>`와 assets/destiny/items/gui/hud/<동일이름>.json. W229와 동일한 64x64 RGBA 흰 silhouette와 minecraft:custom_model_data index0 tint; default16777215. 원작 공식 sprite 추출본이 아니라 자체 그린 구분용 아이콘. HUD는 로컬 사용자 컬러이므로 별도 enemyHUD를 만들지 않음. 3D14종 모두 normal/red를 포함함.

## 원본/임시 구분

원본5blend 직접 확인과 전체 한계를 README 참조. 자체 모델링인 spectral knife와 GPU VFX 대체물을 ripped mesh라고 부르지 말 것. 기존 원본40animation의 존재는 모든 공격/이동/종료/VFX source를 확보했다는 뜻이 아님.
