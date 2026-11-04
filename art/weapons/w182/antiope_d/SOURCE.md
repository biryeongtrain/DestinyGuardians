# Antiope-D W182 reload source

Primary motion footage: [CammyCakes Gaming, The Perfect Antiope-D does exist!](https://www.youtube.com/watch?v=M3tC-IkkFRU), published 2019-08-04. ANTIOPE-D inventory at10.00s; continuous gameplay reload99.65-101.00s. Actual720p60 decoded frames inspected, not thumbnail or another weapon reload. Frame n/60, exact ffmpeg select(n). Raw video, info JSON, extraction command and full frames are external at /private/tmp/w182-antiope-report/.

## Identity and action

Inventory label + Hakke wordmark, compact box receiver, orange rear cap, vertical foregrip, pistol-grip-fed magazine, short muzzle and side tube establish Antiope-D. Action clip uses an alternate gold/red shader and holo sight; preserve canonical pale/gray/orange atlas and iron sights. Do not infer API item hash or roll from footage. Video HUD16->26 is not local capacity30. Video reload speed/perks do not alter local46ticks,600rpm or audio.

Order: leave ADS -> sharp muzzle-up rolled extraction -> empty pistol-grip socket presentation -> incoming complete magazine rises into grip -> positive seating impulse -> open support hand recovers forward -> hip. Source hand/screen edge occlude exact exchange; numeric poses, pivot and7.4-unit downward clearance are authored interpretation. Single intact magazine proxies both outgoing and replacement. No scale-hide, duplicate loose rounds, separate cartridge animation or extracted bones. Partial reload does not establish a distinct charging-handle stroke; handle remains fixed. Empty-reload-specific bolt handling is not established by this source.

## Canonical geometry inspection

Read weapon_surface_w123/antiope_d.json before authoring:118 existing cubes,708 face UVs.113 body includes continuous upper/lower receiver, orange cap, stock/brace, hollow sights/muzzle, grip/trigger guard, foregrip, side cylinder/optic and fixed charging handle. Five overlapping magazine_core/front_spine/back_spine/floor/pull_front cubes form ONE complete magazine extending below pistol grip. Preserve every element record, axis/angle, UV, texture slot, dye and scale. No redesign, extra geometry or triangles. Canonical grip_core/grip_heel are solid cuboids, so removing the magazine exposes the existing solid grip underside: this asset implies an empty grip-fed well but does not reproduce the source cavity/interior. No new socket faces or internal mechanism are fabricated under the geometry-preservation constraint. Assembled118=113+5 (cap1000, not a target). Alternative canonical full model is not counted twice.

Read minecraft-weapon-art-design/SKILL.md and references/ace-izanagi-study.md: semantic large solids with face UVs; preserve depth/identity.79/87 example counts are examples, not targets. W180/W179/W181 supply generator, matrix, codec and QA patterns only. No other weapon motion or source frames used.

## Runtime API and limits

Model destiny:weapon_reload_w182_antiope_d/antiope_d.21 samples i/20; custom_model_data floats[1] progress, booleans[0] twohand. Both FP hands. strings[0] ads/inspect branches and non-FP/inactive graph exact canonical. Endpoints0/1 exact canonical displays for each grip; no scale change. Master routes/admission/lifecycle, not this worker. Existing ammo30,reload46ticks,rpm600,cadence2,burst1, audio and existing QA untouched.

comparison.png is independent textured CPU reconstruction from emitted JSON, axis/angle handling and both mirrored FP contexts, not native pixels. storyboard.png pairs actual frames with independently reconstructed authored poses; common model framing, not a camera registration or pixel-equivalence claim. No rendered hands/IK, no new third-person reload, no native/audio/performance claims. Numeric hidden path and hand contact require master native review.

## Retained source hashes

Video720p60 SHA256: b0949a310d8791e978b47fc46a8347c5c893693ef02c161618a27fe5307c28e8

Metadata SHA256: df24dca45363d90d4deeccbfea169f0a61532d6e079ed3bc610cee94e8338665

| actual frame | seconds | decoded n | SHA256 | observed action |
|---|---:|---:|---|---|
| reference-01.png | 10.00 | 600 | c6d8387fff1f1063111a1f18e591ed69c31151e8f4e8e48342174a496e8dc9ff | ANTIOPE-D nameplate, Hakke branding, pale receiver, orange rear cap, vertical foregrip, narrow grip-fed magazine; inventory identity only. |
| reference-02.png | 99.60 | 5976 | 81f304aa1db62aa4f6e0defeb1792beef2e8b393e6b69c6d0b156f35c391d82e | Final ADS shots before reload; HUD16; same narrow barrel and side optic visible. |
| reference-03.png | 99.70 | 5982 | f94e8bf6ea5aca6ccdbdb09dcfc1b35f0c5ea926ed27a50f64bfb98ac31bf000 | Leaves ADS and lifts/rolls receiver to expose underside of pistol grip. |
| reference-04.png | 99.80 | 5988 | e35e6b6bee649e2e1d35e8af0691c18d475adae0f4bf925f6cf6d983ca27bd4d | Sharp upward presentation; support hand carries withdrawn magazine below grip; receiver partly exits upper right. |
| reference-05.png | 99.90 | 5994 | 3c52630000a38a76ed935eabd332ed76930e1099406f1695b31622b5ee0c242e | Receiver settles into rolled presentation; grip socket exposed, magazine out of view. |
| reference-06.png | 100.00 | 6000 | 3c41fdc862dd0a903fd410147237f8007b2acc88ac5fa707dca84e434229d0bf | Clear magazine socket held; support hand out of view. |
| reference-07.png | 100.10 | 6006 | 3ea2aebe378b2e61c7c169700991f94cd9fbed385323c327d17e4ba8bce5f9e6 | Rolled receiver holds; grip-fed socket still exposed. |
| reference-08.png | 100.20 | 6012 | bb92114a29ec7245c021c8a5976b3c9efdda3986efb6ea1dec89983437fac887 | Support hand starts returning below pistol grip; replacement approach begins. |
| reference-09.png | 100.30 | 6018 | b42ab229eefcb88c1c280c490115a252bc4c7c2e7d50175da0c2d9f6efa9a648 | Replacement magazine rises toward bottom of grip; top of magazine enters socket. |
| reference-10.png | 100.40 | 6024 | f3381c696c748c3915dd4d07cf2caec3adab944f7257802678a34d69c8629799 | Support hand presses magazine into pistol grip; receiver lifts with seating impulse. |
| reference-11.png | 100.50 | 6030 | 0b0f40cb6147596f32ef47f0b67eeee4b850be7a520627fa6ed97686d53cebe0 | Magazine seated; HUD26 and Kill Clip appear; support hand releases below grip. |
| reference-12.png | 100.60 | 6036 | 4876e7f6e4cc9fb409909ac47e204f6bd3cf3c66c21b43fd90e1d828b58cd0b3 | Open support hand moves forward away from magazine toward foregrip. |
| reference-13.png | 100.70 | 6042 | 7833be02ab03c5f0e38235f601e077d3530a34ea699bcb75801196f072c212e6 | Support hand passes forward as muzzle lowers; no separately measurable charging-lug stroke. |
| reference-14.png | 100.80 | 6048 | b37ed72658d5cca759ddc24b058230c1e584ebfc3e4e3427d42dac57cd521d14 | Foregrip recovery and receiver lowering toward hip. |
| reference-15.png | 100.90 | 6054 | 861439475ee1cfed331bb82342d1fb525f1077ab99f85e08cb49104632308d71 | Receiver settles; complete magazine remains seated. |
| reference-16.png | 101.00 | 6060 | fb5a81ac0665e61f4d3274a808d05756d22d2c831523ad9a3e6900edf958a957 | Ready hip view recovered with complete magazine and same Hakke receiver. |
