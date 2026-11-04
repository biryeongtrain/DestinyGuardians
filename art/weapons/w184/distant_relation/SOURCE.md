# Distant Relation W184 original gameplay and authored reload

Original source: DFP, [The Gambit Scout Rifle! Distant Relation - Destiny 2 Forsaken](https://www.youtube.com/watch?v=4SvDoK8HidQ), uploaded 2018-09-22. Original 1280x720, 60/1 fps, timebase 1/15360, retained video/metadata/exact PNGs in /private/tmp/w184-distant-report. Sequential ffmpeg select(n), no approximate seek; PTS=n*256. Identity inventory n300/5s says DISTANT RELATION and matches the distinctive stock/thumbhole/lower loop, exposed action, short optic and muzzle. Source has white shader; canonical default dark teal/walnut paint remains unchanged. Tactical reload HUD7->17 is evidence of motion only: local capacity16/RPM180/reload44ticks/sounds preserved.

Viewed original inventory, source contact sheet and full n20094/n20118/n20124 frames BEFORE authoring. Chosen action n20070..20184, 334.500000..336.400000s, with pre/post context retained. Visible: abrupt steep lift on right, rear-understock release, dark intact outgoing box downwards, incoming fluted box from lower-left, seat covered by palm/stock, fast lowering and a small settling dip. No independently resolved bolt stroke: bolt_slide/stem/knob remain fixed. No invented sounds, bullets, loose mechanism, bolt stroke or hand mesh.

Canonical geometry is weapon_surface_w123/distant_relation.json (88 solids), not legacy family geometry. Magazine indices58/59 are magazine_body + magazine_floor; remaining86 stay body. Both original elements/faces/rotations/UV and every non-element field remain exact. They move as one rigid payload.

Reload-only upper neck: one cuboid named magazine_shaft_upper, unrotated authored bounds [7.73,6.80,11.50]..[8.27,7.00,13.00], dimensions .54 x .20 x 1.50 model units, same original magazine_body origin [8,6.69,10.72] and X=-54.39546601956689 degrees. Overlaps original magazine tip and extends into filled lower stock, reusing original magazine_body face UVs/default paint. No new atlas. Its narrow hidden-neck dimensions are authored from the visible incoming long box (n20118), not extracted mesh or measurable occluded feed lips. All dense sampled neck points are enclosed by original magazine/stock solids when seated; endpoints dispatch exact canonical graph without added neck. Active assembly86+3=89<=1000; canonical endpoints88. Canonical flutes already exist in face UV; no arbitrary added ribs. This is a complete represented moving magazine, with authored hidden neck; exact original shaft proportions/feed interface fidelity and native hand fit remain unverified. Do not call exact shaft fidelity complete.

Trajectory was authored after source inspection, independent of W183 motion. W183 contributes rigid matrix composition, guards, renderer and parser/JOML testing patterns only. Pivot[8,8.55,8.30] is canonical hand-contact region; magazine anchor[8,6.69,10.72]. Normalized phases: reach/lift0..20%; withdraw20..32%; exchange32..44%; incoming44..60%; seat60..66%; fast lower66..82%; settling dip82..92%; recover92..100%. Peak carrier75X/9Y/-12Z, extraction[.20,-4.50,-3.10] follows down/forward direction of slanted rear magazine with authored lateral bias. Same single magazine proxies outgoing and incoming; invisible exchange identity is authored. No scale hiding. Hidden path, numeric angles, translations, phase ratios, shaft dimensions and exact recovery are authored interpretations. 21 samples every2.2 local ticks retain44tick clock. Source enhanced speed/perks/view motion do not set gameplay timing.

Both FP hands and native/twohand displays use equal unchanged scale. float[1] normalized progress; boolean[0] grip. ADS/inspect string[0], negative progress and nonFP select exact canonical graph. At0/1 entire canonical item graph is selected, and unreachable endpoint children also retain exact accepted displays.

Comparison and storyboard are OFFLINE / NO HANDS / NOT NATIVE. Multiple obliques, common-scale movement, rigid magazine detail and both hands/grips are CPU rasters decoded from emitted JSON. Source/model views have independent framing; no pixel tracking, native success, hand IK, audio listening or performance claim. Master owns routing/admission/runtime/native gates.

Video SHA256: 31e1cd1ac852620de4bab761a6ffa86b35eb429bbb40bd4082859dec643f88ea
Metadata SHA256: c38a003682c88d3f320e895a57683fa4c20fa5994e82c6d3540134b06dae6965

|Frame n|PTS|Seconds|p|Observation|PNG SHA256|
|---:|---:|---:|---:|---|---|
|300|76800|5.00000000|0|Inventory explicitly DISTANT RELATION; same thumb-loop stock, open lower hand loop, exposed action and short box optic. White shader differs from canonical default paint.|5982f184a9b772e2e687b891583f31397c292ecce77bd970cc96b7cc387a94ae|
|20064|5136384|334.40000000|0|Pre-reload hip presentation after firing; HUD7.|a43ce6efd9166a9c97d0de568fcf4de73d0f8f226d6e834ece62905cdf133226|
|20070|5137920|334.50000000|0|Last pre-lift hip pose.|74029a1f3281bfe2a36d2fe92439a8f5227097de26b347bea3068130af71bee3|
|20076|5139456|334.60000000|0.1|Rapid lift/cant, receiver at right; support hand leaves fore-end.|d59e4681802c38cca8b54aaee17bb8ef723acb126ff5433854dd3b707dfe1136|
|20082|5140992|334.70000000|0.2|Steep muzzle-up hold; rear-understock magazine access, right hand remains at grip.|437868db7257f0e6a59f9e11f094fb426ec3de618319cbb1cee51623ade815cb|
|20094|5144064|334.90000000|0.3|Outgoing intact dark box magazine visible below stock; support hand/edge conceal extraction origin.|775f471c4bae8854635bcfa083d66ffc6af49903f474c5f8657cc37797dad005|
|20106|5147136|335.10000000|0.4|Rifle held up; exchange below frame, exact hidden path authored.|d5d94977e03c2b15ea5745d4ad738c84cb1cc6c454249a92d207d534f6d07e11|
|20118|5150208|335.30000000|0.5|Incoming long rectangular magazine with fluted broad face rises from below-left in support hand.|dd6b4ad4ec8b179b019b671459b316992d3c17e5fa8f9ca317a7e488649cc3df|
|20124|5151744|335.40000000|0.6|Incoming magazine approaches rear-understock seat; upper tip and final lock occluded by hand/stock; HUD17.|529b1659a61f794cebd478e5946f22e221571c87480f6ee3b601a7f7b78b3836|
|20130|5153280|335.50000000|0.65|Support palm covers seating area; entire magazine returns to stock.|628879edfe3c6360223d38008df8f79731d3e2ccd7b7d5506251d2d14cfb9f42|
|20136|5154816|335.60000000|0.7|Carrier begins lowering; support hand obscures rear underside.|a66b6232a40204071df98d00c87ac9468e7f29e679ca5ab27d68dd1bea6d853f|
|20148|5157888|335.80000000|0.8|Fast lower from upright presentation; support hand moves forward.|b0e5f490e85ab446f6e6ada3b00f683b057e4e2049519ddc1ac9a119c713d082|
|20160|5160960|336.00000000|0.85|Support hand advances; receiver settles.|01eb8dd009154b2a522490030ff40799386e3a7b7ccad7a23d9b948cd55dc588|
|20172|5164032|336.20000000|0.9|Further small downward settling motion.|712593a492b727f7e00699bfe5fdf942d0450175a9413d8f2097fa4ecd28432d|
|20184|5167104|336.40000000|0.95|Small settling dip; source player also moves view downward.|548fa648b8766c8987c1bebd97aca8509f159c069882d841f077943458d9042e|
|20208|5173248|336.80000000|1|Recovered hip presentation before switching weapon; exact local endpoint authored.|b5af7321a27e7704954aaad1afc34baf449f7b033b0d3dcc028b6c51342fa0e0|
