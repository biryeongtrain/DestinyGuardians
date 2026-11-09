# Energy delegated first native review

Reviewed actual first-{sunshot,graviton_lance,jotunn}-{hip-0,third,ads-end-0,reload-valid-0..4} PNGs in /tmp/exotic-expansion-20261109/qa/native. Geometry/materials load. Sunshot cylinder/crane and Jotunn top-cell/hand motion plus return appear in valid samples. Graviton valid2/4 resemble idle; sparse captures alone do not establish its complete reload animation.

Confirmed defects: all ADS sight lines low despite horizontal centering; Graviton/Jotunn third-person muzzles vertical under crossbow hold. Corrected ADS physical anchors: Sunshot front iron top11.46, Graviton aperture center13.9776, Jotunn clear rear-plate top14.22. Master-confirmed camera base(+0.56,-0.52,-0.72)m gives translationX=-8.96 and Y=8.32-scale*(height-8); all projected anchor Y=0 analytically. Recomputed21 aim samples and matching hands. Graviton/Jotunn -Z muzzle basis matches accepted krait_twohand rotation[5.729578,-17.188734,0], translation[0,-2,2], scale0.7. Sunshot pistol third stance preserved.

Native-first corrections change display/aim/hand transforms only. Geometry, textures, reload motion and shared runtime/HUD unchanged. Master output-only1024 cap preserves owned authored2K atlases/proofs. Aim endpoint agrees within1e-7; reload endpoints still identity. Second native Vision remains required for actual aim/third-person/grip/return acceptance.
