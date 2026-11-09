package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;

/** Explicit accepted melee provenance. Generic playerAttack damage cannot identify a melee:
 * weapons, grenades and supers use that DamageSource too. Never hook generic onKill.
 */
public final class MeleeWeaponTraits {
    public record Snapshot(WeaponSwashbuckler.MeleeToken swashbuckler, WeaponGraveRobber.Token graveRobber, WeaponPugilist.MeleeToken pugilist, WeaponWellRounded.Token wellRounded, PerkBatchC.MeleeToken batchC /* W322 batch C */, PerkExpansionCombat.AbilityToken desperate) {
        public static final Snapshot NONE = new Snapshot(WeaponSwashbuckler.MeleeToken.NONE,WeaponGraveRobber.Token.NONE,WeaponPugilist.MeleeToken.NONE,WeaponWellRounded.Token.NONE,PerkBatchC.MeleeToken.NONE,PerkExpansionCombat.AbilityToken.NONE);
    }
    private MeleeWeaponTraits() {}
    public static Snapshot accepted(ServerPlayer p) {
        return new Snapshot(WeaponSwashbuckler.meleeAccepted(p),WeaponGraveRobber.accepted(p),WeaponPugilist.meleeAccepted(p),WeaponWellRounded.accepted(p,kim.biryeong.destiny.guardian.AbilitySlot.MELEE),PerkBatchC.meleeAccepted(p),PerkExpansionCombat.acceptedAbility(p,kim.biryeong.destiny.guardian.AbilitySlot.MELEE));
    }
    /** Real direct powered contact only. Damage-over-time/status pulses are deliberately excluded. */
    public static boolean poweredDamage(ServerLevel level,ServerPlayer p,LivingEntity target,float amount,
                                        Element element,Snapshot source) {
        boolean eligible=Combat.isEnemy(p,target) && !p.isAlliedTo(target)
                && !(target instanceof TamableAnimal tame && tame.isTame());
        if(source!=null&&eligible)amount=source.batchC().apply(target,amount); // W322 batch C One-Two Punch
        float before=target.getHealth()+target.getAbsorptionAmount();
        boolean killed=Combat.damage(level,p,target,amount,element);
        float actual=before-target.getHealth()-target.getAbsorptionAmount();
        if(eligible && Float.isFinite(actual) && actual>0) confirmed(p,source,target,true,killed);
        return killed;
    }
    /** Only for callers already observing positive actual loss and exact melee attribution. */
    static void confirmed(ServerPlayer p,Snapshot source,LivingEntity target,boolean powered,boolean killed) {
        if(source==null || source==Snapshot.NONE)return;
        if(killed)PerkExpansionCombat.abilityKilled(p,source.desperate(),target);
        if(killed)WeaponSwashbuckler.meleeKilled(p,source.swashbuckler(),target);
        WeaponGraveRobber.confirmed(p,source.graveRobber(),target,powered,killed);
        WeaponPugilist.meleeConfirmed(p,source.pugilist(),target);
        if(powered)WeaponWellRounded.meleeConfirmed(p,source.wellRounded(),target);
    }
}
