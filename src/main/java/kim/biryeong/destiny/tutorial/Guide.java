package kim.biryeong.destiny.tutorial;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.activity.strike.Strikes;
import kim.biryeong.destiny.economy.EconomyLedger;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;

import java.util.*;
import java.util.function.Predicate;

/**
 * Post-tutorial "Guardian guide": four short interactive lessons played in the Tower once the first campaign is done
 * (finding a strike, engrams, dismantling, the auction house). Every action step completes on the real action: the
 * screens report through {@link #event}, and open screens are observed by polling. The Ghost narrates on the tutorial
 * HUD, the tracker lists what is left, and gifts (one engram, two practice weapons) are given once per account.
 * Progress persists, so a lesson can be replayed with {@code /안내 <주제>} without repeating the gifts.
 */
public final class Guide {
    /** Bit 0..3 lesson done; 4 offered; 8 engram gift; 9 dismantle weapon gift; 10 auction weapon gift. */
    private static final AttachmentType<Integer> STATE = AttachmentRegistry.create(DestinyGuardians.id("guide_state"),
            b -> b.persistent(Codec.INT).copyOnDeath().initializer(() -> 0));
    private static final int OFFERED = 1 << 4, GIFT_ENGRAM = 1 << 8, GIFT_DISMANTLE = 1 << 9, GIFT_AUCTION = 1 << 10;
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final Map<UUID, Integer> JOINED = new HashMap<>();
    private static boolean initialized;

    /** Things the game screens report; only the current step's trigger is consumed. */
    public enum Event { ENGRAM_DECODED, DISMANTLED, AUCTION_OPENED, SELL_OPENED, LISTED }
    private enum Trigger { TIMER, GEAR_OPEN, FINDER_OPEN, FINDER_ACTIVITY, ENGRAM_DECODED, DISMANTLED, AUCTION_OPENED, SELL_OPENED }

    private record Step(String label, Trigger trigger, int minTicks, String key, String keyAction, String ghost,
                        java.util.function.Consumer<ServerPlayer> enter, Predicate<ServerPlayer> available, String replayGhost) {
        boolean action() { return trigger != Trigger.TIMER; }
    }
    private record Lesson(String id, String name, List<Step> steps) { }

    private static Step talk(String ghost, int ticks) { return new Step(null, Trigger.TIMER, ticks, null, null, ghost, null, p -> true, null); }
    private static Step act(String label, Trigger t, String key, String keyAction, String ghost) {
        return new Step(label, t, 20, key, keyAction, ghost, null, p -> true, null);
    }
    private static Step gift(String ghost, java.util.function.Consumer<ServerPlayer> enter) {
        return new Step(null, Trigger.TIMER, 150, null, null, ghost, enter, p -> true, null);
    }
    private static Step guarded(Step s, Predicate<ServerPlayer> available, String replay) {
        return new Step(s.label, s.trigger, s.minTicks, s.key, s.keyAction, s.ghost, s.enter, available, replay);
    }

    private static final List<Lesson> LESSONS = List.of(
            new Lesson("공격전", "공격전 참가하기", List.of(
                    talk("수호자, 이제 혼자서도 활동에 나설 수 있어요. 공격전은 화력팀과 함께 도전하는 협동 임무예요. 출발하는 방법부터 같이 볼까요?", 160),
                    act("장비 화면 열기", Trigger.GEAR_OPEN, "E", "장비 화면",
                            "인벤토리 키(E)로 장비 화면을 열어요. 마우스로 커서를 움직이고, 스페이스나 좌클릭으로 고릅니다."),
                    act("화력팀 탐색기 열기", Trigger.FINDER_OPEN, "D", "화력팀 탐색기",
                            "장비 화면에서 D를 누르면 화력팀 탐색기가 열려요. 채팅창에 /화력팀 을 입력해도 열립니다."),
                    act("활동 카드 고르기", Trigger.FINDER_ACTIVITY, "클릭", "공격전 선택",
                            "활동 카드를 눌러 보세요. 이름, 권장 인원과 설명이 나오고, 상세 화면의 시작 버튼으로 출발해요. 혼자서도, 화력팀을 꾸려서도 갈 수 있어요."),
                    talk("공격전을 마치면 보상 상자와 엔그램이 나와요. 준비가 되면 언제든 출발하세요. 다음은 그 엔그램 이야기예요!", 170))),
            new Lesson("엔그램", "엔그램 얻고 해독하기", List.of(
                    talk("엔그램은 아직 열리지 않은 무기 꾸러미예요. 색이 높은 등급일수록 좋은 무기가 나옵니다. 연습용으로 하나 드릴게요.", 150),
                    gift("희귀 엔그램을 받았어요! 엔그램은 최대 10개까지 들고 다닐 수 있어요. 가득 차면 새 엔그램은 자동으로 해독돼요.", p -> {
                        if ((p.getAttachedOrElse(STATE, 0) & GIFT_ENGRAM) == 0) {
                            p.setAttached(STATE, p.getAttachedOrElse(STATE, 0) | GIFT_ENGRAM);
                            kim.biryeong.destiny.loot.Loot.storeEngram(p, "rare");
                        }
                    }),
                    act("장비 화면 열기", Trigger.GEAR_OPEN, "E", "장비 화면",
                            "다시 E로 장비 화면을 열어요. 아래쪽 엔그램 칸에 방금 받은 엔그램이 보일 거예요."),
                    guarded(act("엔그램 해독하기", Trigger.ENGRAM_DECODED, "클릭", "엔그램 해독",
                            "엔그램 칸을 선택해 해독하세요. 무기가 나와 보관함에 들어갑니다. 보관함이 가득 차 있으면 먼저 분해로 자리를 비워요."),
                            p -> !kim.biryeong.destiny.loot.Loot.profile(p).engrams().isEmpty(),
                            "지금은 해독할 엔그램이 없네요. 공격전을 클리어하면 얻을 수 있어요. 엔그램이 생기면 장비 화면의 엔그램 칸을 선택해 해독하면 됩니다."),
                    talk("해독한 무기는 보관함에 들어가요. 마음에 들면 장착하고, 아니라면 분해하거나 경매장에 팔아요. 분해를 배워 볼까요?", 170))),
            new Lesson("분해", "분해와 잠금", List.of(
                    talk("쓰지 않는 무기는 분해해서 미광체로 바꿔요. 미광체는 경매장에서 쓰는 돈이에요.", 140),
                    gift("연습용 무기를 한 자루 보관함에 넣어 드렸어요. 이 무기로 분해를 해 볼게요.", p -> giveWeapon(p, GIFT_DISMANTLE)),
                    act("장비 화면 열기", Trigger.GEAR_OPEN, "E", "장비 화면", "E로 장비 화면을 열어요."),
                    guarded(act("무기 분해하기", Trigger.DISMANTLED, "Q ×2", "분해",
                            "보관함의 무기에 커서를 올리고 Q를 두 번 누르면 분해해요. 장착 중인 무기나 잠긴 무기는 분해할 수 없어요. 아끼는 무기는 Shift로 잠가 두세요."),
                            p -> (p.getAttachedOrElse(STATE, 0) & GIFT_DISMANTLE) != 0 && hasUnlockedStored(p),
                            "분해는 보관함 무기에 커서를 올리고 Q를 두 번 누르면 돼요. 아끼는 무기는 Shift로 잠가서 실수로 분해하지 않게 하세요."),
                    talk("잘했어요! 같은 무기가 여러 개일 땐 롤이 더 좋은 쪽을 남기세요. 이제 미광체를 쓰러 경매장으로 가 볼까요?", 170))),
            new Lesson("경매장", "경매장과 거래", List.of(
                    talk("경매장에서는 다른 수호자와 무기를 사고팔아요. 값은 판매자가 정하고, 거래는 미광체로 이루어져요.", 150),
                    gift("연습용 무기를 한 자루 더 넣어 드렸어요. 직접 팔아 보세요.", p -> giveWeapon(p, GIFT_AUCTION)),
                    act("장비 화면 열기", Trigger.GEAR_OPEN, "E", "장비 화면", "E로 장비 화면을 열어요."),
                    act("경매장 열기", Trigger.AUCTION_OPENED, "W", "경매장",
                            "장비 화면에서 W를 누르면 경매장이 열려요. 채팅창의 /경매장 으로도 열 수 있고, 이름으로 검색할 수도 있어요. 마음에 드는 물건을 누르면 구매 확인 화면이 나와요."),
                    talk("판매를 등록하면 보증금 " + EconomyLedger.DEPOSIT_PERCENT + "%(최소 " + EconomyLedger.MIN_DEPOSIT
                            + ")가 들고, 팔리면 수수료 " + EconomyLedger.TAX_PERCENT + "%를 뗀 금액을 받아요. 최대 " + EconomyLedger.MAX_LISTINGS + "개까지 동시에 올릴 수 있어요.", 260),
                    act("장비 화면 다시 열기", Trigger.GEAR_OPEN, "E", "장비 화면", "경매장을 닫고 E로 장비 화면을 다시 열어요. 판매는 장비 화면에서 시작해요."),
                    guarded(act("판매 화면 열기", Trigger.SELL_OPENED, "A", "판매",
                            "판매할 무기에 커서를 올리고 A를 누르세요. 가격과 기간을 정하고 등록하면 끝이에요. 연습용 무기를 올리면 실제로 판매되니 가격은 신중하게!"),
                            p -> hasUnlockedStored(p),
                            "판매는 장비 화면에서 무기에 커서를 올리고 A를 누르면 시작해요. 잠긴 무기는 팔 수 없어요."),
                    talk("판매품은 내 판매 화면에서 취소할 수 있고, 팔린 돈과 우편은 /우편, 보관은 /창고 에서 확인해요. 이제 수호자로서 준비 끝! 전설이 되세요.", 220))));

    private static void giveWeapon(ServerPlayer p, int bit) {
        int state = p.getAttachedOrElse(STATE, 0);
        if ((state & bit) != 0) return;
        p.setAttached(STATE, state | bit);
        var table = kim.biryeong.destiny.loot.LootTables.table("engram_common");
        if (table.isEmpty()) return;
        for (int attempt = 0; attempt < 6; attempt++)
            for (var r : kim.biryeong.destiny.loot.LootRoller.roll(table.get(), p.getRandom()))
                if (r.weapon() != null) {
                    if (kim.biryeong.destiny.inventory.gear.GearAcquisition.store(p, r.weapon()) == null) return;
                    p.sendSystemMessage(Component.literal("보관함이 가득 차 연습용 무기를 드리지 못했어요. 자리를 비운 뒤 /안내 로 다시 시도하세요."));
                    p.setAttached(STATE, p.getAttachedOrElse(STATE, 0) & ~bit);
                    return;
                }
    }
    private static boolean hasUnlockedStored(ServerPlayer p) {
        for (var e : kim.biryeong.destiny.inventory.WeaponStorage.entries(p))
            if (!kim.biryeong.destiny.weapon.WeaponLock.locked(e.stack())) return true;
        return false;
    }

    private static final class Session {
        final ServerPlayer player;
        final boolean chain;
        int lesson, step = -1, stepStart, nextAt = -1, toastUntil, hintAt, closeAt = -1;
        boolean satisfied, replay;
        TutorialUi.Toast toast;
        int baselineEngrams;
        Session(ServerPlayer player, int lesson, boolean chain) { this.player = player; this.lesson = lesson; this.chain = chain; }
    }

    private Guide() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        ServerTickEvents.END_SERVER_TICK.register(Guide::tick);
        ServerPlayConnectionEvents.JOIN.register((h, s, server) -> JOINED.put(h.getPlayer().getUUID(), server.getTickCount()));
        ServerPlayConnectionEvents.DISCONNECT.register((h, server) -> {
            var s = SESSIONS.remove(h.getPlayer().getUUID());
            JOINED.remove(h.getPlayer().getUUID());
            if (s != null) TutorialUi.remove(h.getPlayer());
        });
        CommandRegistrationCallback.EVENT.register((d, access, env) -> {
            for (String name : new String[]{"안내", "guide"}) d.register(Commands.literal(name)
                    .executes(c -> command(c.getSource().getPlayerOrException(), "시작"))
                    .then(Commands.argument("항목", StringArgumentType.word())
                            .suggests((c, b) -> net.minecraft.commands.SharedSuggestionProvider.suggest(
                                    List.of("시작", "공격전", "엔그램", "분해", "경매장", "다음", "중단", "나중에"), b))
                            .executes(c -> command(c.getSource().getPlayerOrException(), StringArgumentType.getString(c, "항목")))));
        });
    }

    public static boolean active(ServerPlayer p) { return SESSIONS.containsKey(p.getUUID()); }
    public static int doneMask(ServerPlayer p) { return p.getAttachedOrElse(STATE, 0) & 0xF; }

    /** A screen reports a real player action. Cheap when no guide is running. */
    public static void event(ServerPlayer p, Event e) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.step < 0 || s.satisfied) return;
        var step = LESSONS.get(s.lesson).steps().get(s.step);
        if (!s.replay && matches(step.trigger(), e)) s.satisfied = true;
    }
    private static boolean matches(Trigger t, Event e) {
        return switch (t) {
            case ENGRAM_DECODED -> e == Event.ENGRAM_DECODED;
            case DISMANTLED -> e == Event.DISMANTLED;
            case AUCTION_OPENED -> e == Event.AUCTION_OPENED;
            case SELL_OPENED -> e == Event.SELL_OPENED || e == Event.LISTED;
            default -> false;
        };
    }

    // ------------------------------------------------------------------------------------------ commands

    private static int command(ServerPlayer p, String arg) {
        switch (arg) {
            case "중단", "나중에" -> {
                if (!end(p, true)) p.sendSystemMessage(Component.literal("진행 중인 안내가 없습니다."));
                return 1;
            }
            case "다음" -> {
                var s = SESSIONS.get(p.getUUID());
                if (s == null) { p.sendSystemMessage(Component.literal("진행 중인 안내가 없습니다.")); return 0; }
                s.satisfied = true; s.stepStart = -1000;
                return 1;
            }
            default -> { }
        }
        String blocked = blocked(p);
        if (blocked != null) { p.sendSystemMessage(Component.literal(blocked)); return 0; }
        int lesson = -1;
        for (int i = 0; i < LESSONS.size(); i++) if (LESSONS.get(i).id().equals(arg)) lesson = i;
        boolean chain = false;
        if (lesson < 0) {
            if (!arg.equals("시작")) { p.sendSystemMessage(Component.literal("알 수 없는 항목입니다.")); return 0; }
            chain = true;
            int mask = doneMask(p);
            for (int i = 0; i < LESSONS.size() && lesson < 0; i++) if ((mask & (1 << i)) == 0) lesson = i;
            if (lesson < 0) { menu(p); return 1; }
        }
        end(p, false);
        p.setAttached(STATE, p.getAttachedOrElse(STATE, 0) | OFFERED);
        SESSIONS.put(p.getUUID(), new Session(p, lesson, chain));
        return 1;
    }

    private static void menu(ServerPlayer p) {
        int mask = doneMask(p);
        p.sendSystemMessage(Component.literal("◆ 수호자 안내 — 다시 보고 싶은 항목을 누르세요").withStyle(net.minecraft.ChatFormatting.GOLD));
        for (int i = 0; i < LESSONS.size(); i++) {
            var l = LESSONS.get(i);
            final String cmd = "/안내 " + l.id();
            p.sendSystemMessage(Component.literal((((mask >> i) & 1) != 0 ? " ■ " : " □ ") + l.name())
                    .withStyle(s -> s.withColor(0x8FE3FF).withUnderlined(true).withClickEvent(new ClickEvent.RunCommand(cmd))));
        }
    }

    private static String blocked(ServerPlayer p) {
        if (!p.isAlive() || p.isSpectator() || p.hasDisconnected()) return "지금은 안내를 시작할 수 없습니다.";
        if (busy(p)) return "활동을 마친 뒤 /안내 로 시작하세요.";
        return null;
    }
    private static boolean busy(ServerPlayer p) {
        return Tutorial.active(p) || Strikes.participating(p) || kim.biryeong.destiny.campaign.RisingCampaign.participating(p)
                || kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p) || kim.biryeong.destiny.fireteam.ActivityCatalog.busy(p)
                || kim.biryeong.destiny.fireteam.Fireteams.dark(p) || kim.biryeong.destiny.down.GuardianDown.active(p)
                || kim.biryeong.destiny.tutorial.TutorialLoan.active(p);
    }

    // ------------------------------------------------------------------------------------------ driving

    private static void tick(MinecraftServer server) {
        int now = server.getTickCount();
        for (var s : List.copyOf(SESSIONS.values())) {
            var p = s.player;
            if (p.hasDisconnected() || p.isRemoved() || busy(p)) { end(p, false); continue; }
            try { drive(s, now); } catch (RuntimeException e) {
                DestinyGuardians.LOGGER.warn("[Guide] stopped for {}", p.getGameProfile().name(), e);
                end(p, false);
            }
        }
        if (now % 40 == 0) for (var p : server.getPlayerList().getPlayers()) offer(p, now);
    }

    /** One-time invitation once the first campaign is cleared and the Guardian stands in the Tower. */
    private static void offer(ServerPlayer p, int now) {
        int state = p.getAttachedOrElse(STATE, 0);
        if ((state & OFFERED) != 0 || SESSIONS.containsKey(p.getUUID()) || blocked(p) != null) return;
        if (now - JOINED.getOrDefault(p.getUUID(), now) < 200) return;
        boolean cleared = p.getAttachedOrElse(kim.biryeong.destiny.campaign.RisingCampaign.COMPLETED_REVISION, 0) > 0
                || p.getAttachedOrElse(Tutorial.COMPLETED_REVISION, 0) >= Tutorial.REQUIRED_REVISION;
        if (!cleared || !kim.biryeong.destiny.loot.Loot.profile(p).starter()) return;
        if (screenOpen(p)) return;
        p.setAttached(STATE, state | OFFERED);
        p.sendSystemMessage(Component.literal(""));
        p.sendSystemMessage(Component.literal("◆ 고스트: 수호자, 이제부터가 진짜예요.").withStyle(net.minecraft.ChatFormatting.AQUA));
        p.sendSystemMessage(Component.literal("   공격전 참가, 엔그램, 분해, 경매장을 짧게 안내해 드릴까요?"));
        p.sendSystemMessage(Component.literal("   ")
                .append(Component.literal("[ 안내 시작 ]").withStyle(st -> st.withColor(0xF2C14E).withBold(true).withClickEvent(new ClickEvent.RunCommand("/안내 시작"))))
                .append(Component.literal("   "))
                .append(Component.literal("[ 나중에 ]").withStyle(st -> st.withColor(0xA9B2BC).withClickEvent(new ClickEvent.RunCommand("/안내 나중에"))))
                .append(Component.literal("   (언제든 /안내)").withStyle(net.minecraft.ChatFormatting.DARK_GRAY)));
        p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, .8f, 1.6f);
    }

    private static boolean screenOpen(ServerPlayer p) {
        return kim.biryeong.destiny.inventory.gear.GearScreen.active(p) || kim.biryeong.destiny.fireteam.FinderScreen.active(p);
    }

    private static void drive(Session s, int now) {
        var p = s.player;
        var lesson = LESSONS.get(s.lesson);
        if (s.nextAt >= 0) {            // between lessons
            if (now >= s.nextAt) { s.nextAt = -1; s.lesson++; s.step = -1; }
            render(s, now);
            return;
        }
        if (s.closeAt >= 0) {
            if (now >= s.closeAt) end(p, false); else if (now % 2 == 0) renderToast(s);
            return;
        }
        if (s.step < 0) { enter(s, 0, now); return; }
        var step = lesson.steps().get(s.step);
        if (!s.replay && !s.satisfied) {
            switch (step.trigger()) {
                case GEAR_OPEN -> s.satisfied = kim.biryeong.destiny.inventory.gear.GearScreen.active(p);
                case FINDER_OPEN -> s.satisfied = kim.biryeong.destiny.fireteam.FinderScreen.active(p);
                case FINDER_ACTIVITY -> s.satisfied = kim.biryeong.destiny.fireteam.FinderScreen.onActivityPage(p);
                default -> { }
            }
        }
        int elapsed = now - s.stepStart;
        boolean ready = step.action() && !s.replay ? s.satisfied && elapsed >= 20
                : elapsed >= step.minTicks() && !screenOpen(p);
        if (ready) {
            if (step.action() && !s.replay) stepDone(s, step, now);
            if (s.step + 1 >= lesson.steps().size()) { lessonDone(s, now); return; }
            enter(s, s.step + 1, now);
            return;
        }
        // Screens hide the world HUD; keep the instruction reachable on the action bar.
        if (screenOpen(p) && step.action() && !s.replay && now >= s.hintAt) {
            s.hintAt = now + 60;
            p.sendOverlayMessage(Component.literal("◆ " + step.label() + "  [" + step.key() + "] " + step.keyAction()).withColor(TutorialUi.GOLD));
        }
        if (now % 2 == 0) render(s, now);
    }

    private static void enter(Session s, int index, int now) {
        var p = s.player;
        var step = LESSONS.get(s.lesson).steps().get(index);
        s.step = index; s.stepStart = now; s.satisfied = false; s.hintAt = now;
        s.replay = !step.available().test(p);
        if (step.enter() != null) step.enter().accept(p);
        if (step.enter() != null) {     // a gift step announces itself
            toast(s, "연습용 선물", "보관함을 확인해 보세요", TutorialUi.GOLD, 100, now);
            p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.PLAYER_LEVELUP, SoundSource.PLAYERS, .45f, 1.6f);
        }
        render(s, now);
    }

    private static void stepDone(Session s, Step step, int now) {
        var p = s.player;
        toast(s, "✔ " + step.label(), LESSONS.get(s.lesson).name(), TutorialUi.DONE, 70, now);
        p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, .7f, 1.3f);
    }

    private static void lessonDone(Session s, int now) {
        var p = s.player;
        int state = p.getAttachedOrElse(STATE, 0) | (1 << s.lesson);
        p.setAttached(STATE, state);
        p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, .8f, 1f);
        boolean more = s.chain && s.lesson + 1 < LESSONS.size();
        toast(s, "안내 완료 · " + LESSONS.get(s.lesson).name(), more ? "잠시 후 다음 안내가 이어집니다" : "언제든 /안내 로 다시 볼 수 있어요",
                TutorialUi.GOLD, 90, now);
        if (more) { s.nextAt = now + 100; s.step = LESSONS.get(s.lesson).steps().size(); render(s, now); return; }
        s.nextAt = -1;
        s.step = -2;                    // finished: keep the final toast up briefly, then close
        s.closeAt = now + 95;
        renderToast(s);
    }

    private static void renderToast(Session s) {
        TutorialUi.render(s.player, new TutorialUi.View("수호자 안내", 1, 1, "", List.of(), null, null, null,
                s.toast, null, false));
    }

    private static boolean end(ServerPlayer p, boolean say) {
        var s = SESSIONS.remove(p.getUUID());
        if (s == null) return false;
        TutorialUi.remove(p);
        if (say) p.sendSystemMessage(Component.literal("안내를 마칩니다. /안내 로 언제든 다시 볼 수 있어요."));
        return true;
    }

    private static void toast(Session s, String title, String sub, int color, int ticks, int now) {
        s.toast = new TutorialUi.Toast(title, sub, color);
        s.toastUntil = now + ticks;
    }

    private static void render(Session s, int now) {
        var p = s.player;
        if (s.toast != null && now >= s.toastUntil) s.toast = null;
        var lesson = LESSONS.get(Math.min(s.lesson, LESSONS.size() - 1));
        var objectives = new ArrayList<TutorialUi.Objective>();
        for (int i = 0; i < lesson.steps().size(); i++) {
            var st = lesson.steps().get(i);
            if (!st.action()) continue;
            boolean skipped = i == s.step && s.replay || !st.available().test(p) && i > s.step;
            if (skipped) continue;
            boolean done = s.step > i || i == s.step && s.satisfied;
            objectives.add(new TutorialUi.Objective(st.label(), done ? 1 : 0, 1));
        }
        Step current = s.step >= 0 && s.step < lesson.steps().size() ? lesson.steps().get(s.step) : null;
        String ghost = current == null ? null : s.replay && current.replayGhost() != null ? current.replayGhost() : current.ghost();
        String key = current != null && current.action() && !s.replay ? current.key() : null;
        TutorialUi.render(p, new TutorialUi.View("수호자 안내", s.lesson + 1, LESSONS.size(), lesson.name(), objectives,
                key, current == null ? null : current.keyAction(), ghost, s.toast, null, screenOpen(p)));
    }
}
