# Zone entry facing — 2026-11-04

Every arrival seat was authored with yaw 0. In the refinery this placed the fireteam facing a corner of the entry corridor, and in the blast zone facing a wall section. The arrival seats now carry authored yaw values: RF.IN/0/1/2 = −82° (down the walk route toward the generator), BL.IN/0/1/2 = −22° (toward the open battlefield). RY and SP keep yaw 0, which already looks into the arena and toward the Sepiks platform.

Two code variants were tried first and rejected on screenshots: always using the heading of the first authored walk route (SP then faced away from Sepiks into the cave, see rejected-sp-route-heading.png), and a 6-block wall ray test (did not trigger in the refinery corner). Data authoring is used instead; no runtime code changed. The zone manifest output hash for markers.json was updated.

Verification: 88 strike unit tests and the jar pass; one isolated real-runtime run through BL_CLEAR shows the corrected RF and BL arrivals (before-after.jpg). Progression was unchanged.
