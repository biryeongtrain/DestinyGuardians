# Hollow Words W185 whole-cell reload

Actual reference: [Ironworker Gaming — HOLLOW WORDS Destiny 2 PvP Weapon Review! A Solid Precision Frame Fusion for the Crucible!?](https://www.youtube.com/watch?v=ozOSAOr5T4c), 2020-07-08.

Inventory frame6900 explicitly names HOLLOW WORDS. Continuous original gameplay frames11204..11348 (186.733333..189.133333s) show steep muzzle-up/right-edge carrier presentation, underside support-hand reach, low/offscreen cell exchange, palm seating, wrist roll and fast lowering. Fixed triangular grip, heel, brace and rear strut remain attached. Original cell shaft/release are partly concealed by hand and screen edge; no exact extracted animation, bones, hidden mechanism or measured hand IK is claimed. Source HUD1 +4 reserve becomes5; local capacity6 and50tick reload remain unchanged.

Canonical W123 accepted model:96 elements/576 explicit faces, original atlas1024², display/pivots preserved. Semantic split is95 fixed + under_grip_cell index53; grip_heel index46 is fixed. The apparent base is under_grip_cell, not the adjacent heel. A single narrow reload-only insert follows canonical front-grip43 axis(-67.5149801deg). Local dimensions0.7x0.6x2.25, original cell53 six UV faces reused; overlaps cell and is inside original solids when seated. Exact hidden profile is authored, not source-proven. Entire cell+insert moves rigidly; no scaling/hiding, separate rounds or invented bolt.97 assembled elements maximum; exact0/1 full canonical graph =96.

API: destiny:weapon_reload_w185_hollow_words/hollow_words; float[1] normalized0..1,21 visual samples/2.5ticks; boolean[0] grip, string[0] ads/inspect. Both FP hands only; ADS/inspect, negative, nonFP and endpoints dispatch original full canonical item graph. Canonical geometry/UV/default paint/ADS/inspect/timing/audio/ammo untouched. Master owns shared runtime, catalog route, lifecycle and native gates.

Trajectory independently authored after viewing these actual frames. W184 rigid matrix, graph guards, offline rasterizer and representative actual26.3 parser/ItemModels/ItemTransform/JOML test infrastructure reused; W184 trajectory not reused. Numeric angles, offsets, pivot and normalized timings are approximations, not animation extraction.

comparison.png and authored panels of storyboard.png are OFFLINE CPU renders, NO HANDS, NOT NATIVE. Actual storyboard panels retain exact original extracted frame pixels before thumbnailing; numbers are source zero-based decode indices. Source60/1fps, MP4 timebase1/15360; PTS=index*256, seconds=PTS/15360. FFmpeg showinfo values retained externally; no generic fps-resampled frame is called exact. Media/large caches remain outside repository. Verification uses repository hashes without external media; --render uses external source PNGs only.

Native pack admission/load, both hands/grips hand contact and cell clearance, lifecycle cancellation/equip/switch/death/disconnect, partial/empty/no-reserve, audio listening and10-20display observation remain pending with master. Offline tests do not establish native success, source-perfect hidden shaft fidelity or performance.

Read art design skill and Ace87/Izanagi79 study; their cube counts guide coherent volume/UV design, not required element targets. Existing96-element base is unchanged.

Video SHA256: ee05a6b627ae2a7353d036972fb6b6efd27d31665c2c2bdf79a2a959fa8967b4

Metadata SHA256: b97cc58732e0ba79472e1ac6df729db5c5b28d28b65244be43fe271ce52c5c1e

|PNG|Source frame|PTS|Seconds|SHA256|Observation|
|---|---:|---:|---:|---|---|
|reference-01.png|6900|1766400|115.000000000|89391402f3363cb1c33c0f876189f05381ee5a16dacbdf0edb4aef67c97888d1|Inventory explicitly HOLLOW WORDS; default teal/gold top, bright silver shoulder, open triangular grip and lower cell establish identity.|
|reference-02.png|11204|2868224|186.733333333|6a129934d046c73219654967de63917ffdcbcd4b73f0c8858f44128d9c0cf992|Last hip pose before lift; HUD1 with4 reserve.|
|reference-03.png|11210|2869760|186.833333333|29fcfc596d3ec0c1c6ed777334e024094101d6675c59c65f688fba4e7f997234|Muzzle lifts steeply at right edge; support hand reaches toward lower frame.|
|reference-04.png|11216|2871296|186.933333333|86130d48665f0498e2e835209352f69700bb4e1917739e336779a1f186324506|Carrier turns side toward viewer, fixed grip and rear strut remain attached.|
|reference-05.png|11224|2873344|187.066666667|0e1df1bc74b48040cdc4562c2de02b7fd8f5ff6058202c1a9a493ea10a8670f5|Steep muzzle-up right-edge presentation, fingers descend toward underside.|
|reference-06.png|11232|2875392|187.200000000|ec187c5a2c41190d9a0a42cc2076a61a2ba2282bfcd228e4867324099c2b3fc5|Right hand stays through triangular grip; support hand reaches lower cell, release partly outside frame.|
|reference-07.png|11244|2878464|187.400000000|bec6524527c5da3945cbaf21a2443f05cac0d6a8c7fc3606660cea5fba84c6a6|Raised fixed grip/brace visible; lower cell exchange drops below bottom edge.|
|reference-08.png|11256|2881536|187.600000000|2db8095f5180c0f46a13bd122ac926840be39b705ad91d4f72d2a8143a34b79b|Carrier holds high, hand and screen edge conceal outgoing cell; exact hidden path authored.|
|reference-09.png|11268|2884608|187.800000000|26f53f8e528718f768e6f7c848d43cec4fb2abeb6ad207a1b8a8c405348ddd53|Support hand remains low/offscreen; fixed grip silhouette unchanged.|
|reference-10.png|11280|2887680|188.000000000|b5a10bd1ff75f45d9d070fbdc9f16dc4cec77d5e9261c2ce736e4858253a3799|Support hand returns underneath; incoming cell silhouette partly concealed by wrist and edge.|
|reference-11.png|11292|2890752|188.200000000|29064d725bb1cdc531a60146281bd83eba032a4020701a6e053586e03a7a935d|Support palm contacts lower grip area; HUD1 becomes5, confirming whole reload with4 reserve.|
|reference-12.png|11304|2893824|188.400000000|69a0c2aefd5d70eb45e5e045cff04fa03c484e4448e457af3f945ac92f5080e5|Support hand opens/releases; weapon starts rotating down and toward hip.|
|reference-13.png|11312|2895872|188.533333333|8bfafa2761dec07d7b77bc3a6ef03fede488c6aba066193cbdf93e7d17ed1cd2|Carrier lowers quickly, support hand passes beneath body.|
|reference-14.png|11320|2897920|188.666666667|858f5b158103228297d61a71fd1a48555a84b98a6a2012483b6b0cd65a90a32b|Fast downward recovery with support fore-end reach.|
|reference-15.png|11332|2900992|188.866666667|6f36b83d2de5b946c96a46dac0eb9aeae1bd60f833472df08006116466693955|Hip presentation recovered with player view motion; no independent bolt stroke resolved.|
|reference-16.png|11348|2905088|189.133333333|857aef29782d97979c25e02a3943f5d72262dda251485421d78ed6d32e0f5ed2|Recovered weapon bobs with movement; canonical exact endpoint authored.|
