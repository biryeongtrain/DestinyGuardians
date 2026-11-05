package kim.biryeong.destiny.economy;

import kim.biryeong.destiny.economy.EconomyLedger.Error;
import kim.biryeong.destiny.economy.EconomyLedger.MailKind;
import net.minecraft.nbt.CompoundTag;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.UUID;

import static kim.biryeong.destiny.economy.EconomyLedger.*;
import static org.junit.jupiter.api.Assertions.*;

/** Edge cases of the Glimmer / vault / postmaster / auction ledger. */
class EconomyLedgerTest {
    static final long T0 = 1_000_000L;
    EconomyLedger l;
    UUID a = UUID.randomUUID(), b = UUID.randomUUID(), c = UUID.randomUUID();

    @BeforeEach void setUp() { l = new EconomyLedger(); l.touch(a, "Alice"); l.touch(b, "Bob"); l.touch(c, "Carol"); }

    ItemPayload weapon(String name) {
        var t = new CompoundTag(); t.putString("id", "destiny:weapon"); t.putString("probe", name);
        return new ItemPayload(l.newId(), t, "w_" + name, name, "rare", "KINETIC");
    }
    ItemPayload dirt() { var t = new CompoundTag(); t.putString("id", "minecraft:dirt"); return new ItemPayload(l.newId(), t, "", "흙", "", ""); }
    long total() { long s = 0; for (var id : l.accountIds()) { s += l.glimmer(id); for (var m : l.mail(id)) s += m.glimmer(); } return s; }

    // ---------------------------------------------------------------- glimmer

    @Test void glimmerHasNoGameplayCapButRejectsNegativeUnknownAndOverflow() {
        assertEquals(Error.INVALID_AMOUNT, l.credit(a, -1).error());
        assertEquals(Error.INVALID_AMOUNT, l.debit(a, -1).error());
        assertEquals(Error.UNKNOWN_ACCOUNT, l.credit(UUID.randomUUID(), 5).error());
        assertTrue(l.credit(a, 500_001).ok());                   // no Destiny 500k cap: trading economy
        assertTrue(l.credit(a, 10_000_000_000L).ok());
        assertEquals(10_000_500_001L, l.glimmer(a));
        assertTrue(l.set(a, GLIMMER_CAP).ok());
        assertEquals(Error.GLIMMER_CAP, l.credit(a, Long.MAX_VALUE).error());   // arithmetic guard only
        assertEquals(GLIMMER_CAP, l.glimmer(a));
        assertEquals(Error.INSUFFICIENT_GLIMMER, l.debit(b, 1).error());
        assertEquals(Error.INVALID_AMOUNT, l.set(a, GLIMMER_CAP + 1).error());
        assertEquals(Error.INVALID_AMOUNT, l.set(a, -1).error());
    }

    @Test void rewardsClampAtCapAndReportLoss() {
        l.set(a, GLIMMER_CAP - 10);
        assertEquals(15, l.creditCapped(a, 25));
        assertEquals(GLIMMER_CAP, l.glimmer(a));
        assertEquals(7, l.creditCapped(a, 7));       // already full: everything lost, nothing breaks
        assertEquals(0, l.creditCapped(a, -3));
    }

    // ---------------------------------------------------------------- vault

    @Test void vaultCapAndStaleWithdraw() {
        for (int i = 0; i < VAULT_CAP; i++) assertTrue(l.deposit(a, dirt()).ok());
        assertEquals(Error.VAULT_FULL, l.deposit(a, dirt()).error());
        long uid = l.vault(a).get(0).uid();
        assertTrue(l.withdraw(a, uid).ok());
        assertEquals(Error.NOT_FOUND, l.withdraw(a, uid).error());         // double click / stale view
        assertEquals(Error.NOT_FOUND, l.withdraw(b, l.vault(a).get(0).uid()).error()); // someone else's item
        assertEquals(VAULT_CAP - 1, l.vault(a).size());
    }

    @Test void vaultReturnsExactlyTheDepositedPayload() {
        var w = weapon("ace");
        l.deposit(a, w);
        var back = l.withdraw(a, w.uid()).value();
        assertEquals(w.stack(), back.stack());
        assertEquals(w.uid(), back.uid());
    }

    // ---------------------------------------------------------------- postmaster

    @Test void sendValidatesWithoutSideEffects() {
        l.credit(a, 100);
        assertEquals(Error.SELF_MAIL, l.send(a, a, weapon("x"), 0, "", T0).error());
        assertEquals(Error.EMPTY_MAIL, l.send(a, b, null, 0, "", T0).error());
        assertEquals(Error.INSUFFICIENT_GLIMMER, l.send(a, b, null, 101, "", T0).error());
        assertEquals(Error.INVALID_AMOUNT, l.send(a, b, null, -5, "", T0).error());
        assertEquals(Error.MESSAGE_TOO_LONG, l.send(a, b, null, 1, "가".repeat(MAX_MESSAGE + 1), T0).error());
        assertTrue(l.send(a, b, null, 1, "가".repeat(MAX_MESSAGE), T0).ok());   // counted in code points, Korean exact limit
        assertEquals(Error.UNKNOWN_ACCOUNT, l.send(a, UUID.randomUUID(), null, 1, "", T0).error());
        assertEquals(99, l.glimmer(a));
    }

    @Test void recipientCapAppliesToPlayerMailOnly() {
        l.credit(a, 1000);
        for (int i = 0; i < POSTMASTER_CAP; i++) assertTrue(l.send(a, b, null, 1, "", T0).ok());
        assertEquals(Error.RECIPIENT_FULL, l.send(a, b, null, 1, "", T0).error());
        assertTrue(l.deliver(b, MailKind.AUCTION_RETURN, "경매장", weapon("r"), 0, "", T0).ok());  // earned items never bounce
        assertEquals(1000 - POSTMASTER_CAP, l.glimmer(a));
    }

    @Test void systemMailboxHasHardCeiling() {
        for (int i = 0; i < SYSTEM_MAIL_CAP; i++) assertTrue(l.deliver(b, MailKind.ADMIN, "", null, 1, "", T0).ok());
        assertEquals(Error.MAILBOX_OVERFLOW, l.deliver(b, MailKind.ADMIN, "", null, 1, "", T0).error());
        assertEquals(Error.INVALID_AMOUNT, l.deliver(b, MailKind.PLAYER, "", null, 1, "", T0).error());
    }

    @Test void claimSplitsGlimmerAtOverflowGuardAndKeepsUntakenItem() {
        l.credit(a, 500);
        var mail = l.send(a, b, weapon("w"), 300, "hi", T0).value();
        l.set(b, GLIMMER_CAP - 100);
        var got = l.claim(b, mail.id(), false).value();      // no room for the item, 100 Glimmer of room
        assertEquals(100, got.glimmer()); assertNull(got.item());
        var left = l.mailItem(b, mail.id()).orElseThrow();
        assertEquals(200, left.glimmer()); assertNotNull(left.item());
        assertEquals(Error.GLIMMER_CAP, l.claim(b, mail.id(), false).error());   // nothing claimable now
        var item = l.claim(b, mail.id(), true).value();
        assertNotNull(item.item()); assertEquals(0, item.glimmer());
        l.set(b, 0);
        assertEquals(200, l.claim(b, mail.id(), true).value().glimmer());
        assertTrue(l.mail(b).isEmpty());
        assertEquals(Error.NOT_FOUND, l.claim(b, mail.id(), true).error());     // double claim
    }

    @Test void mailConservesGlimmer() {
        l.credit(a, 1000); long before = total();
        var m = l.send(a, b, null, 400, "", T0).value();
        assertEquals(before, total());
        l.claim(b, m.id(), true);
        assertEquals(before, total());
    }

    // ---------------------------------------------------------------- auction

    @Test void listingValidation() {
        l.credit(a, 10_000);
        assertEquals(Error.NOT_A_WEAPON, l.canList(a, dirt(), 100, 24));
        assertEquals(Error.PRICE_RANGE, l.canList(a, weapon("x"), MIN_PRICE - 1, 24));
        assertEquals(Error.PRICE_RANGE, l.canList(a, weapon("x"), MAX_PRICE + 1, 24));
        assertEquals(Error.DURATION, l.canList(a, weapon("x"), 100, 7));
        assertEquals(Error.INSUFFICIENT_GLIMMER, l.canList(b, weapon("x"), 100, 24));   // cannot pay deposit
        for (int i = 0; i < MAX_LISTINGS; i++) assertTrue(l.list(a, weapon("w" + i), 100, 24, T0).ok());
        assertEquals(Error.LISTING_LIMIT, l.list(a, weapon("x"), 100, 24, T0).error());
        assertEquals(10_000 - MAX_LISTINGS * deposit(100), l.glimmer(a));
    }

    @Test void depositAndTaxRounding() {
        assertEquals(MIN_DEPOSIT, deposit(MIN_PRICE));
        assertEquals(5_000, deposit(500_000));
        assertEquals(Error.PRICE_RANGE, l.canList(a, weapon("big"), MAX_PRICE + 1, 24));
        assertEquals(0, tax(19));           // integer Glimmer: tax floors
        assertEquals(25_000, tax(500_000));
    }

    @Test void purchasePaysSellerMinusTaxAndHandsOverItem() {
        l.credit(a, 1000); l.credit(b, 5000);
        var w = weapon("sold");
        var listing = l.list(a, w, 2000, 24, T0).value();
        long before = total();
        var sale = l.buy(b, listing.id(), 2000, T0 + 1).value();
        assertEquals(w.uid(), sale.listing().item().uid());
        assertEquals(3000, l.glimmer(b));
        assertEquals(1000 - deposit(2000) + 2000 - tax(2000), l.glimmer(a));
        assertEquals(before - tax(2000), total());          // the tax is the only sink
        assertTrue(l.listing(listing.id()).isEmpty());
        assertEquals(Error.NOT_FOUND, l.buy(c, listing.id(), 2000, T0 + 2).error());   // second buyer loses cleanly
    }

    @Test void purchaseGuards() {
        l.credit(a, 1000); l.credit(b, 50);
        var listing = l.list(a, weapon("x"), 100, 12, T0).value();
        assertEquals(Error.OWN_LISTING, l.canBuy(a, listing.id(), 100, T0));
        assertEquals(Error.INSUFFICIENT_GLIMMER, l.canBuy(b, listing.id(), 100, T0));
        assertEquals(Error.PRICE_CHANGED, l.canBuy(b, listing.id(), 90, T0));
        assertEquals(Error.EXPIRED, l.canBuy(b, listing.id(), 100, T0 + 12 * HOUR));
        assertEquals(Error.NOT_FOUND, l.canBuy(b, 999_999, 100, T0));
        assertEquals(50, l.glimmer(b));
    }

    @Test void sellerAtOverflowGuardGetsProceedsByMail() {
        l.credit(b, 10_000);
        l.set(a, GLIMMER_CAP);
        var listing = l.list(a, weapon("x"), 1000, 24, T0).value();   // deposit leaves room 10 under the guard
        var sale = l.buy(b, listing.id(), 1000, T0).value();
        assertTrue(sale.proceedsMailed());
        assertEquals(GLIMMER_CAP - deposit(1000), l.glimmer(a));
        var mail = l.mail(a).get(0);
        assertEquals(MailKind.AUCTION_SALE, mail.kind()); assertEquals(1000 - tax(1000), mail.glimmer());
    }

    @Test void cancelOnlyBySellerAndRaceWithBuyer() {
        l.credit(a, 1000); l.credit(b, 1000);
        var listing = l.list(a, weapon("x"), 100, 24, T0).value();
        assertEquals(Error.NOT_SELLER, l.cancel(b, listing.id()).error());
        assertTrue(l.cancel(a, listing.id()).ok());
        assertEquals(Error.NOT_FOUND, l.buy(b, listing.id(), 100, T0).error());
        assertEquals(Error.NOT_FOUND, l.cancel(a, listing.id()).error());
        assertEquals(1000, l.glimmer(b));
    }

    @Test void expiryReturnsItemsAndRetriesWhenMailboxIsFull() {
        l.credit(a, 1000);
        var one = l.list(a, weapon("one"), 100, 12, T0).value();
        var two = l.list(a, weapon("two"), 100, 48, T0).value();
        assertTrue(l.expire(T0 + 12 * HOUR - 1).isEmpty());
        assertEquals(1, l.expire(T0 + 12 * HOUR).size());
        assertTrue(l.listing(one.id()).isEmpty()); assertTrue(l.listing(two.id()).isPresent());
        assertEquals(one.item().uid(), l.mail(a).get(0).item().uid());

        for (int i = 0; i < SYSTEM_MAIL_CAP - 1; i++) l.deliver(a, MailKind.ADMIN, "", null, 1, "", T0);
        assertTrue(l.expire(T0 + 48 * HOUR).isEmpty());            // no room: listing stays, item not lost
        assertTrue(l.listing(two.id()).isPresent());
        assertEquals(Error.EXPIRED, l.canBuy(b, two.id(), 100, T0 + 48 * HOUR));
        l.claim(a, l.mail(a).get(1).id(), true);
        assertEquals(1, l.expire(T0 + 48 * HOUR).size());
    }

    // ---------------------------------------------------------------- accounts and persistence

    @Test void namesAreCaseInsensitiveAndRenamesMoveTheAlias() {
        assertEquals(a, l.find("alice").orElseThrow());
        assertEquals(a, l.find("  ALICE ").orElseThrow());
        l.touch(a, "Alicia");
        assertTrue(l.find("alice").isEmpty());
        assertEquals(a, l.find("alicia").orElseThrow());
        l.touch(c, "Alice");                                       // name reused by another account
        assertEquals(c, l.find("alice").orElseThrow());
    }

    @Test void persistenceRoundTripKeepsEverythingAndNeverReusesIds() {
        l.credit(a, 5000); l.credit(b, 5000);
        l.deposit(a, weapon("vaulted"));
        l.send(a, b, weapon("mailed"), 250, "선물", T0);
        var listing = l.list(b, weapon("listed"), 777, 48, T0).value();
        var damaged = new CompoundTag(); damaged.putString("id", "removed_mod:thing");
        l.deposit(c, new ItemPayload(l.newId(), damaged, "", "옛 아이템", "", ""));

        var copy = new EconomyLedger();
        for (var id : l.accountIds()) copy.readAccount(l.writeAccount(id));
        copy.readListings(l.writeListings());

        for (var id : l.accountIds()) {
            assertEquals(l.glimmer(id), copy.glimmer(id));
            assertEquals(l.vault(id), copy.vault(id));
            assertEquals(l.mail(id), copy.mail(id));
        }
        assertEquals(l.listings(), copy.listings());
        assertEquals("removed_mod:thing", copy.vault(c).get(0).stack().getStringOr("id", ""));   // undecodable kept as-is
        assertEquals(b, copy.find("bob").orElseThrow());
        long fresh = copy.newId();
        assertTrue(fresh > listing.id() && fresh > listing.item().uid(), "ids continue after reload");
    }

    @Test void loadClampsCorruptBalances() {
        var t = l.writeAccount(a); t.putLong("glimmer", -50);
        var copy = new EconomyLedger(); copy.readAccount(t);
        assertEquals(0, copy.glimmer(a));
        t.putLong("glimmer", Long.MAX_VALUE); copy = new EconomyLedger(); copy.readAccount(t);
        assertEquals(GLIMMER_CAP, copy.glimmer(a));
    }

    @Test void failedOperationsDoNotMarkDirty() {
        l.drainDirty();
        l.debit(a, 1); l.withdraw(a, 42); l.send(a, a, null, 1, "", T0); l.cancel(a, 9);
        assertTrue(l.drainDirty().empty());
        l.credit(a, 1);
        assertEquals(java.util.Set.of(a), l.drainDirty().accounts());
    }

    @Test void payloadIsDefensivelyCopied() {
        var t = new CompoundTag(); t.putString("id", "minecraft:dirt");
        var p = new ItemPayload(1, t, "", "x", "", "");
        t.putString("id", "minecraft:diamond");
        p.stack().putString("id", "minecraft:emerald");
        assertEquals("minecraft:dirt", p.stack().getStringOr("id", ""));
    }
}
