# W44 weapon reticles

Original procedural HUD artwork, inspired by Destiny's weapon-family readability.
No extracted sprites, screenshots, downloaded icons, or third-party artwork are used.
These are a source-style interpretation, with no pixel-exact reproduction claim.

`scripts/generate_weapon_reticle_w44.py` is the editable artwork source. Run it with
a Python containing Pillow; add `--verify` to check every generated file without writing.
`contact-sheet.png` shows the 17 family/frame variants. Its labels are reference-only;
all in-game textures contain only transparent geometry.

Hand cannons and sidearms use rings and a fixed centre dot. Automatic weapons use
segmented arcs or corner brackets. Sniper and linear fusion sights contract to a
narrow precision opening in ADS. Pellet shotguns have a wide spread circle; slug
shotguns have a smaller circle and upper diamond. Fusion, trace, bow, grenade,
heavy grenade and rocket weapons have their own geometric sights. Sword and
glaive families are excluded; the glaive's existing W41 HUD keeps its ownership.

`WeaponReticleHud.update(player, aimProgress, bloom, reloading)` reads only the
equipped live `WeaponItems` entry and actual loadout eligibility. Each player has
two stable `destiny:reticle_w44_` nodes: a responsive outer frame and a fixed centre
dot. At 1920×1080 reference coordinates the centre stays at (960, 540), and frame
expansion is bounded to 4–12 pixels per supplied normalized bloom value. Geometry
is quantized to half-pixels. Reload hides the reticle until the supplied flag clears. Non-finite inputs fall
back to zero; finite values are clamped to [0,1].

The main integration owns calling `update` from CombatHud and calling `remove`
during its cleanup/disconnect path. This addition does not modify registrations,
weapon runtime, firing profiles, or existing HUD ownership.

The GameTest class is `kim.biryeong.destiny.test.WeaponReticleW44GameTests`; the main
integration must register it in the existing `fabric-gametest` entrypoints before
the coordinated run. Gradle and runtime execution are intentionally deferred to
that coordinated validation. The optional asset test is `WeaponReticleAssetsW44Test`.
