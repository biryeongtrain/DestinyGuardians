# W331 Arc Staff dodge

User requested Arc Staff super dodge with a two-second cooldown using the supplied motion.

- Class-ability input is explicitly opt-in per SuperSession; only Arc Staff enables this action. Other supers still reject ordinary class abilities.
- Arc Staff owns a separate40-server-tick cooldown and HUD charge. It begins ready, bypasses the ordinary class cooldown and leaves that saved timer/perks unchanged. Ordinary reload, melee reset and class-ability perk effects do not run.
- Original Arc Staff evade front/back/left/right actions938/93C/93E/93F were evaluated directly from the read-only source.blend. Each retains its1.033333s source span,1-tick entry and2-tick exit. Existing six W330 clips remain dictionary-identical; source provenance and representative source/retarget review are under art/animation/w330/arc_staff/w331-dodge-*.
- Existing camera and staff equipment persist. Dodge uses the established native velocity impulse1.15 horizontal/.18 vertical and six invulnerability ticks; these are the existing Minecraft dodge policy, not newly decoded Destiny source events. No meaningful source root impulse marker could be established.
- Deploy, pending contact/attack recovery and dodge playback reject overlapping actions; accepted attacks are not erased or duplicated. No new grounded/air eligibility restriction was added. Ending/cancelling the owning super revokes pending dodge motion and rejects stale session references. Cooldown is measured from accepted dodge, not animation end.
- Server regression and actual native/framebuffer acceptance are recorded in validation.json. The existing isolated QA server empty-pause setting was temporarily disabled for this batch and will be restored. General Minecraft profiles and user Blender/Blockbench scenes are untouched.
