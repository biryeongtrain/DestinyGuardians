package kim.biryeong.destiny.economy;

import kim.biryeong.destiny.economy.EconomyLedger.Listing;
import kim.biryeong.destiny.economy.EconomyLedger.Mail;
import kim.biryeong.destiny.weapon.WeaponRarity;
import net.minecraft.ChatFormatting;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.MutableComponent;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.SimpleContainer;
import net.minecraft.world.SimpleMenuProvider;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.inventory.ChestMenu;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.inventory.MenuType;
import net.minecraft.world.item.Item;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.ItemLore;

import java.util.*;
import java.util.function.IntConsumer;

/**
 * Server-side chest GUIs for the vault, postmaster, mail composer and auction house. Nothing in these menus is a
 * real container slot: every click is intercepted, resolved against the {@link EconomyLedger} by id (so a click on a
 * stale view fails cleanly with NOT_FOUND), and the client is resynchronised. Player inventory rows act as item
 * pickers. One menu per player; server thread only.
 */
public final class EconomyMenus {
    static final Identifier GLIMMER_ICON = Identifier.parse("destiny:gui/hud/bungie/currency_glimmer");
    static final Identifier VAULT_ICON = Identifier.parse("destiny:gui/hud/bungie/vendor_vault");
    static final Identifier POSTMASTER_ICON = Identifier.parse("destiny:gui/hud/bungie/vendor_postmaster");
    private static final int ROWS = 6, CONTENT = 45, PAGE = 45;
    private static final Map<UUID, Menu> OPEN = new HashMap<>();

    private EconomyMenus() { }
    static void init() { }

    // ================================================================== framework

    /** A clickable cell: what it shows and what a click does ({@code right} = right click, {@code shift} = shift click). */
    record Cell(ItemStack icon, Click click) { }
    interface Click { void run(boolean right, boolean shift); }

    abstract static class Screen {
        abstract Component title(Menu m);
        abstract void draw(Menu m, Map<Integer, Cell> cells);
        /** A click on the player's own inventory slot {@code index} (0..35). */
        void inventory(Menu m, int index) { }
    }

    static final class Menu extends ChestMenu {
        final ServerPlayer owner;
        final Screen screen;
        final SimpleContainer box;
        final Map<Integer, Cell> cells = new HashMap<>();
        int lastClick = Integer.MIN_VALUE / 2;
        String notice = "";
        boolean noticeGood;
        int noticeUntil;

        Menu(int id, ServerPlayer owner, Screen screen, SimpleContainer box) {
            super(MenuType.GENERIC_9x6, id, owner.getInventory(), box, ROWS);
            this.owner = owner; this.screen = screen; this.box = box;
        }

        void redraw() {
            cells.clear();
            screen.draw(this, cells);
            // Feedback inside the panel (the action bar sits behind the dimmed menu). Slot 52 is free on every screen.
            if (!notice.isEmpty() && owner.level().getServer().getTickCount() < noticeUntil)
                cells.put(52, new Cell(econStyled(noticeGood ? "confirm" : "cancel",
                        text(notice, noticeGood ? ChatFormatting.GREEN : ChatFormatting.RED)), null));
            for (int i = 0; i < ROWS * 9; i++) {
                var c = cells.get(i);
                box.setItem(i, c == null ? filler() : c.icon());
            }
            broadcastChanges();
        }

        @Override public void clicked(int slot, int button, ContainerInput input, Player player) {
            try {
                if (player != owner || Economy.ledger() == null) return;
                int now = owner.level().getServer().getTickCount();
                if (now - lastClick < 2 || (input != ContainerInput.PICKUP && input != ContainerInput.QUICK_MOVE)) return;
                lastClick = now;
                boolean right = button == 1, shift = input == ContainerInput.QUICK_MOVE;
                if (slot >= 0 && slot < ROWS * 9) {
                    var c = cells.get(slot);
                    if (c != null && c.click() != null) c.click().run(right, shift);
                } else if (slot >= ROWS * 9 && slot < ROWS * 9 + 36) {
                    int local = slot - ROWS * 9;               // 0..26 main inventory, 27..35 hotbar
                    int index = local < 27 ? local + 9 : local - 27;
                    screen.inventory(this, index);
                }
            } finally {
                // Undo any client-side prediction (cursor, moved stacks) and show the server's truth.
                setCarried(ItemStack.EMPTY);
                if (OPEN.get(owner.getUUID()) == this) redraw();
                sendAllDataToRemote();
            }
        }

        @Override public ItemStack quickMoveStack(Player player, int slot) { return ItemStack.EMPTY; }
        @Override public boolean stillValid(Player player) { return player == owner && owner.isAlive() && !owner.hasDisconnected(); }
        @Override public void removed(Player player) {
            box.clearContent();          // display copies only; never hand them to the player
            super.removed(player);
            OPEN.remove(owner.getUUID(), this);
        }
    }

    static void open(ServerPlayer p, Screen screen) {
        var ledger = Economy.ledger();
        if (ledger == null) { p.sendSystemMessage(Component.literal("경제 시스템을 사용할 수 없습니다.")); return; }
        String blocked = blocked(p);
        if (blocked != null) { p.sendOverlayMessage(Component.literal(blocked)); return; }
        ledger.touch(p.getUUID(), p.getGameProfile().name());
        var holder = new Menu[1];
        p.openMenu(new SimpleMenuProvider((id, inv, pl) -> {
            var m = new Menu(id, p, screen, new SimpleContainer(ROWS * 9));
            holder[0] = m; return m;
        }, screen.title(null)));
        if (holder[0] != null) { OPEN.put(p.getUUID(), holder[0]); holder[0].redraw(); holder[0].sendAllDataToRemote(); }
    }

    /** Entry points for the gear screen keys (W auction, S vault, A sell the hovered weapon). */
    public static void openVault(ServerPlayer p) { open(p, new VaultScreen()); }
    public static void openAuction(ServerPlayer p) { open(p, new AuctionScreen("")); }
    /** Null when the sell screen opened with inventory slot {@code index} picked, else why not. */
    public static String sellable(ServerPlayer p, int index) {
        String why = Economy.movable(p, index);
        if (why == null && kim.biryeong.destiny.weapon.WeaponItems.entry(p.getInventory().getItem(index)).isEmpty())
            why = EconomyLedger.Error.NOT_A_WEAPON.message;
        if (why == null && kim.biryeong.destiny.weapon.WeaponLock.locked(p.getInventory().getItem(index)))
            why = "잠긴 무기는 판매할 수 없습니다.";
        return why;
    }
    public static void openSell(ServerPlayer p, int index) {
        var sell = new SellScreen();
        if (sellable(p, index) == null) { sell.index = index; sell.picked = p.getInventory().getItem(index); }
        open(p, sell);
    }

    static String blocked(ServerPlayer p) {
        if (!p.isAlive() || p.isSpectator() || p.hasDisconnected()) return "지금은 열 수 없습니다.";
        if (kim.biryeong.destiny.inventory.gear.GearScreen.active(p)) return "장비 화면을 닫은 뒤 여세요.";
        if (kim.biryeong.destiny.down.GuardianDown.active(p)) return "쓰러진 상태에서는 열 수 없습니다.";
        if (kim.biryeong.destiny.tutorial.TutorialLoan.active(p)) return "실습 중에는 열 수 없습니다.";
        return null;
    }

    static void refresh(UUID id) { var m = OPEN.get(id); if (m != null) m.redraw(); }
    static void refreshAll() { for (var m : List.copyOf(OPEN.values())) m.redraw(); }
    static void closeAll(MinecraftServer server) {
        for (var m : List.copyOf(OPEN.values())) if (!m.owner.hasDisconnected()) m.owner.closeContainer();
        OPEN.clear();
    }
    /** QA: run a click on the player's open economy menu through the same path as a client click packet. */
    static boolean qaClick(ServerPlayer p, int slot, boolean right, boolean shift) {
        var m = OPEN.get(p.getUUID());
        if (m == null || p.containerMenu != m) return false;
        m.lastClick = Integer.MIN_VALUE / 2;
        m.clicked(slot, right ? 1 : 0, shift ? ContainerInput.QUICK_MOVE : ContainerInput.PICKUP, p);
        return true;
    }
    /** QA: chest slot (0..53) or player inventory index (0..35) as a menu slot. */
    static int inventorySlot(int index) { return ROWS * 9 + (index < 9 ? 27 + index : index - 9); }

    /** Open screen of a player, for QA status. */
    static Optional<String> describe(ServerPlayer p) {
        var m = OPEN.get(p.getUUID());
        return m == null ? Optional.empty() : Optional.of(m.screen.getClass().getSimpleName() + " notice=" + m.notice);
    }

    static void say(Menu m, EconomyLedger.Error e) { say(m, e.message, false); }
    static void say(Menu m, String text, boolean good) {
        m.notice = text; m.noticeGood = good; m.noticeUntil = m.owner.level().getServer().getTickCount() + 80;
        m.owner.sendOverlayMessage(Component.literal(text).withStyle(good ? ChatFormatting.GREEN : ChatFormatting.RED));
        m.owner.level().playSound(null, m.owner.blockPosition(), good ? SoundEvents.EXPERIENCE_ORB_PICKUP : SoundEvents.VILLAGER_NO,
                SoundSource.PLAYERS, .5f, good ? 1.2f : 1f);
    }

    // ================================================================== icons

    static ItemStack filler() { return ItemStack.EMPTY; }

    static final Identifier TOOLTIP = Identifier.parse("destiny:econ");
    /** Vanilla stand-ins mapped to the Destiny button icons (destiny:gui/econ/*). */
    private static final Map<Item, String> ICONS = Map.ofEntries(
            Map.entry(Items.ARROW, "next"), Map.entry(Items.BARRIER, "cancel"), Map.entry(Items.ITEM_FRAME, "attach"),
            Map.entry(Items.NAME_TAG, "send"), Map.entry(Items.HOPPER, "filter"), Map.entry(Items.AMETHYST_SHARD, "filter"),
            Map.entry(Items.COMPARATOR, "sort"), Map.entry(Items.BOOK, "listings"), Map.entry(Items.GOLD_INGOT, "sell"),
            Map.entry(Items.CLOCK, "clock"), Map.entry(Items.PAPER, "auction"), Map.entry(Items.STRUCTURE_VOID, "empty"),
            Map.entry(Items.CONCRETE.lime(), "confirm"), Map.entry(Items.CONCRETE.red(), "cancel"),
            Map.entry(Items.STAINED_GLASS_PANE.lime(), "plus"), Map.entry(Items.STAINED_GLASS_PANE.red(), "minus"));

    static ItemStack named(Item item, Component name, Component... lore) {
        String icon = ICONS.get(item);
        var s = icon == null ? new ItemStack(item) : econ(icon);
        return style(s, name, Arrays.asList(lore));
    }
    static ItemStack econStyled(String icon, Component name) {
        var s = econ(icon); s.set(DataComponents.ENCHANTMENT_GLINT_OVERRIDE, true); return style(s, name, List.of());
    }
    /** Clear expired notices (server tick, every 10 ticks). */
    static void tick(MinecraftServer server) {
        int now = server.getTickCount();
        for (var m : List.copyOf(OPEN.values()))
            if (!m.notice.isEmpty() && now >= m.noticeUntil && now - m.noticeUntil < 10) m.redraw();
    }
    static ItemStack econ(String icon) {
        var s = new ItemStack(Items.PAPER);
        s.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/econ/" + icon));
        return s;
    }
    /** Destiny tooltip: Noto name and lore, dark tooltip frame. */
    static ItemStack style(ItemStack s, Component name, List<Component> lore) {
        s.set(DataComponents.CUSTOM_NAME, font(name));
        if (!lore.isEmpty()) s.set(DataComponents.LORE, new ItemLore(lore.stream().map(EconomyMenus::font).toList()));
        s.set(DataComponents.TOOLTIP_STYLE, TOOLTIP);
        return s;
    }
    static Component font(Component c) { return c.copy().withStyle(st -> st.withItalic(false).withFont(EconomyGui.TEXT)); }
    static ItemStack icon(Identifier model, Component name, Component... lore) {
        var s = new ItemStack(Items.PAPER); s.set(DataComponents.ITEM_MODEL, model);
        return style(s, name, Arrays.asList(lore));
    }
    static Component plain(Component c) { return c.copy().withStyle(st -> st.withItalic(false)); }
    static MutableComponent text(String s, ChatFormatting... f) { return Component.literal(s).withStyle(f); }
    static String glimmer(long v) { return String.format("%,d", v); }

    static ItemStack balance(ServerPlayer p) {
        return icon(GLIMMER_ICON, text("미광체 " + glimmer(Economy.ledger().glimmer(p.getUUID())), ChatFormatting.AQUA));
    }

    static int rarityColor(String rarity) { return WeaponRarity.parse(rarity).map(WeaponRarity::color).orElse(0xFFFFFF); }
    static String rarityLabel(String rarity) { return WeaponRarity.parse(rarity).map(WeaponRarity::label).orElse(""); }
    static String slotLabel(String slot) {
        return switch (slot) { case "KINETIC" -> "물리"; case "ENERGY" -> "에너지"; case "POWER" -> "파워"; default -> ""; };
    }

    /** A display copy of a ledger item with extra lore. Undecodable payloads show as a damaged placeholder. */
    static ItemStack show(ItemPayload item, List<Component> extra) {
        var stack = Economy.stack(item).map(ItemStack::copy).orElse(null);
        var lore = new ArrayList<Component>();
        if (stack == null) {
            stack = new ItemStack(Items.BARRIER);
            lore.add(text("데이터를 읽을 수 없는 아이템입니다. 관리자에게 문의하세요.", ChatFormatting.RED));
        }
        if (item.weapon()) lore.add(text(rarityLabel(item.rarity()) + " · " + slotLabel(item.slot()) + " 무기", ChatFormatting.GRAY));
        else if (stack.getCount() > 1) lore.add(text("수량 " + stack.getCount(), ChatFormatting.GRAY));
        lore.addAll(extra);
        return style(stack, Component.literal(item.name()).withColor(rarityColor(item.rarity())), lore);
    }

    static void pager(Map<Integer, Cell> cells, int page, int pages, IntConsumer go) {
        if (page > 0) cells.put(45, new Cell(icon(Identifier.parse("destiny:gui/econ/prev"), text("이전 페이지", ChatFormatting.WHITE), text((page) + "/" + pages, ChatFormatting.GRAY)), (r, s) -> go.accept(page - 1)));
        if (page + 1 < pages) cells.put(53, new Cell(named(Items.ARROW, text("다음 페이지", ChatFormatting.WHITE), text((page + 2) + "/" + pages, ChatFormatting.GRAY)), (r, s) -> go.accept(page + 1)));
    }
    static int pages(int count) { return Math.max(1, (count + PAGE - 1) / PAGE); }

    static String remaining(long ms) {
        if (ms <= 0) return "만료";
        long m = ms / 60_000;
        return m >= 60 ? (m / 60) + "시간 " + (m % 60) + "분" : Math.max(1, m) + "분";
    }

    // ================================================================== vault

    static final class VaultScreen extends Screen {
        int page;
        @Override Component title(Menu m) { return EconomyGui.title("vault", "창고"); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            var l = Economy.ledger(); var id = m.owner.getUUID();
            var items = l.vault(id);
            page = Math.min(page, pages(items.size()) - 1);
            for (int i = 0; i < PAGE && page * PAGE + i < items.size(); i++) {
                var item = items.get(page * PAGE + i);
                cells.put(i, new Cell(show(item, List.of(text("클릭: 인벤토리로 꺼내기", ChatFormatting.YELLOW))), (r, s) -> withdraw(m, item.uid())));
            }
            cells.put(49, new Cell(icon(VAULT_ICON, text("창고 " + items.size() + "/" + EconomyLedger.VAULT_CAP, ChatFormatting.WHITE),
                    text("아래 인벤토리의 아이템을 클릭하면 보관합니다.", ChatFormatting.GRAY),
                    text("장착 중인 무기(1~3번 칸)는 보관할 수 없습니다.", ChatFormatting.GRAY)), null));
            cells.put(47, new Cell(balance(m.owner), null));
            pager(cells, page, pages(items.size()), p -> { page = p; m.redraw(); });
        }
        @Override void inventory(Menu m, int index) {
            String why = Economy.movable(m.owner, index);
            if (why != null) { say(m, why, false); return; }
            var l = Economy.ledger();
            if (l.vault(m.owner.getUUID()).size() >= EconomyLedger.VAULT_CAP) { say(m, EconomyLedger.Error.VAULT_FULL); return; }
            var payload = Economy.take(m.owner, index);
            var r = l.deposit(m.owner.getUUID(), payload);
            if (!r.ok()) { Economy.restore(m.owner, index, payload); say(m, r.error()); }
            else say(m, payload.name() + " 보관", true);
            Economy.commit(m.owner);
        }
        private void withdraw(Menu m, long uid) {
            var l = Economy.ledger();
            var item = l.vaultItem(m.owner.getUUID(), uid);
            if (item.isEmpty()) { say(m, EconomyLedger.Error.NOT_FOUND); return; }
            var stack = Economy.stack(item.get());
            if (stack.isEmpty()) { say(m, "손상된 아이템은 꺼낼 수 없습니다.", false); return; }
            String why = Economy.canReceive(m.owner, stack.get());
            if (why != null) { say(m, why, false); return; }
            var r = l.withdraw(m.owner.getUUID(), uid);
            if (!r.ok()) { say(m, r.error()); return; }
            String err = Economy.place(m.owner, stack.get());
            if (err != null) { l.deposit(m.owner.getUUID(), r.value()); say(m, err, false); }
            else say(m, item.get().name() + " 꺼내기", true);
            Economy.commit(m.owner);
        }
    }

    // ================================================================== postmaster

    static final class MailScreen extends Screen {
        int page;
        @Override Component title(Menu m) { return EconomyGui.title("mail", "우편함"); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            var mail = Economy.ledger().mail(m.owner.getUUID());
            page = Math.min(page, pages(mail.size()) - 1);
            for (int i = 0; i < PAGE && page * PAGE + i < mail.size(); i++) {
                var x = mail.get(page * PAGE + i);
                cells.put(i, new Cell(mailIcon(x), (r, s) -> claim(m, x.id(), true)));
            }
            int players = Economy.ledger().playerMailCount(m.owner.getUUID());
            cells.put(49, new Cell(icon(Identifier.parse("destiny:gui/econ/claim_all"), text("모두 받기", ChatFormatting.GREEN),
                    text("우편 " + mail.size() + "개 · 수호자 우편 " + players + "/" + EconomyLedger.POSTMASTER_CAP, ChatFormatting.GRAY),
                    text("자리가 없는 아이템은 우편함에 남습니다.", ChatFormatting.GRAY)), (r, s) -> claimAll(m)));
            cells.put(47, new Cell(balance(m.owner), null));
            pager(cells, page, pages(mail.size()), p -> { page = p; m.redraw(); });
        }
        static ItemStack mailIcon(Mail x) {
            var extra = new ArrayList<Component>();
            extra.add(text("보낸 이: " + (x.fromName().isEmpty() ? "시스템" : x.fromName()), ChatFormatting.GRAY));
            if (x.glimmer() > 0) extra.add(text("미광체 " + glimmer(x.glimmer()), ChatFormatting.AQUA));
            if (!x.message().isEmpty()) extra.add(text("“" + x.message() + "”", ChatFormatting.WHITE));
            extra.add(text("클릭: 받기", ChatFormatting.YELLOW));
            if (x.item() != null) return show(x.item(), extra);
            var name = text(x.kind() == EconomyLedger.MailKind.AUCTION_SALE ? "판매 대금" : "미광체", ChatFormatting.AQUA);
            return icon(GLIMMER_ICON, name, extra.toArray(Component[]::new));
        }
        /** Claim one mail. Returns true when anything was received. */
        static boolean claim(Menu m, long id, boolean loud) {
            var l = Economy.ledger(); var me = m.owner.getUUID();
            var mail = l.mailItem(me, id);
            if (mail.isEmpty()) { if (loud) say(m, EconomyLedger.Error.NOT_FOUND); return false; }
            ItemStack stack = null; String why = null;
            if (mail.get().item() != null) {
                var decoded = Economy.stack(mail.get().item());
                if (decoded.isEmpty()) why = "손상된 아이템은 받을 수 없습니다.";
                else { stack = decoded.get(); why = Economy.canReceive(m.owner, stack); }
            }
            var r = l.claim(me, id, stack != null && why == null);
            if (!r.ok()) { if (loud) say(m, why != null ? why : r.error().message, false); return false; }
            if (r.value().item() != null) {
                String err = Economy.place(m.owner, stack);
                if (err != null) l.deliver(me, EconomyLedger.MailKind.OVERFLOW, "시스템", r.value().item(), 0, mail.get().message(), Economy.now());
            }
            Economy.commit(m.owner);
            if (loud) {
                var got = new StringBuilder();
                if (r.value().item() != null) got.append(r.value().item().name());
                if (r.value().glimmer() > 0) got.append(got.isEmpty() ? "" : " · ").append("미광체 ").append(glimmer(r.value().glimmer()));
                boolean partial = why != null || r.value().glimmer() < mail.get().glimmer();
                say(m, got + " 받음" + (partial ? " (일부는 우편함에 남았습니다: " + (why != null ? why : "미광체") + ")" : ""), true);
            }
            return true;
        }
        private void claimAll(Menu m) {
            int n = 0;
            for (var x : Economy.ledger().mail(m.owner.getUUID())) if (claim(m, x.id(), false)) n++;
            int left = Economy.ledger().mail(m.owner.getUUID()).size();
            if (n == 0) say(m, left == 0 ? "받을 우편이 없습니다." : "받을 수 있는 우편이 없습니다. 인벤토리 공간을 확인하세요.", false);
            else say(m, n + "개를 받았습니다." + (left > 0 ? " " + left + "개는 남았습니다." : ""), true);
        }
    }

    // ================================================================== mail composer

    static final class SendScreen extends Screen {
        final UUID to; final String toName; final String message;
        int index = -1; ItemStack picked = ItemStack.EMPTY; long amount;
        SendScreen(UUID to, String toName, String message) { this.to = to; this.toName = toName; this.message = message == null ? "" : message; }
        @Override Component title(Menu m) { return EconomyGui.title("send", "우편 보내기 · " + toName); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            if (index >= 0 && m.owner.getInventory().getItem(index) != picked) { index = -1; picked = ItemStack.EMPTY; }
            if (index >= 0) cells.put(13, new Cell(show(Economy.payloadPreview(picked), List.of(text("클릭: 첨부 해제", ChatFormatting.YELLOW))), (r, s) -> { index = -1; picked = ItemStack.EMPTY; m.redraw(); }));
            else cells.put(13, new Cell(named(Items.ITEM_FRAME, text("첨부할 아이템", ChatFormatting.WHITE), text("아래 인벤토리에서 클릭하세요. (선택)", ChatFormatting.GRAY)), null));
            stepper(cells, 18, amount, Economy.ledger().glimmer(m.owner.getUUID()), v -> { amount = v; m.redraw(); }, "보낼 미광체");
            cells.put(31, new Cell(named(Items.NAME_TAG, text("받는 사람: " + toName, ChatFormatting.WHITE),
                    text(message.isEmpty() ? "메시지 없음" : "“" + message + "”", ChatFormatting.GRAY)), null));
            cells.put(45, new Cell(named(Items.BARRIER, text("취소", ChatFormatting.RED)), (r, s) -> m.owner.closeContainer()));
            cells.put(47, new Cell(balance(m.owner), null));
            cells.put(49, new Cell(named(Items.CONCRETE.lime(), text("보내기", ChatFormatting.GREEN),
                    text((index >= 0 ? "아이템 1개" : "아이템 없음") + " · 미광체 " + glimmer(amount), ChatFormatting.GRAY)), (r, s) -> send(m)));
        }
        @Override void inventory(Menu m, int i) {
            String why = Economy.movable(m.owner, i);
            if (why != null) { say(m, why, false); return; }
            index = i; picked = m.owner.getInventory().getItem(i);
        }
        private void send(Menu m) {
            var l = Economy.ledger(); var me = m.owner.getUUID();
            if (index >= 0 && m.owner.getInventory().getItem(index) != picked) { say(m, "첨부한 아이템이 바뀌었습니다. 다시 선택하세요.", false); index = -1; return; }
            if (index < 0 && amount == 0) { say(m, EconomyLedger.Error.EMPTY_MAIL); return; }
            if (index >= 0) { String why = Economy.movable(m.owner, index); if (why != null) { say(m, why, false); return; } }
            if (l.playerMailCount(to) >= EconomyLedger.POSTMASTER_CAP) { say(m, EconomyLedger.Error.RECIPIENT_FULL); return; }
            ItemPayload payload = index >= 0 ? Economy.take(m.owner, index) : null;
            var r = l.send(me, to, payload, amount, message, Economy.now());
            if (!r.ok()) { if (payload != null) Economy.restore(m.owner, index, payload); say(m, r.error()); Economy.commit(m.owner); return; }
            Economy.commit(m.owner);
            Economy.notify(to, m.owner.getGameProfile().name() + "님이 우편을 보냈습니다. /우편");
            refresh(to);
            say(m, toName + "님에게 우편을 보냈습니다.", true);
            index = -1; picked = ItemStack.EMPTY; amount = 0;
        }
    }

    /** Glimmer amount stepper on row {@code base}/9 (9 cells): -10000 -1000 -100 -10 [value] +10 +100 +1000 +10000. */
    static void stepper(Map<Integer, Cell> cells, int base, long value, long max, java.util.function.LongConsumer set, String label) {
        long[] steps = {-10_000, -1_000, -100, -10, 0, 10, 100, 1_000, 10_000};
        for (int i = 0; i < 9; i++) {
            long step = steps[i];
            if (step == 0) {
                cells.put(base + i, new Cell(icon(GLIMMER_ICON, text(label + ": " + glimmer(value), ChatFormatting.AQUA),
                        text("좌클릭 ±, 우클릭 ×10", ChatFormatting.GRAY)), null));
                continue;
            }
            var item = step > 0 ? Items.STAINED_GLASS_PANE.lime() : Items.STAINED_GLASS_PANE.red();
            cells.put(base + i, new Cell(named(item, text((step > 0 ? "+" : "") + glimmer(step), step > 0 ? ChatFormatting.GREEN : ChatFormatting.RED),
                    text("우클릭: " + (step > 0 ? "+" : "") + glimmer(step * 10), ChatFormatting.GRAY)),
                    (r, s) -> set.accept(Math.clamp(value + (r ? step * 10 : step), 0, Math.max(0, max)))));
        }
    }

    // ================================================================== auction

    enum Sort { NEWEST("최신순"), PRICE_LOW("낮은 가격순"), PRICE_HIGH("높은 가격순"), ENDING("마감 임박순");
        final String label; Sort(String l) { label = l; } }
    private static final List<String> SLOTS = Arrays.asList(null, "KINETIC", "ENERGY", "POWER");
    private static final List<String> RARITIES = Arrays.asList(null, "common", "uncommon", "rare", "legendary", "exotic");

    static final class AuctionScreen extends Screen {
        int page; String slot; String rarity; Sort sort = Sort.NEWEST; final String query;
        AuctionScreen(String query) { this.query = query == null ? "" : query.trim(); }
        @Override Component title(Menu m) { return EconomyGui.title("auction", query.isEmpty() ? "경매장" : "경매장 · " + query); }
        List<Listing> visible() {
            long now = Economy.now();
            var q = query.toLowerCase(Locale.ROOT);
            var out = new ArrayList<>(Economy.ledger().listings().stream()
                    .filter(l -> l.expiresAt() > now)
                    .filter(l -> slot == null || slot.equals(l.item().slot()))
                    .filter(l -> rarity == null || rarity.equals(l.item().rarity()))
                    .filter(l -> q.isEmpty() || l.item().name().toLowerCase(Locale.ROOT).contains(q) || l.item().weaponId().contains(q))
                    .toList());
            out.sort(switch (sort) {
                case NEWEST -> Comparator.comparingLong(Listing::createdAt).reversed().thenComparingLong(Listing::id);
                case PRICE_LOW -> Comparator.comparingLong(Listing::price).thenComparingLong(Listing::id);
                case PRICE_HIGH -> Comparator.comparingLong(Listing::price).reversed().thenComparingLong(Listing::id);
                case ENDING -> Comparator.comparingLong(Listing::expiresAt).thenComparingLong(Listing::id);
            });
            return out;
        }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            var list = visible(); long now = Economy.now(); var me = m.owner.getUUID();
            page = Math.min(page, pages(list.size()) - 1);
            for (int i = 0; i < PAGE && page * PAGE + i < list.size(); i++) {
                var l = list.get(page * PAGE + i);
                boolean mine = l.seller().equals(me);
                cells.put(i, new Cell(show(l.item(), List.of(
                        text("가격 " + glimmer(l.price()) + " 미광체", ChatFormatting.AQUA),
                        text("판매자 " + l.sellerName() + " · 남은 시간 " + remaining(l.expiresAt() - now), ChatFormatting.GRAY),
                        text(mine ? "내 판매품 · 클릭: 판매 취소" : "클릭: 구매", ChatFormatting.YELLOW))),
                        (r, s) -> open(m.owner, new ConfirmScreen(l.id(), l.price(), mine, this))));
            }
            if (list.isEmpty()) cells.put(22, new Cell(named(Items.STRUCTURE_VOID, text("등록된 무기가 없습니다.", ChatFormatting.GRAY)), null));
            cells.put(46, new Cell(named(Items.HOPPER, text("무기 칸: " + (slot == null ? "전체" : slotLabel(slot)), ChatFormatting.WHITE)),
                    (r, s) -> { slot = cycle(SLOTS, slot); page = 0; m.redraw(); }));
            cells.put(47, new Cell(named(Items.AMETHYST_SHARD, text("등급: " + (rarity == null ? "전체" : rarityLabel(rarity)), ChatFormatting.WHITE)),
                    (r, s) -> { rarity = cycle(RARITIES, rarity); page = 0; m.redraw(); }));
            cells.put(48, new Cell(named(Items.COMPARATOR, text("정렬: " + sort.label, ChatFormatting.WHITE)),
                    (r, s) -> { sort = Sort.values()[(sort.ordinal() + 1) % Sort.values().length]; page = 0; m.redraw(); }));
            cells.put(49, new Cell(balance(m.owner), null));
            cells.put(50, new Cell(named(Items.BOOK, text("내 판매 목록 (" + Economy.ledger().listingsOf(me).size() + "/" + EconomyLedger.MAX_LISTINGS + ")", ChatFormatting.WHITE)),
                    (r, s) -> open(m.owner, new MyListingsScreen())));
            cells.put(51, new Cell(named(Items.GOLD_INGOT, text("무기 판매 등록", ChatFormatting.GOLD),
                    text("아래 인벤토리의 무기를 클릭해도 됩니다.", ChatFormatting.GRAY)), (r, s) -> open(m.owner, new SellScreen())));
            pager(cells, page, pages(list.size()), p -> { page = p; m.redraw(); });
        }
        @Override void inventory(Menu m, int index) {
            var sell = new SellScreen(); sell.pick(m, index);
            if (sell.index >= 0) open(m.owner, sell);
        }
    }

    static <T> T cycle(List<T> values, T current) { return values.get((values.indexOf(current) + 1) % values.size()); }

    static final class ConfirmScreen extends Screen {
        final long listing, price; final boolean cancel; final Screen back;
        ConfirmScreen(long listing, long price, boolean cancel, Screen back) { this.listing = listing; this.price = price; this.cancel = cancel; this.back = back; }
        @Override Component title(Menu m) { return EconomyGui.title("confirm", cancel ? "판매 취소 확인" : "구매 확인"); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            var l = Economy.ledger().listing(listing);
            if (l.isEmpty()) { cells.put(22, new Cell(named(Items.BARRIER, text("이미 판매되었거나 취소된 물품입니다.", ChatFormatting.RED)), (r, s) -> open(m.owner, back))); return; }
            cells.put(13, new Cell(show(l.get().item(), List.of(text("가격 " + glimmer(l.get().price()) + " 미광체", ChatFormatting.AQUA),
                    text("판매자 " + l.get().sellerName(), ChatFormatting.GRAY))), null));
            cells.put(29, new Cell(named(Items.CONCRETE.lime(), text(cancel ? "판매 취소" : "구매", ChatFormatting.GREEN),
                    text(cancel ? "무기는 우편함으로 돌아옵니다. 등록 보증금은 돌려받지 않습니다." : glimmer(price) + " 미광체를 지불합니다.", ChatFormatting.GRAY)),
                    (r, s) -> { if (cancel) cancel(m); else buy(m); }));
            cells.put(33, new Cell(named(Items.CONCRETE.red(), text("돌아가기", ChatFormatting.RED)), (r, s) -> open(m.owner, back)));
            cells.put(49, new Cell(balance(m.owner), null));
        }
        private void buy(Menu m) {
            var l = Economy.ledger(); var me = m.owner.getUUID(); long now = Economy.now();
            var e = l.canBuy(me, listing, price, now);
            if (e != null) { say(m, e); return; }
            var listingItem = l.listing(listing).orElseThrow().item();
            var stack = Economy.stack(listingItem);
            if (stack.isEmpty()) { say(m, "손상된 물품은 구매할 수 없습니다.", false); return; }
            // An item that does not fit goes to the buyer's postmaster instead of failing the purchase.
            boolean fits = Economy.canReceive(m.owner, stack.get()) == null;
            var r = l.buy(me, listing, price, now);
            if (!r.ok()) { say(m, r.error()); return; }
            var sale = r.value();
            String err = fits ? Economy.place(m.owner, stack.get()) : "공간 부족";
            if (err != null) l.deliver(me, EconomyLedger.MailKind.AUCTION_ITEM, "경매장", sale.listing().item(), 0, "구매한 물품 (인벤토리 공간 부족)", now);
            Economy.commit(m.owner);
            Economy.notify(sale.listing().seller(), sale.listing().item().name() + " 판매 완료: " + glimmer(sale.proceeds()) + " 미광체 (수수료 "
                    + glimmer(sale.tax()) + ")" + (sale.proceedsMailed() ? " · 우편함에 보관" : ""));
            refreshAll();
            say(m, sale.listing().item().name() + " 구매" + (err != null ? " · 우편함으로 보냈습니다" : ""), true);
            open(m.owner, back);
        }
        private void cancel(Menu m) {
            var l = Economy.ledger(); var me = m.owner.getUUID();
            var r = l.cancel(me, listing);
            if (!r.ok()) { say(m, r.error()); return; }
            l.deliver(me, EconomyLedger.MailKind.AUCTION_RETURN, "경매장", r.value().item(), 0, "판매 취소: " + r.value().item().name(), Economy.now());
            Economy.commit(m.owner);
            refreshAll();
            say(m, "판매를 취소했습니다. 무기는 우편함에 있습니다.", true);
            open(m.owner, back);
        }
    }

    static final class MyListingsScreen extends Screen {
        @Override Component title(Menu m) { return EconomyGui.title("listings", "내 판매 목록"); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            var list = Economy.ledger().listingsOf(m.owner.getUUID()); long now = Economy.now();
            for (int i = 0; i < list.size() && i < PAGE; i++) {
                var l = list.get(i);
                cells.put(i, new Cell(show(l.item(), List.of(text("가격 " + glimmer(l.price()) + " 미광체", ChatFormatting.AQUA),
                        text("남은 시간 " + remaining(l.expiresAt() - now), ChatFormatting.GRAY), text("클릭: 판매 취소", ChatFormatting.YELLOW))),
                        (r, s) -> open(m.owner, new ConfirmScreen(l.id(), l.price(), true, this))));
            }
            cells.put(45, new Cell(icon(Identifier.parse("destiny:gui/econ/prev"), text("경매장으로", ChatFormatting.WHITE)), (r, s) -> open(m.owner, new AuctionScreen(""))));
            cells.put(49, new Cell(balance(m.owner), null));
        }
    }

    static final class SellScreen extends Screen {
        int index = -1; ItemStack picked = ItemStack.EMPTY; long price = 1_000; int hours = 24;
        @Override Component title(Menu m) { return EconomyGui.title("sell", "무기 판매 등록"); }
        void pick(Menu m, int i) {
            String why = sellable(m.owner, i);
            if (why != null) { say(m, why, false); return; }
            index = i; picked = m.owner.getInventory().getItem(i);
        }
        @Override void inventory(Menu m, int i) { pick(m, i); }
        @Override void draw(Menu m, Map<Integer, Cell> cells) {
            if (index >= 0 && m.owner.getInventory().getItem(index) != picked) { index = -1; picked = ItemStack.EMPTY; }
            if (index >= 0) cells.put(13, new Cell(show(Economy.payloadPreview(picked), List.of(text("다른 무기를 고르려면 인벤토리에서 클릭", ChatFormatting.GRAY))), null));
            else cells.put(13, new Cell(named(Items.ITEM_FRAME, text("판매할 무기", ChatFormatting.WHITE), text("아래 인벤토리에서 무기를 클릭하세요.", ChatFormatting.GRAY)), null));
            stepper(cells, 18, price, EconomyLedger.MAX_PRICE, v -> { price = Math.max(EconomyLedger.MIN_PRICE, v); m.redraw(); }, "판매 가격");
            cells.put(30, new Cell(named(Items.CLOCK, text("판매 기간: " + hours + "시간", ChatFormatting.WHITE), text("클릭: 변경", ChatFormatting.GRAY)),
                    (r, s) -> { hours = cycle(EconomyLedger.DURATIONS_HOURS, hours); m.redraw(); }));
            long deposit = EconomyLedger.deposit(price), tax = EconomyLedger.tax(price);
            cells.put(32, new Cell(named(Items.PAPER, text("정산 미리보기", ChatFormatting.WHITE),
                    text("등록 보증금 " + glimmer(deposit) + " (돌려받지 않음)", ChatFormatting.GRAY),
                    text("판매 수수료 " + EconomyLedger.TAX_PERCENT + "% · " + glimmer(tax), ChatFormatting.GRAY),
                    text("판매 시 수령 " + glimmer(price - tax) + " 미광체", ChatFormatting.AQUA)), null));
            cells.put(45, new Cell(icon(Identifier.parse("destiny:gui/econ/prev"), text("경매장으로", ChatFormatting.WHITE)), (r, s) -> open(m.owner, new AuctionScreen(""))));
            cells.put(47, new Cell(balance(m.owner), null));
            cells.put(49, new Cell(named(Items.CONCRETE.lime(), text("등록", ChatFormatting.GREEN),
                    text(glimmer(price) + " 미광체 · " + hours + "시간", ChatFormatting.GRAY)), (r, s) -> list(m)));
        }
        private void list(Menu m) {
            var l = Economy.ledger(); var me = m.owner.getUUID();
            if (index < 0) { say(m, "판매할 무기를 먼저 고르세요.", false); return; }
            if (m.owner.getInventory().getItem(index) != picked) { say(m, "선택한 무기가 바뀌었습니다. 다시 고르세요.", false); index = -1; return; }
            String why = sellable(m.owner, index);
            if (why != null) { say(m, why, false); return; }
            var preview = Economy.payloadPreview(picked);
            var e = l.canList(me, preview, price, hours);
            if (e != null) { say(m, e); return; }
            var payload = Economy.take(m.owner, index);
            var r = l.list(me, payload, price, hours, Economy.now());
            if (!r.ok()) { Economy.restore(m.owner, index, payload); say(m, r.error()); Economy.commit(m.owner); return; }
            Economy.commit(m.owner);
            refreshAll();
            say(m, payload.name() + " 등록 · " + glimmer(price) + " 미광체", true);
            open(m.owner, new MyListingsScreen());
        }
    }
}
