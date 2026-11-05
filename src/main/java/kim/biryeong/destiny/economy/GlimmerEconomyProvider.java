package kim.biryeong.destiny.economy;

import com.mojang.authlib.GameProfile;
import eu.pb4.common.economy.api.*;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;

import java.math.BigInteger;
import java.util.Collection;
import java.util.List;
import java.util.UUID;

/**
 * Exposes Glimmer through Patbox's Common Economy API so other economy-aware mods (shops, /pay, leaderboards) read
 * and change the same balance as the vault/postmaster/auction. All calls go to {@link EconomyLedger}; the non-negative and
 * overflow rules apply to every caller.
 */
public final class GlimmerEconomyProvider implements EconomyProvider {
    public static final String ID = "destiny";
    public static final GlimmerEconomyProvider INSTANCE = new GlimmerEconomyProvider();
    private final Currency currency = new Currency();

    private GlimmerEconomyProvider() { }

    public static void register() { CommonEconomy.register(ID, INSTANCE); }

    @Override public Component name() { return Component.literal("Destiny Guardians"); }

    @Override public EconomyAccount getAccount(MinecraftServer server, GameProfile profile, String id) {
        if (!Economy.GLIMMER_ACCOUNT.equals(id)) return null;
        var ledger = Economy.ledger(server);
        if (ledger == null) return null;
        ledger.touch(profile.id(), profile.name());
        return new Account(profile.id());
    }

    @Override public Collection<EconomyAccount> getAccounts(MinecraftServer server, GameProfile profile) {
        var a = getAccount(server, profile, Economy.GLIMMER_ACCOUNT);
        return a == null ? List.of() : List.of(a);
    }

    @Override public EconomyCurrency getCurrency(MinecraftServer server, String id) { return Economy.GLIMMER_ACCOUNT.equals(id) ? currency : null; }
    @Override public Collection<EconomyCurrency> getCurrencies(MinecraftServer server) { return List.of(currency); }
    @Override public String defaultAccount(MinecraftServer server, GameProfile profile, EconomyCurrency c) { return Economy.GLIMMER_ACCOUNT; }
    @Override public String id() { return ID; }

    private final class Currency implements EconomyCurrency {
        @Override public Component name() { return Component.literal("미광체"); }
        @Override public Identifier id() { return Identifier.fromNamespaceAndPath(ID, Economy.GLIMMER_ACCOUNT); }
        @Override public String formatValue(BigInteger value, boolean precise) { return String.format("%,d", value) + " 미광체"; }
        @Override public BigInteger parseValue(String value) {
            var v = new BigInteger(value.replace(",", "").replace("미광체", "").trim());
            if (v.signum() < 0) throw new NumberFormatException("negative");
            return v;
        }
        @Override public EconomyProvider provider() { return GlimmerEconomyProvider.this; }
    }

    private final class Account implements EconomyAccount {
        private final UUID owner;
        Account(UUID owner) { this.owner = owner; }
        private EconomyLedger ledger() { return Economy.ledger(); }
        @Override public Component name() { return Component.literal("미광체"); }
        @Override public UUID owner() { return owner; }
        @Override public Identifier id() { return currency.id(); }
        @Override public BigInteger balance() { var l = ledger(); return BigInteger.valueOf(l == null ? 0 : l.glimmer(owner)); }

        @Override public EconomyTransaction canIncreaseBalance(BigInteger amount) { return check(amount, true, false); }
        @Override public EconomyTransaction canDecreaseBalance(BigInteger amount) { return check(amount, false, false); }
        @Override public EconomyTransaction increaseBalance(BigInteger amount) { return check(amount, true, true); }
        @Override public EconomyTransaction decreaseBalance(BigInteger amount) { return check(amount, false, true); }

        private EconomyTransaction check(BigInteger amount, boolean add, boolean apply) {
            var l = ledger();
            BigInteger before = balance();
            if (l == null || amount.signum() < 0 || amount.bitLength() > 62)
                return fail(before, amount, EconomyLedger.Error.INVALID_AMOUNT.message);
            long v = amount.longValue();
            EconomyLedger.Error error = null;
            if (add && v > l.room(owner)) error = EconomyLedger.Error.GLIMMER_CAP;
            if (!add && v > l.glimmer(owner)) error = EconomyLedger.Error.INSUFFICIENT_GLIMMER;
            if (error != null) return fail(before, amount, error.message);
            if (apply) { var r = add ? l.credit(owner, v) : l.debit(owner, v); if (!r.ok()) return fail(before, amount, r.error().message); Economy.changed(owner); }
            BigInteger after = apply ? balance() : (add ? before.add(amount) : before.subtract(amount));
            return new EconomyTransaction.Simple(true, Component.literal("완료"), after, before, amount, this);
        }

        private EconomyTransaction fail(BigInteger before, BigInteger amount, String why) {
            return new EconomyTransaction.Simple(false, Component.literal(why), before, before, amount, this);
        }

        @Override public void setBalance(BigInteger value) {
            var l = ledger();
            if (l == null || value.signum() < 0 || value.bitLength() > 62) return;
            l.set(owner, Math.min(value.longValue(), EconomyLedger.GLIMMER_CAP)); Economy.changed(owner);
        }
        @Override public EconomyProvider provider() { return GlimmerEconomyProvider.this; }
        @Override public EconomyCurrency currency() { return currency; }
    }
}
