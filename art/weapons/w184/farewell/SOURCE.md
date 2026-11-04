# Farewell W184 original reference and authorship

Source: True Vanguard, The Sidearm with No Competition - Farewell Legendary Review, uploaded2021-05-14, https://www.youtube.com/watch?v=2VaZGMrEfjQ . Downloaded original video-only1280x720 H264; retained in /private/tmp/w184-farewell-report/farewell-reference.mp4 plus metadata, hashes and frame-exact PNGs. Source stream is60000/1001fps, timebase1/60000 (metadata rounded60fps is not used for frame timestamps).

Identity: review title explicitly Farewell; continuous FP footage matches green cable bundle, finned front, hanging blade, magenta marks and blue/silver rear. No inventory name/roll is claimed. Source lighting is not canonical paint input. Action n1456..1524 =24.290933..25.425400seconds. Scene/camera motion is excluded from weapon trajectory.

Canonical models/weapon_surface_w123/farewell.json has115 elements. Grip_shoulder77 and grip_core78 stay fixed. Heel81 and open_heel_loop82..89 are the exposed magazine-foot assembly. Canonical has no separate shaft. All115 original elements/faces/UV/paint and their rotations remain exact. Added reload-only shaft core .84x3.72x1.28 model units; local bounds[7.58,7.23,7.57]..[8.42,10.95,8.85], rotation inherited grip78 at-14.00158177855961deg about[8,9.305,8.175]. Core extends .070443 local-Y units below fixed grip to overlap original heel at world point[8,7.20,8.30]; it is not claimed wholly occluded while seated. Canonical endpoint graph bypasses all additions. Two narrow seam strips .025x3.51x.06 on either side, all existing heel81 atlas rectangles. Exact dimensions, backside and seam thickness are authored from n1472; no exact extracted original shaft fidelity claim. Active assembly106body+12magazine=118<=1000. Endpoint canonical115.

Motion keys are authored interpretations after inspecting these exact source frames, not copied High Albedo/Patron motion. Muzzle lift/cant -> grip-base release -> down-left magazine withdrawal -> incoming insertion -> inward wrist roll -> canonical recovery. Magazine stays one rigid object, without scale changes or duplicate spent/fresh props. No independently resolved bolt motion animated. Occluded exchange/seat path, numeric pose angles/offsets and canonical hip recovery are authored. Fixed cable bundle, receiver, bayonet and sights never animate separately. No invented sound/bolts/mechanism.

Reuse: W183 generator matrix/guard/CPU renderer and independent Python/JUnit parser/transform test infrastructure only. Gameplay stays15round/360RPM/32ticks, original sounds/ammo transfer/cadence unchanged. Source HUD8to15 and source duration do not drive runtime. Master owns registry/runtime/routing/HUD/gates/native.

Offline comparison: multiple obliques, common-camera motion, rigid magazine detail and both hand/grip transforms. Storyboard pairs actual frames with authored poses. OFFLINE / NO HANDS / NOT NATIVE. No native success, audio listening, performance or IK claim. Deterministic --verify reads retained product media hashes and never needs the source video/frames/network.

## Exact observed frames

- n1456 at 24.290933s, authored p0: Hip presentation before reload; green bound cables, magenta stencil, finned front, blue receiver and hanging blade establish Farewell silhouette. PNG SHA256 cd49e9fd789ebf27396fd9512d050dbe4008c093c5f47e3024d083cb0239ce5d.

- n1460 at 24.357667s, authored p0.1: Muzzle begins rising and left side turns toward camera. PNG SHA256 088294db57d52391405d2355603d37b51a5d3e1999e1d6bec69e002e0cd8ddab.

- n1464 at 24.424400s, authored p0.2: Raised diagonal carrier; right hand stays on grip; left hand comes to grip base. PNG SHA256 738dfbbbe8a270c036c2f514c86bdcd16b5f33d15d8729df772546f1b0fc153a.

- n1468 at 24.491133s, authored p0.25: Support fingers cup grip base; heel release partly hidden. PNG SHA256 3823239b724f690957e1590074be7a35e17b24d9482501122f609e64b3c908ee.

- n1472 at 24.557867s, authored p0.3: Rectangular grey magazine with parallel broad-face lines visible down-left in support hand; shaft is separate from fixed pistol grip. PNG SHA256 a24a6a3501968a4ebdee304dfffa87c08ef50f9aa027e08afaed962847cc1f4b.

- n1480 at 24.691333s, authored p0.4: Outgoing magazine lowers below screen; fixed rear receiver and trigger guard remain attached. PNG SHA256 0241bfc085e9961cf63e2c3e3b259b1bba3fcd801a5034a467c40e1e4f849df0.

- n1488 at 24.824800s, authored p0.55: Carrier remains raised while support hand is below screen; exchange hidden. PNG SHA256 b109b9366546119786c1593cf2edc2b18547fd786fd1d609d558dbb4ad30f679.

- n1496 at 24.958267s, authored p0.65: Support hand returns from below toward grip, top/seat boundary hand occluded. PNG SHA256 ee983c306acb682123eec019cca3b7e1fa6699bb8d432cd0804f88931c2762da.

- n1500 at 25.025000s, authored p0.72: Magazine seated, HUD changes from8 to15; carrier rolls inward/down. HUD timing is not local reload clock. PNG SHA256 dc57c570a6f8b17667bc8fe7df4df251a17bb5e19e87c56035a7066612138524.

- n1504 at 25.091733s, authored p0.8: Left hand leaves grip and moves upward as wrist rolls; no independently resolved bolt stroke. PNG SHA256 8292d0f17ca6f2fe8f16491c855e0460720671ca58c61730f5c5a7d721614d15.

- n1512 at 25.225200s, authored p0.9: Weapon turns toward forward presentation; support-hand contact is partly hidden. PNG SHA256 f9450cc4edd8fb6eefc3a6902a0a6be09cc943dba7a864bd019cd8997201ecdb.

- n1524 at 25.425400s, authored p1: Forward recovery follows; camera/player motion continues. Canonical hip endpoint is authored. PNG SHA256 2d5ed1380dae60caa366b7cda118e389f27116bf7f9ebf3bbd290db6bab08f36.

Video SHA256 8fafe0a686a8706dcbbc07d99127927a4bf5fef17f9290abd9995b80e2c307ca
Metadata SHA256 bf3555ff87589a275eaf48afbd7f96609de383f855d791abbd51febb33b4b72d

## Authored numeric keys

((0, (0, 0, 0), (0, 0, 0), (0, 0, 0)), (0.1, (12, -4, -6), (0.1, -0.08, 0.03), (0, 0, 0)), (0.2, (31, -6, -24), (0.28, 0.2, 0.1), (0, 0, 0)), (0.3, (37, -5, -27), (0.32, 0.27, 0.15), (-0.1, -1.7, 0.424)), (0.4, (38, -7, -25), (0.34, 0.26, 0.12), (-0.6, -4.6, 1.147)), (0.5, (36, -8, -24), (0.34, 0.21, 0.1), (-0.8, -5.4, 1.346)), (0.6, (35, -8, -23), (0.32, 0.15, 0.08), (-0.3, -3.4, 0.848)), (0.72, (29, -6, -20), (0.28, 0.04, 0.05), (0, 0, 0)), (0.8, (11, 3, -43), (0.18, -0.12, 0.04), (0, 0, 0)), (0.86, (5, 9, -55), (0.1, -0.18, 0.02), (0, 0, 0)), (0.93, (13, 5, -22), (0.06, -0.05, 0.01), (0, 0, 0)), (1, (0, 0, 0), (0, 0, 0), (0, 0, 0)))
