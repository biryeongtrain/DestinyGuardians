# W350 kinetic exotic models — first offline handoff

Exclusive worker checkout; no shared registry or main changes. No game client/server operated.

## Source evaluation

Actual .blend files were opened read-only in owned background Blender5.4 with autoexec disabled. Source hashes, materials, mesh counts, bones and action slots are in each art/weapons/w350/<id>/source-evaluation.json. Source side/oblique/top and material-color PNGs accompany them. All three have zero actions and no player wrist/elbow rig. Crimson has no armature; Thorn has Cylinder/CraneRotate/CraneExtend/Magazine/Trigger/Hammer; Outbreak has Pedestal/Magazine and two unresolved hash bones. No original reload or extracted hand trajectory is claimed. Outbreak supplied shader renders grey/white; official default inventory icon confirms the reconstructed black/red palette.

## Product

Crimson96,Thorn156,Outbreak118 solid elements, each512x512atlas. Semantically adjoining blocks preserve blade, drum, wrapped grip, open barrel windows, SIVA chamber banks and open lower frame. UV palette has material roles and1texel edges. No source mesh conversion or alpha sideplate body. W204 immutable player-color arm parents are reused with exclusive per-weapon pose leaves. Weapon+two classic forearms stays below1000elements.

Root items destiny:weapon/<id> show hip at idle, string0 ads/inspect/reload selectors, and non-first-person full-model fallback. Reload dispatcher destiny:weapon_reload_w350/<id> uses float1with61thresholds; frame aliases append /0../60. Aim dispatcher destiny:weapon_aim_w350/<id> uses float3with21thresholds. See per-weapon integration.json for identifiers. Skin color flag8/9 and RGB offsets64/192 require master carrier skin projection.

Reload is authored shape-preserving C1 Hermite body lift plus cylinder hinge/extractor for hand cannons or downward removable rear magazine for Outbreak. The same transforms carry block-arm contact frames.61poses are a discrete model bank, not proof of60fps continuous client interpolation. Local rig.json records each pose and source-binding limits. ADS translations and all hand contacts await native review.

## Performed / outstanding

Performed: valid JSON, positive bounded solid boxes, unique names, normalized UVs,61pose endpoint equality and bounded angular steps, source hash unchanged, side/oblique/top/front offline renders and exterior coplanar review. Static graph references checked separately in validation artifact.

Pending: native pack load, first-person grip, left/right variants, ADS occlusion, reload contact and return, third-person appearance,10–20display behavior, sound timing/listening. Master first Vision → delegated review/fixes → master second Vision required before acceptance. This is an offline handoff, not a completed visual acceptance.
