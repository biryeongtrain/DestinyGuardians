# Beloved W126 — offline art review

Reference: `/tmp/destiny-weapons-w31/references/beloved.jpg` (default dye), W31 render and original Beloved FBX/DDS. The raw albedo is mostly undyed; it is deliberately labeled that way in the comparison.

The new design uses **99 opaque cuboids**: body 94, magazine 5. These are semantic barrel walls, forked muzzle jaws, open gold frame, solid jewel settings, receiver, stock braces and optic. It does not convert all 22,120 source triangles/components or substitute two alpha side sheets for a body. Full and body+magazine are alternative representations; assembled count is 99, below 1,000.

Identity retained: long silver barrel; open slotted muzzle; three purple jewels per side in gold settings; source scrollwork and pearl studs; dark skeleton stock and scope with gold objective rim. A continuous 1024² atlas allocates independent face islands at about 27 texels per model unit, with 2px extruded gutters. Purple cabochons and upper/lower scroll relief use selected original DDS crops, softly cleaned and recolored to the default-dye reference. Wide structural panels use restrained satin shading, panel seams, grip wraps and magazine flutes. There is no random texture noise or invented text. The static source relief is not runtime PBR.

The side + front/rear oblique comparison shows raw source, local 253-cube canonical, and the new design at the same scale per row. Detail panels show solid jewelry, recessed lens/rim, open muzzle and open stock. `inspection.bbmodel` embeds the atlas and separate body/magazine groups for user-opened inspection only; no GUI state is touched.

Preserved: canonical display transforms; native muzzle -Z axis; source scale 18.824982686476197; source anchor [8,8,8.359254816030532]; existing magazine coordinate frame/external reload anchor. The magazine's lowest Y and feed height match the source split. Approximate curves, subtle sculpted lip transitions and physical metallic reflections remain simplified.

Offline Python checks cover regeneration, emitted-element budget, all-solid geometry, face UV/opaque gutters, independent mag partition and anchor envelope, structural voids, input provenance, display, and inspection-project parity. Master must still validate 26.3 native rotation/parser, resource-pack registration and texture loading, Polymer parts, first/third-person holding and ADS, split reload trajectory, and 10–20 simultaneously displayed weapons. No game, GUI, Gradle or performance acceptance is claimed.
