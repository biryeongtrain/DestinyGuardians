package kim.biryeong.destiny.weapon;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class PerkExpansionSupportOwnershipTest {
    private boolean equipped(Object target,int count,Object[] slots,boolean canonical) {
        return PerkExpansionSupport.equippedIdentity(target,count,slots.length,i->slots[i],canonical);
    }
    @Test void hotbarRetainsStowedOriginalButBackpackAndOffhandLoseCredit() {
        Object source=new Object(); Object[] inventory=new Object[41];
        inventory[2]=source; assertTrue(equipped(source,1,inventory,true));
        inventory[2]=null;inventory[8]=source;assertTrue(equipped(source,1,inventory,true));
        inventory[8]=null;inventory[9]=source;assertFalse(equipped(source,1,inventory,true));
        inventory[9]=null;inventory[40]=source;assertFalse(equipped(source,1,inventory,true));
    }
    @Test void canonicalLoadoutAndUniquePhysicalIdentityAreRequired() {
        Object source=new Object();Object[] inventory=new Object[41];inventory[0]=source;
        assertFalse(equipped(source,1,inventory,false));
        assertTrue(equipped(source,1,inventory,true));
        inventory[15]=source;assertFalse(equipped(source,1,inventory,true));
        inventory[15]=null;assertFalse(equipped(source,2,inventory,true));
        inventory[0]=new Object();assertFalse(equipped(source,1,inventory,true));
    }
    @Test void equalReplacementDoesNotInheritOriginalSource() {
        Object source=new String("same");Object replacement=new String("same");Object[] inventory=new Object[41];
        inventory[0]=replacement;assertEquals(source,replacement);assertFalse(equipped(source,1,inventory,true));
        assertTrue(equipped(replacement,1,inventory,true));
    }
}
