# Stormchaser W188 source and temporal study

OFFLINE evidence only. Native pack load, screen framing, hand contact, audio listening and 10-20 display observation remain master-owned and unverified.

Actual same-weapon source: [Ehroar - The New Burst Linear Fusion Is Insane! (Stormchaser)](https://www.youtube.com/watch?v=Ev71jjG4JbQ), uploaded 2022-05-29. Inventory n900 explicitly identifies STORMCHASER and its basic silver crest, red-black body, swept daylight loop, green heel and hooked stock. Gameplay n26872..27000 shows the same distinctive cage, grip and loop under a silver/white shader. This shader is mechanism evidence only; the canonical basic-dye atlas is unchanged.

Video nominal API metadata says60fps; actual decoded track is60000/1001fps, timebase1/60000, each frame1001PTS. The continuous action spans448.3145333333..450.45s (128 source intervals,2.1354666667s). The source begins exiting ADS after a burst and includes viewpoint rotation; we author a hip-based presentation and do not claim camera/bone extraction. Source phase times normalize to progress0..1; the local product reload stays49ticks/2.45s and5rounds,533ms charge,11charge ticks,3shot shared-ammo burst. Source perks and source duration never change local gameplay. The user DDC sheet is numerical priority; this presentation applies no numerical delta or broad rebalance.

Observed mechanism: steep muzzle-up presentation, support hand reaches the grip heel, downward withdrawal along the pistol-grip axis, a short low exchange partly occluded by hand/frame, replacement with a long narrow stem entering from below left, palm seating, then a fast lower/regrip. HUD1 becomes5 during seating. The upper receiver, swept loop and rear pistol grip remain attached. All six original heel/crown elements80..85 (grip_floor, power_shoe, toe, rear lip and both green insets) form one moving assembly. This is a full battery with one added narrow stem, not an animated receiver plate or isolated green strip.

The stem is authored inside original pistol_grip76 bounds, reusing its rotation and six UVs. The original95 cuboids,570faces,UVs,rotations,base paint and all canonical context transforms are unchanged.89 original fixed elements+6 original moving heel elements+1 added stem=96 simultaneous emitted elements; exact endpoints resolve95 original elements. The entire swept loop, stock, cooling cage, barrel, grip and receiver stay on the fixed carrier. Hidden shaft profile and support-hand clearance are approximations; no extracted bones/animation or hand IK.

Inert rip inspection compared actual Stormchaser.blend stored object matrices and Stormchaser.fbx coordinates via the existing source parser, outside Blender.29,718 accepted triangles; Stormchaser.00.002 is the separate green grip-emission object, mapping native=[world.X,world.Z,world.Y]*21.374938294786276+[8,8,8]. Its native bounds are[7.59868555,6.59893699,7.92155398]..[8.40092973,6.79577870,9.36278049], locating the heel. Rip files are static geometry/material evidence, not animation.

Rip SHA256: Stormchaser.blend22486c3c8359a9977d13ce72f323a2e38a2b56c445c5378b4120a596dba22629; Stormchaser.fbx50ff6f85305dab322e229c75bf807f6a6b56545c6be6c16e0e640fb8a9ce6ce0. Canonical geometry is weapon_surface_w123/stormchaser.json (W150 semantic95-element assembly); neither rip silhouette nor existing UVs are simplified.

Independently authored keyframes: dip0..06,lift.06..22,withdraw.22..39,low exchange.39..49,incoming.49..68,seat.68..75,rapid lower.75..95,recover.95..1. Common FP translation(-1.4,-1.2,-2.8) through the steep exchange moves the assembly inward/farther; the same carrier is transported into two_hand. No native viewport claim follows from the offline views. Both hands use Minecraft left-mirror ItemTransform semantics, constant accepted scale, exact canonical0/1, negative/overshoot/nonFP/ADS/inspect fallbacks.

Only W185 matrix, graph and W123 raster infrastructure were reused, with independent Stormchaser mechanism, partition and motion. comparison.png renders actual emitted JSON from side/front/reverse/rear, common-scale sequences, battery detail and both FP hands/grips. storyboard.png pairs the retained actual source PNGs below with emitted samples at nearest normalized progress; all authored storyboard panels use one fixed camera and extent. Source and authored camera framing are independent, with no hands drawn. This is not native screenshot evidence.

Research/media and reports remain in /private/tmp/w188-storm-report, outside source/worktree. Reproduction: imaging Python scripts/generate_reload_w188_stormchaser.py --render --evidence /private/tmp/w188-storm-report. Media-free deterministic verification: same command with --verify and without --render.

Video SHA256: 357954642f7931469b4ef0e7a9d5e44b4735111ef43c4b26272cb2f3e3fb3c9d

Metadata SHA256: db84af0fc9c5b578c1529882df09ee05520f6d783f7b4e1c95307adc0370c819

- n900; PTS900900; 15.01500000s; normalized0.000000. Inventory explicitly STORMCHASER: silver crest, red-black body, swept loop, hooked stock and green grip heel identify the weapon. SHA256 `fb37a10be8c66041e3b2bb2517125d9d8462230005b3c3b6efc4b6c7f773e61e`
- n26872; PTS26898872; 448.31453333s; normalized0.000000. Final ADS burst with HUD1; start of continuous reload window. SHA256 `0533cd5c4bd9058298bd4e70f1527123893acabb4febd9ffea04ee2e0abe52d4`
- n26880; PTS26906880; 448.44800000s; normalized0.062500. Drops out of ADS before muzzle-up rise; player turns to the reload presentation. SHA256 `c4e568f9f6ffa23637aae0c7ea89be00deaf93d760ba9a370f809256b610bd9e`
- n26888; PTS26914888; 448.58146667s; normalized0.125000. Muzzle rises at right edge, broad cage and swept loop visible. SHA256 `55ad462d6438123a25bdee899eecc4f0341ecb51446290aa6e0ded877f1458cb`
- n26896; PTS26922896; 448.71493333s; normalized0.187500. Steep muzzle-up hold; support hand reaches beneath pistol grip toward heel. SHA256 `24641ca85c52fa4375b84048bd2f1a4a480e10d38fe5f89c1f7f71856c5f1f02`
- n26904; PTS26930904; 448.84840000s; normalized0.250000. Support hand encloses the full heel assembly; receiver and open frame remain attached. SHA256 `4abae023050ec64b2beb3bd255d33805f822959885d30176b1956a826a29fc83`
- n26916; PTS26942916; 449.04860000s; normalized0.343750. Support hand pulls down along the pistol-grip axis; outgoing battery partly occluded. SHA256 `0725b171f935bcc5f0f372eabe127c880c9f7dc6406b8670f7f5973c97b87c6d`
- n26928; PTS26954928; 449.24880000s; normalized0.437500. Right hand retains pistol grip; outgoing battery and support hand descend below the edge. SHA256 `cd420c6d98c3a635288e3f479aaf067cc2f512d41dec8cb750bcbc300d87234f`
- n26940; PTS26966940; 449.44900000s; normalized0.531250. Empty heel area remains at lower right while carrier holds steep. SHA256 `f75c805d18286c2d75fe0c54fb96481abe2a02cd18d780f8b2f3de7806c97f16`
- n26952; PTS26978952; 449.64920000s; normalized0.625000. Replacement long narrow stem and substantial foot enter from below left. SHA256 `d85cc2600b049e105c78fc60150c1647a4fd88a7937de353d3a4e5a0a05e48ac`
- n26960; PTS26986960; 449.78266667s; normalized0.687500. Stem aligns into pistol-grip underside; shoe remains supported by left hand. SHA256 `3f9f176762e2014b9833cc3b1d1d8bfa86bd20ba4b0148fc2825da98ec567335`
- n26968; PTS26994968; 449.91613333s; normalized0.750000. Palm drives complete replacement upward; shaft is almost concealed. SHA256 `0b8b5d34b0e04f043b8bfceda04476a6796f4a87c74ccd95c256bf685be1e2b0`
- n26976; PTS27002976; 450.04960000s; normalized0.812500. Seated heel, support hand releases and HUD1 becomes5. SHA256 `266536dacdaec2ebbb78faa8cc8d2d7fdde15d6cfe98d61693e5657f9bb6e558`
- n26984; PTS27010984; 450.18306667s; normalized0.875000. Rapid muzzle-down recovery with support-hand fore-end reach. SHA256 `dde13fabfa38966d58236faf3b6455826d083557fe70e6568bbb954d191aedeb`
- n26992; PTS27018992; 450.31653333s; normalized0.937500. Weapon returns toward hip; viewpoint motion remains in source. SHA256 `788afc090aae823d4b36f9d8b326bf067c3c1bbbab535df9d832f504620737b1`
- n27000; PTS27027000; 450.45000000s; normalized1.000000. Recovered hip hold with5 rounds, before following melee. SHA256 `713aafe624f016807518701e036f8fe80d4f96e2ed720d1da7b946187752a982`
