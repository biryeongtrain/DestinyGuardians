package kim.biryeong.destiny.hud;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
import static kim.biryeong.destiny.hud.WeaponPerkRows.Kind.*;

class PerkExpansionHudTest {
    @Test void damagePreemptsUtilityWithoutExceedingSharedBudget() {
        var legacy = List.of(new WeaponPerkRows.Row(MEMENTO_MORI,0,2,0),
                new WeaponPerkRows.Row(OUTLAW,20,0,1), new WeaponPerkRows.Row(RAPID_HIT,30,2,2));
        var extra = List.of(new WeaponPerkRows.Extra("precision_instrument",3,22),
                new WeaponPerkRows.Extra("desperate_measures",2,140),new WeaponPerkRows.Extra("keep_away",1,-1));
        var rows = WeaponPerkRows.merge(legacy, extra);
        assertEquals(List.of(MEMENTO_MORI,PRECISION_INSTRUMENT,DESPERATE_MEASURES,OUTLAW),rows.stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(List.of(778,746,714,682),rows.stream().map(WeaponPerkRows.Row::y).toList());
        assertEquals(22,rows.get(1).ticks());
    }
    @Test void expiredUnknownAndDuplicateObservationsCannotLeaveStaleNodes() {
        var extra = List.of(new WeaponPerkRows.Extra("heal_clip",1,0),new WeaponPerkRows.Extra("missing",1,20),
                new WeaponPerkRows.Extra("permeability",1,-1),new WeaponPerkRows.Extra("permeability",1,-1));
        var rows=WeaponPerkRows.merge(List.of(),extra);
        assertEquals(1,rows.size()); assertEquals(PERMEABILITY,rows.getFirst().kind());
        assertEquals(List.of(PERMEABILITY.nodeId("minutes")),WeaponPerkRows.nodesToRemove(rows,
                List.of(PERMEABILITY.nodeId("label"),PERMEABILITY.nodeId("minutes"))));
        assertEquals(rows.getFirst().nodeIds().stream().sorted().toList(),
                WeaponPerkRows.nodesToRemove(List.of(),rows.getFirst().nodeIds()));
    }
}
