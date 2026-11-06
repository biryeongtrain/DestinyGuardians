package kim.biryeong.destiny.economy;

import net.minecraft.nbt.CompoundTag;
import net.minecraft.nbt.ListTag;
import net.minecraft.nbt.Tag;

import java.util.*;

/**
 * Authoritative economy state: Glimmer balances, vaults, postmasters and auction listings for every Guardian who
 * ever joined, online or not. Pure bookkeeping with no Minecraft player access, so every rule and edge case is
 * unit-tested ({@code EconomyLedgerTest}). All mutations must run on one thread (the server thread); each returns a
 * {@link Result} and changes nothing when it fails. Every successful mutation records the accounts it touched in
 * {@link #drainDirty()} so persistence can flush exactly those files.
 *
 * <p>Items are opaque {@link ItemPayload}s; moving them in and out of a player's inventory is {@link Economy}'s job.
 */
public final class EconomyLedger {
    /**
     * No gameplay balance cap (trading economy, user decision 2026-11-06). This is only an arithmetic ceiling far
     * above any reachable balance so that sums can never overflow a long.
     */
    public static final long GLIMMER_CAP = 1_000_000_000_000_000L;
    public static final int VAULT_CAP = 100;
    /** Destiny's postmaster holds 21; player-sent mail respects it, system deliveries may exceed it up to {@link #SYSTEM_MAIL_CAP}. */
    public static final int POSTMASTER_CAP = 21, SYSTEM_MAIL_CAP = 200;
    public static final int MAX_LISTINGS = 10, MAX_MESSAGE = 60;
    public static final long MIN_PRICE = 10, MAX_PRICE = 1_000_000_000L;
    public static final long HOUR = 3_600_000L;
    public static final List<Integer> DURATIONS_HOURS = List.of(12, 24, 48);
    /** Non-refundable listing deposit: 1% of the price, at least {@link #MIN_DEPOSIT}. Sales tax: 5% of the price. */
    public static final long MIN_DEPOSIT = 10;
    public static final int DEPOSIT_PERCENT = 1, TAX_PERCENT = 5;
    public static final UUID SYSTEM = new UUID(0, 0);

    public enum Error {
        UNKNOWN_ACCOUNT("계정을 찾을 수 없습니다."),
        INVALID_AMOUNT("금액이 올바르지 않습니다."),
        INSUFFICIENT_GLIMMER("미광체가 부족합니다."),
        GLIMMER_CAP("처리할 수 없는 미광체 금액입니다."),
        VAULT_FULL("창고가 가득 찼습니다."),
        NOT_FOUND("대상이 이미 사라졌습니다. 목록을 새로 고칩니다."),
        RECIPIENT_FULL("받는 사람의 우편함이 가득 찼습니다."),
        SELF_MAIL("자기 자신에게는 우편을 보낼 수 없습니다."),
        MESSAGE_TOO_LONG("메시지가 너무 깁니다."),
        EMPTY_MAIL("보낼 아이템이나 미광체가 없습니다."),
        LISTING_LIMIT("동시에 등록할 수 있는 판매품은 " + MAX_LISTINGS + "개입니다."),
        PRICE_RANGE("가격은 " + String.format("%,d", MIN_PRICE) + "~" + String.format("%,d", MAX_PRICE) + " 미광체 사이여야 합니다."),
        DURATION("판매 기간이 올바르지 않습니다."),
        NOT_A_WEAPON("경매장에는 무기만 등록할 수 있습니다."),
        OWN_LISTING("자신의 판매품은 구매할 수 없습니다."),
        NOT_SELLER("자신의 판매품만 취소할 수 있습니다."),
        EXPIRED("판매 기간이 끝난 물품입니다."),
        PRICE_CHANGED("가격이 바뀌었습니다. 다시 확인하세요."),
        MAILBOX_OVERFLOW("우편함이 넘쳐 처리할 수 없습니다.");
        public final String message;
        Error(String message) { this.message = message; }
    }

    public record Result<T>(T value, Error error) {
        public static <T> Result<T> ok(T v) { return new Result<>(v, null); }
        public static <T> Result<T> fail(Error e) { return new Result<>(null, e); }
        public boolean ok() { return error == null; }
    }

    public enum MailKind { PLAYER, AUCTION_ITEM, AUCTION_RETURN, AUCTION_SALE, OVERFLOW, ADMIN, LOST_ITEM }

    /** One postmaster entry: an item, Glimmer, or both. */
    public record Mail(long id, UUID from, String fromName, MailKind kind, ItemPayload item, long glimmer,
                       String message, long sentAt) {
        public Mail { fromName = fromName == null ? "" : fromName; message = message == null ? "" : message; }
        public boolean system() { return kind != MailKind.PLAYER; }
        Mail withGlimmer(long g) { return new Mail(id, from, fromName, kind, item, g, message, sentAt); }
        Mail withoutItem() { return new Mail(id, from, fromName, kind, null, glimmer, message, sentAt); }
    }

    public record Listing(long id, UUID seller, String sellerName, ItemPayload item, long price, long createdAt, long expiresAt) { }

    /** A finished purchase: who got paid and what the buyer received. */
    public record Sale(Listing listing, long tax, long proceeds, boolean proceedsMailed) { }

    static final class Account {
        final UUID id;
        String name;
        long glimmer;
        final List<ItemPayload> vault = new ArrayList<>();
        final List<Mail> mail = new ArrayList<>();
        Account(UUID id, String name) { this.id = id; this.name = name == null ? "" : name; }
    }

    private final Map<UUID, Account> accounts = new HashMap<>();
    private final Map<String, UUID> byName = new HashMap<>();
    private final TreeMap<Long, Listing> listings = new TreeMap<>();
    private long nextId = 1;
    private final Set<UUID> dirty = new HashSet<>();
    private boolean dirtyListings;

    // ------------------------------------------------------------------ accounts

    /** Create or rename an account (on join). Names are unique case-insensitively; a stale holder loses the alias. */
    public void touch(UUID id, String name) {
        var a = accounts.computeIfAbsent(id, k -> { dirty.add(k); return new Account(k, name); });
        if (name != null && !name.isBlank()) {
            String key = name.toLowerCase(Locale.ROOT);
            if (!name.equals(a.name)) { byName.remove(a.name.toLowerCase(Locale.ROOT), id); a.name = name; dirty.add(id); }
            byName.put(key, id);
        }
    }

    public boolean known(UUID id) { return accounts.containsKey(id); }
    public Optional<UUID> find(String name) { return name == null ? Optional.empty() : Optional.ofNullable(byName.get(name.trim().toLowerCase(Locale.ROOT))); }
    public String name(UUID id) { var a = accounts.get(id); return a == null ? "" : a.name; }
    public Collection<UUID> accountIds() { return List.copyOf(accounts.keySet()); }

    public long newId() { return nextId++; }

    // ------------------------------------------------------------------ glimmer

    public long glimmer(UUID id) { var a = accounts.get(id); return a == null ? 0 : a.glimmer; }
    /** Room left under the cap. */
    public long room(UUID id) { return GLIMMER_CAP - glimmer(id); }

    /** Add exactly {@code amount}, or fail without change when it would pass the cap. */
    public Result<Long> credit(UUID id, long amount) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (amount < 0) return Result.fail(Error.INVALID_AMOUNT);
        if (amount > GLIMMER_CAP - a.glimmer) return Result.fail(Error.GLIMMER_CAP);
        a.glimmer += amount; dirty.add(id);
        return Result.ok(a.glimmer);
    }

    /** Add up to the cap; returns the amount that did not fit. Used for rewards, where overflow is simply lost (Destiny). */
    public long creditCapped(UUID id, long amount) {
        var a = accounts.get(id);
        if (a == null || amount <= 0) return Math.max(0, amount);
        long fit = Math.min(amount, GLIMMER_CAP - a.glimmer);
        a.glimmer += fit; if (fit > 0) dirty.add(id);
        return amount - fit;
    }

    public Result<Long> debit(UUID id, long amount) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (amount < 0) return Result.fail(Error.INVALID_AMOUNT);
        if (a.glimmer < amount) return Result.fail(Error.INSUFFICIENT_GLIMMER);
        a.glimmer -= amount; dirty.add(id);
        return Result.ok(a.glimmer);
    }

    public Result<Long> set(UUID id, long amount) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (amount < 0 || amount > GLIMMER_CAP) return Result.fail(Error.INVALID_AMOUNT);
        a.glimmer = amount; dirty.add(id);
        return Result.ok(amount);
    }

    // ------------------------------------------------------------------ vault

    public List<ItemPayload> vault(UUID id) { var a = accounts.get(id); return a == null ? List.of() : List.copyOf(a.vault); }

    public Result<ItemPayload> deposit(UUID id, ItemPayload item) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (a.vault.size() >= VAULT_CAP) return Result.fail(Error.VAULT_FULL);
        a.vault.add(item); dirty.add(id);
        return Result.ok(item);
    }

    /** Look up a vault item by uid without removing it (the caller checks it can be placed first). */
    public Optional<ItemPayload> vaultItem(UUID id, long uid) {
        var a = accounts.get(id);
        return a == null ? Optional.empty() : a.vault.stream().filter(i -> i.uid() == uid).findFirst();
    }

    public Result<ItemPayload> withdraw(UUID id, long uid) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        for (var it = a.vault.iterator(); it.hasNext(); ) {
            var i = it.next();
            if (i.uid() == uid) { it.remove(); dirty.add(id); return Result.ok(i); }
        }
        return Result.fail(Error.NOT_FOUND);
    }

    // ------------------------------------------------------------------ postmaster

    public List<Mail> mail(UUID id) { var a = accounts.get(id); return a == null ? List.of() : List.copyOf(a.mail); }
    public int playerMailCount(UUID id) { return (int) mail(id).stream().filter(m -> !m.system()).count(); }

    /** Player-to-player mail: an item and/or Glimmer (debited from the sender). */
    public Result<Mail> send(UUID from, UUID to, ItemPayload item, long glimmer, String message, long now) {
        var s = accounts.get(from); var r = accounts.get(to);
        if (s == null || r == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (from.equals(to)) return Result.fail(Error.SELF_MAIL);
        if (glimmer < 0) return Result.fail(Error.INVALID_AMOUNT);
        if (item == null && glimmer == 0) return Result.fail(Error.EMPTY_MAIL);
        if (message != null && message.codePointCount(0, message.length()) > MAX_MESSAGE) return Result.fail(Error.MESSAGE_TOO_LONG);
        if (playerMailCount(to) >= POSTMASTER_CAP) return Result.fail(Error.RECIPIENT_FULL);
        if (s.glimmer < glimmer) return Result.fail(Error.INSUFFICIENT_GLIMMER);
        s.glimmer -= glimmer; dirty.add(from);
        var m = new Mail(newId(), from, s.name, MailKind.PLAYER, item, glimmer, message, now);
        r.mail.add(m); dirty.add(to);
        return Result.ok(m);
    }

    /** System delivery (auction, overflow, admin). Exempt from the player cap so nothing earned is ever lost. */
    public Result<Mail> deliver(UUID to, MailKind kind, String fromName, ItemPayload item, long glimmer, String message, long now) {
        var r = accounts.get(to);
        if (r == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        if (kind == MailKind.PLAYER || glimmer < 0 || (item == null && glimmer == 0)) return Result.fail(Error.INVALID_AMOUNT);
        if (r.mail.size() >= SYSTEM_MAIL_CAP) return Result.fail(Error.MAILBOX_OVERFLOW);
        var m = new Mail(newId(), SYSTEM, fromName, kind, item, glimmer, message, now);
        r.mail.add(m); dirty.add(to);
        return Result.ok(m);
    }

    public Optional<Mail> mailItem(UUID id, long mailId) {
        return mail(id).stream().filter(m -> m.id() == mailId).findFirst();
    }

    /**
     * Claim mail {@code mailId}. Glimmer is credited up to the cap; any remainder stays in the mail. The item is
     * returned to the caller only when {@code takeItem} (the caller has verified it can be placed); otherwise it stays.
     * The mail disappears once both parts are claimed. Fails without change when nothing could be claimed.
     */
    public Result<Mail> claim(UUID id, long mailId, boolean takeItem) {
        var a = accounts.get(id);
        if (a == null) return Result.fail(Error.UNKNOWN_ACCOUNT);
        int index = -1;
        for (int i = 0; i < a.mail.size(); i++) if (a.mail.get(i).id() == mailId) { index = i; break; }
        if (index < 0) return Result.fail(Error.NOT_FOUND);
        var m = a.mail.get(index);
        long fit = Math.min(m.glimmer(), GLIMMER_CAP - a.glimmer);
        boolean item = takeItem && m.item() != null;
        if (fit == 0 && !item) return Result.fail(m.glimmer() > 0 ? Error.GLIMMER_CAP : Error.NOT_FOUND);
        a.glimmer += fit;
        var rest = m.withGlimmer(m.glimmer() - fit);
        if (item) rest = rest.withoutItem();
        if (rest.item() == null && rest.glimmer() == 0) a.mail.remove(index); else a.mail.set(index, rest);
        dirty.add(id);
        // Claimed view: what was handed over.
        return Result.ok(new Mail(m.id(), m.from(), m.fromName(), m.kind(), item ? m.item() : null, fit, m.message(), m.sentAt()));
    }

    // ------------------------------------------------------------------ auction

    public static long deposit(long price) { return Math.max(MIN_DEPOSIT, price * DEPOSIT_PERCENT / 100); }
    public static long tax(long price) { return price * TAX_PERCENT / 100; }

    public List<Listing> listings() { return List.copyOf(listings.values()); }
    public Optional<Listing> listing(long id) { return Optional.ofNullable(listings.get(id)); }
    public List<Listing> listingsOf(UUID seller) { return listings.values().stream().filter(l -> l.seller().equals(seller)).toList(); }

    /** Validate a listing before the caller removes the item from the seller's inventory. */
    public Error canList(UUID seller, ItemPayload item, long price, int hours) {
        var a = accounts.get(seller);
        if (a == null) return Error.UNKNOWN_ACCOUNT;
        if (item == null || !item.weapon()) return Error.NOT_A_WEAPON;
        if (price < MIN_PRICE || price > MAX_PRICE) return Error.PRICE_RANGE;
        if (!DURATIONS_HOURS.contains(hours)) return Error.DURATION;
        if (listingsOf(seller).size() >= MAX_LISTINGS) return Error.LISTING_LIMIT;
        if (a.glimmer < deposit(price)) return Error.INSUFFICIENT_GLIMMER;
        return null;
    }

    public Result<Listing> list(UUID seller, ItemPayload item, long price, int hours, long now) {
        var e = canList(seller, item, price, hours);
        if (e != null) return Result.fail(e);
        var a = accounts.get(seller);
        a.glimmer -= deposit(price); dirty.add(seller);
        var l = new Listing(newId(), seller, a.name, item, price, now, now + hours * HOUR);
        listings.put(l.id(), l); dirtyListings = true;
        return Result.ok(l);
    }

    /** Validate a purchase before the caller reserves inventory space. */
    public Error canBuy(UUID buyer, long listingId, long expectedPrice, long now) {
        var b = accounts.get(buyer);
        if (b == null) return Error.UNKNOWN_ACCOUNT;
        var l = listings.get(listingId);
        if (l == null) return Error.NOT_FOUND;
        if (l.expiresAt() <= now) return Error.EXPIRED;
        if (l.seller().equals(buyer)) return Error.OWN_LISTING;
        if (l.price() != expectedPrice) return Error.PRICE_CHANGED;
        if (b.glimmer < l.price()) return Error.INSUFFICIENT_GLIMMER;
        if (!accounts.containsKey(l.seller())) return Error.UNKNOWN_ACCOUNT;
        return null;
    }

    /**
     * Pay for a listing. The buyer is debited, the seller credited with price minus tax (into the postmaster when
     * the balance cap would be passed). The listing is removed; the caller hands the returned item to the buyer.
     */
    public Result<Sale> buy(UUID buyer, long listingId, long expectedPrice, long now) {
        var e = canBuy(buyer, listingId, expectedPrice, now);
        if (e != null) return Result.fail(e);
        var l = listings.get(listingId);
        var s = accounts.get(l.seller());
        long tax = tax(l.price()), proceeds = l.price() - tax;
        boolean mailed = proceeds > GLIMMER_CAP - s.glimmer;
        if (mailed && s.mail.size() >= SYSTEM_MAIL_CAP) return Result.fail(Error.MAILBOX_OVERFLOW);
        accounts.get(buyer).glimmer -= l.price(); dirty.add(buyer);
        listings.remove(listingId); dirtyListings = true;
        if (mailed) deliver(l.seller(), MailKind.AUCTION_SALE, "경매장", null, proceeds, l.item().name() + " 판매 대금", now);
        else { s.glimmer += proceeds; dirty.add(l.seller()); }
        return Result.ok(new Sale(l, tax, proceeds, mailed));
    }

    /** Seller cancels: the listing is removed and its item returned to the caller (the deposit is not refunded). */
    public Result<Listing> cancel(UUID seller, long listingId) {
        var l = listings.get(listingId);
        if (l == null) return Result.fail(Error.NOT_FOUND);
        if (!l.seller().equals(seller)) return Result.fail(Error.NOT_SELLER);
        listings.remove(listingId); dirtyListings = true;
        return Result.ok(l);
    }

    /** Return every listing whose time is up to its seller's postmaster. Returns the expired listings. */
    public List<Listing> expire(long now) {
        var out = new ArrayList<Listing>();
        for (var l : List.copyOf(listings.values())) {
            if (l.expiresAt() > now) continue;
            if (!accounts.containsKey(l.seller())) continue;
            var r = deliver(l.seller(), MailKind.AUCTION_RETURN, "경매장", l.item(), 0, "판매 기간 만료: " + l.item().name(), now);
            if (!r.ok()) continue;   // mailbox overflow: keep listing (unbuyable once expired) and retry later
            listings.remove(l.id()); dirtyListings = true; out.add(l);
        }
        return out;
    }

    // ------------------------------------------------------------------ persistence

    /** Accounts changed since the last drain, plus whether listings changed. Clears the set. */
    public record Dirty(Set<UUID> accounts, boolean listings) { public boolean empty() { return accounts.isEmpty() && !listings; } }
    public Dirty drainDirty() {
        var d = new Dirty(Set.copyOf(dirty), dirtyListings);
        dirty.clear(); dirtyListings = false;
        return d;
    }
    public void markAllDirty() { dirty.addAll(accounts.keySet()); dirtyListings = true; }

    public CompoundTag writeAccount(UUID id) {
        var a = accounts.get(id);
        var t = new CompoundTag();
        if (a == null) return t;
        t.putString("uuid", id.toString()); t.putString("name", a.name); t.putLong("glimmer", a.glimmer);
        var vault = new ListTag(); for (var i : a.vault) vault.add(i.write()); t.put("vault", vault);
        var mail = new ListTag();
        for (var m : a.mail) {
            var c = new CompoundTag();
            c.putLong("id", m.id()); c.putString("from", m.from().toString()); c.putString("fromName", m.fromName());
            c.putString("kind", m.kind().name()); if (m.item() != null) c.put("item", m.item().write());
            c.putLong("glimmer", m.glimmer()); c.putString("message", m.message()); c.putLong("sentAt", m.sentAt());
            mail.add(c);
        }
        t.put("mail", mail);
        return t;
    }

    public CompoundTag writeListings() {
        var t = new CompoundTag();
        t.putLong("nextId", nextId);
        var list = new ListTag();
        for (var l : listings.values()) {
            var c = new CompoundTag();
            c.putLong("id", l.id()); c.putString("seller", l.seller().toString()); c.putString("sellerName", l.sellerName());
            c.put("item", l.item().write()); c.putLong("price", l.price()); c.putLong("createdAt", l.createdAt()); c.putLong("expiresAt", l.expiresAt());
            list.add(c);
        }
        t.put("listings", list);
        return t;
    }

    /** Load one account file. Unparseable entries are kept as damaged payloads by {@link ItemPayload}; never dropped. */
    public void readAccount(CompoundTag t) {
        var id = UUID.fromString(t.getStringOr("uuid", ""));
        var a = new Account(id, t.getStringOr("name", ""));
        a.glimmer = Math.clamp(t.getLongOr("glimmer", 0), 0, GLIMMER_CAP);
        for (Tag v : t.getListOrEmpty("vault")) if (v instanceof CompoundTag c) { var p = ItemPayload.read(c); a.vault.add(p); bump(p.uid()); }
        for (Tag v : t.getListOrEmpty("mail")) if (v instanceof CompoundTag c) {
            var item = c.contains("item") ? ItemPayload.read(c.getCompoundOrEmpty("item")) : null;
            if (item != null) bump(item.uid());
            MailKind kind;
            try { kind = MailKind.valueOf(c.getStringOr("kind", "ADMIN")); } catch (IllegalArgumentException e) { kind = MailKind.ADMIN; }
            var m = new Mail(c.getLongOr("id", 0), UUID.fromString(c.getStringOr("from", SYSTEM.toString())), c.getStringOr("fromName", ""),
                    kind, item, Math.max(0, c.getLongOr("glimmer", 0)), c.getStringOr("message", ""), c.getLongOr("sentAt", 0));
            bump(m.id()); a.mail.add(m);
        }
        accounts.put(id, a);
        if (!a.name.isEmpty()) byName.put(a.name.toLowerCase(Locale.ROOT), id);
    }

    public void readListings(CompoundTag t) {
        nextId = Math.max(nextId, t.getLongOr("nextId", 1));
        for (Tag v : t.getListOrEmpty("listings")) if (v instanceof CompoundTag c) {
            var l = new Listing(c.getLongOr("id", 0), UUID.fromString(c.getStringOr("seller", SYSTEM.toString())), c.getStringOr("sellerName", ""),
                    ItemPayload.read(c.getCompoundOrEmpty("item")), c.getLongOr("price", 0), c.getLongOr("createdAt", 0), c.getLongOr("expiresAt", 0));
            bump(l.id()); bump(l.item().uid());
            listings.put(l.id(), l);
        }
    }

    private void bump(long used) { if (used >= nextId) nextId = used + 1; }
}
