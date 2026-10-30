# W269 test delta handoff

Only this delta was written. Main and the fixed slot's stale src were not edited. No build, GameTest execution, native QA, commit, or resource manifest edit was performed.

Master integration: compare baseline-sha256.json against current main before copying the five existing files. Add the new GcbInputW269GameTests.java and register kim.biryeong.destiny.test.GcbInputW269GameTests in the master-owned GameTest manifest. This delta does not contain registration changes.

## Counts

- `src/gametest/java/kim/biryeong/destiny/test/GcbInputW269GameTests.java`: 5 GameTests
- `src/gametest/java/kim/biryeong/destiny/test/ReloadInputW249GameTests.java`: 6 GameTests
- `src/gametest/java/kim/biryeong/destiny/test/WeaponInventoryWireW92GameTests.java`: 4 GameTests
- `src/gametest/java/kim/biryeong/destiny/test/WeaponIzanagiPresentationW91GameTests.java`: 8 GameTests
- `src/gametest/java/kim/biryeong/destiny/test/WeaponIzanagiScopeW162GameTests.java`: 3 GameTests
- `src/gametest/java/kim/biryeong/destiny/test/WeaponIzanagiW84GameTests.java`: 12 GameTests

Total: 38 methods across six files; five new GCB tests, 33 existing methods retained in the five changed suites. Counts are source annotations, not passed test results.

## Coverage

- Existing honing requests in W84, W91, W92 and W162 now send DROP_ITEM with Shift held, preserving ordinary Q scenarios. W84's old CtrlQ test name changes to normalQAndAlternateShiftQBothWaitFullSixtyOneWithoutEarlyCreditOrDuplicateRestart.
- W249 renames the old both-hone test to izanagiShiftQHonesButCtrlQOnlyRepairsPredictedDrop. It proves ShiftQ honing and CtrlQ/Ctrl+Shift+Q no-op on a partial-magazine Izanagi and Ace: no reload/honing/menu, exact authoritative stack and components/ammo retained, adjacent inventory intact, encoded clientbound selected-slot repair. Its no-reserve ShiftQ rejection now actually sends Shift+DROP_ITEM.
- New grouped GCB callback test checks the full Key enum mapping (Z grenade, C melee, V class, attack primary, X unmapped, no F enum), release filtering, attack outside super, and actual registered event dispatch to ability cooldowns/action history.
- GCB legacy chords are blocked while vanilla F/ShiftF/doubleShift/Shift+punch positive controls still cast. A debug runtime flag alone does not count as handshake.
- GCB fixtures use GCBPlayer.gcb$markHasMod() and gcb$setModVersion, with the production ClientControls detector. Runtime forget retains mode; a same-UUID replacement without a fresh handshake verifies session retention, and ClientControls.forget removes it. Every owned fixture registers TestPlayers.remove plus ClientControls.forget in finally.
- Plain F uses the real offhand packet handler. Failed F does not poison same-tick retry. Successful duplicate F preserves one session; end/refill in the same tick isolates dedup from BUSY/energy guards, followed by acceptance on a later tick.
- Air jump and real Golden Gun primary remain enabled; GCB attack and vanilla punch in both orders consume one shot without casting melee, including while Shift is held.

## Existing CtrlQ invariant audit

Conflicting assertions were confined to the five changed suites. W44, W51, W69, W71, W100 and W114 CtrlQ checks assert cancellation/no drop or no restart of an already accepted Q reload; they do not require CtrlQ to start a new reload and were left intact. W44's old method name still says qAndCtrlQReload, but its assertions are compatible.

## Validation and limits

Static diff, annotation counts, delimiter/whitespace checks, GCB API and production callback review completed. All five recorded main SHA-256 baselines matched at handoff. No compilation or runtime pass is claimed. Optional HUD key-mode/cleanup assertions were not added to avoid delaying master QA.
