package kim.biryeong.destiny.test;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.fx.PostEffects;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import javax.imageio.ImageIO;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

/** H17 HUD state through embedded owners and real HUD entities; no client rendering claims. */
public final class SuperReadyHudGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String DIAMOND = "destiny:hud_super_diamond";
    private static final String ICON = "destiny:hud_super_icon";
    private static final int GOLD = 0xF4D36A;

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    private static ItemDisplayHud item(GameTestHelper h, ServerPlayer owner, String id) {
        DisplayHud hud = DisplayHud.getHud(owner, id);
        check(h, hud instanceof ItemDisplayHud, id + " must exist as an ItemDisplayHud");
        return (ItemDisplayHud) hud;
    }

    private static void noReady(GameTestHelper h, ServerPlayer owner) {
        check(h, DisplayHud.getHud(owner, CombatHud.READY_ID) == null, "Ready banner must be absent");
        check(h, DisplayHud.getHud(owner, CombatHud.READY_ECHO_ID) == null, "Ready echo must be absent");
    }

    private static void noTransient(GameTestHelper h, ServerPlayer owner) {
        noReady(h, owner);
        check(h, DisplayHud.getHud(owner, CombatHud.CAST_ID) == null, "Cast flash must be absent");
    }

    private static int color(GameTestHelper h, ItemDisplayHud hud) {
        var colors = hud.getItem().get(DataComponents.CUSTOM_MODEL_DATA);
        check(h, colors != null && colors.getColor(0) != null, "HUD must carry its actual item tint");
        return colors.getColor(0);
    }

    private static void readyAppearance(GameTestHelper h, ServerPlayer owner) {
        check(h, color(h, item(h, owner, DIAMOND)) == GOLD, "Full-charge diamond remains gold");
        int icon = color(h, item(h, owner, ICON));
        check(h, ((icon >> 16) & 255) <= 96 && ((icon >> 8) & 255) <= 96 && (icon & 255) <= 96,
                "Ready icon must be dark against the filled gold diamond");
        check(h, Guardians.data(owner).superEnergy() == 1f && !AbilityService.inSuper(owner),
                "Ready presentation must not consume energy or activate a super");
    }

    private static ItemDisplayHud chargeEdge(GameTestHelper h, ServerPlayer owner) {
        Guardians.data(owner).setSuperEnergy(0.75f);
        CombatHud.update(owner);
        noReady(h, owner);
        Guardians.data(owner).setSuperEnergy(1f);
        CombatHud.update(owner);
        ItemDisplayHud banner = item(h, owner, CombatHud.READY_ID);
        DisplayHud echo = DisplayHud.getHud(owner, CombatHud.READY_ECHO_ID);
        if (echo != null) check(h, echo instanceof ItemDisplayHud, "Ready echo uses an item HUD");
        return banner;
    }

    private static final class Owners implements AutoCloseable {
        private final GameTestHelper h;
        private final List<ServerPlayer> players = new ArrayList<>();
        private boolean closed;

        private Owners(GameTestHelper h) {
            this.h = h;
            h.runBeforeTestEnd(this::close);
        }

        private ServerPlayer create(Element element) {
            ServerPlayer player = TestPlayers.hunter(h, element, new Vec3(2.5, 1, 6.5), -90, 0);
            players.add(player);
            return player;
        }

        private void guarded(Runnable action) {
            try {
                action.run();
            } catch (RuntimeException | Error failure) {
                try { close(); }
                catch (RuntimeException | Error cleanup) { failure.addSuppressed(cleanup); }
                throw failure;
            }
        }

        private void after(int ticks, Runnable action) {
            h.runAfterDelay(ticks, () -> guarded(action));
        }

        private void done(Runnable assertions) {
            try { assertions.run(); }
            finally { close(); }
            h.succeed();
        }

        @Override
        public void close() {
            if (closed) return;
            closed = true;
            RuntimeException failure = null;
            for (ServerPlayer player : players) {
                try { TestPlayers.remove(player); }
                catch (RuntimeException cleanup) {
                    if (failure == null) failure = cleanup;
                    else failure.addSuppressed(cleanup);
                }
            }
            if (failure != null) throw failure;
        }
    }

    private static void scenario(GameTestHelper h, Consumer<Owners> assertions) {
        Owners owners = new Owners(h);
        owners.guarded(() -> assertions.accept(owners));
    }

    private static InputStream resource(GameTestHelper h, Identifier id, String directory, String extension) {
        String path = "/assets/" + id.getNamespace() + "/" + directory + "/" + id.getPath() + extension;
        InputStream stream = SuperReadyHudGameTests.class.getResourceAsStream(path);
        check(h, stream != null, "Bundled HUD resource must exist: " + path);
        return stream;
    }

    private static JsonObject json(GameTestHelper h, Identifier id, String directory) {
        try (var reader = new InputStreamReader(resource(h, id, directory, ".json"), StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        } catch (IOException failure) {
            throw new IllegalStateException("Cannot read HUD resource " + id, failure);
        }
    }

    /** Follow the actual selected sprite, avoiding an invented filename for the new filled asset. */
    private static void filledDiamond(GameTestHelper h, ServerPlayer owner) {
        Identifier itemModel = item(h, owner, DIAMOND).getItem().get(DataComponents.ITEM_MODEL);
        check(h, itemModel != null, "Diamond must select a pack-backed sprite");
        JsonObject selected = json(h, itemModel, "items").getAsJsonObject("model");
        check(h, selected != null && selected.has("model"), "Diamond uses the HUD's direct sprite model");
        JsonObject model = json(h, Identifier.parse(selected.get("model").getAsString()), "models");
        var textures = model.getAsJsonObject("textures");
        check(h, textures != null && textures.has("layer0"), "HUD quad must reference its sprite texture");
        Identifier texture = Identifier.parse(textures.get("layer0").getAsString());
        try (var stream = resource(h, texture, "textures", ".png")) {
            var image = ImageIO.read(stream);
            check(h, image != null, "Diamond texture must decode as PNG");
            for (double[] point : new double[][]{{0.5, 0.5}, {0.35, 0.5}, {0.65, 0.5}, {0.5, 0.35}, {0.5, 0.65}}) {
                int x = Math.min(image.getWidth() - 1, (int) (point[0] * image.getWidth()));
                int y = Math.min(image.getHeight() - 1, (int) (point[1] * image.getHeight()));
                check(h, (image.getRGB(x, y) >>> 24) >= 200,
                        "Ready diamond has an opaque interior, not only an outline");
            }
        } catch (IOException failure) {
            throw new IllegalStateException("Cannot decode ready diamond " + texture, failure);
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void baselineFullChargeHasNoBannerAndKeepsFilledGoldDiamondWithDarkIcon(GameTestHelper h) {
        scenario(h, owners -> {
            for (Element element : List.of(Element.ARC, Element.SOLAR, Element.VOID)) {
                ServerPlayer owner = owners.create(element);
                Guardians.data(owner).setSuperEnergy(1f);
                CombatHud.update(owner);
                noTransient(h, owner);
                readyAppearance(h, owner);
                filledDiamond(h, owner);
                for (int i = 0; i < 8; i++) CombatHud.update(owner);
                noTransient(h, owner);
            }
            owners.done(() -> { });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void chargeTransitionCreatesOneBannerAndSameTickUpdatesReuseItsEntity(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.ARC);
            ItemDisplayHud banner = chargeEdge(h, owner);
            int entity = banner.getEntityId();
            DisplayHud echo = DisplayHud.getHud(owner, CombatHud.READY_ECHO_ID);
            int tick = h.getLevel().getServer().getTickCount();
            for (int i = 0; i < 64; i++) {
                CombatHud.update(owner);
                check(h, item(h, owner, CombatHud.READY_ID).getEntityId() == entity,
                        "Repeated update must reuse the ready entity");
                if (echo != null) check(h, DisplayHud.getHud(owner, CombatHud.READY_ECHO_ID) == echo,
                        "Same-tick updates must not replace the echo entity");
            }
            owners.done(() -> {
                check(h, h.getLevel().getServer().getTickCount() == tick, "Exercise same-tick repeated updates");
                readyAppearance(h, owner);
                check(h, DisplayHud.getHud(owner, CombatHud.CAST_ID) == null, "Charging is not a cast");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90)
    public void bannerUsesServerTickDeadlineAndDoesNotReplayUntilAnotherChargeEdge(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.SOLAR);
            int entity = chargeEdge(h, owner).getEntityId();
            int startedAt = h.getLevel().getServer().getTickCount();
            owners.after(50, () -> {
                CombatHud.update(owner);
                check(h, item(h, owner, CombatHud.READY_ID).getEntityId() == entity,
                        "Updates over time reuse the same active banner");
            });
            owners.after(55, () -> {
                for (int i = 0; i < 32; i++) CombatHud.update(owner);
                check(h, item(h, owner, CombatHud.READY_ID).getEntityId() == entity,
                        "Banner remains alive just before its 56-tick deadline");
            });
            owners.after(58, () -> {
                check(h, h.getLevel().getServer().getTickCount() - startedAt == 58,
                        "Wait for normal server ticks, not simulated HUD update calls");
                CombatHud.update(owner);
                noTransient(h, owner);
                readyAppearance(h, owner);
            });
            owners.after(60, () -> owners.done(() -> {
                for (int i = 0; i < 16; i++) CombatHud.update(owner);
                noTransient(h, owner);
                chargeEdge(h, owner);
                readyAppearance(h, owner);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void removeResetsOnlyItsOwnerAndNextFullBaselineDoesNotReplay(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer a = owners.create(Element.ARC), b = owners.create(Element.VOID);
            int aId = chargeEdge(h, a).getEntityId(), bId = chargeEdge(h, b).getEntityId();
            check(h, aId != bId, "Owners must have distinct ready entities");
            CombatHud.remove(a);
            CombatHud.remove(a);
            noTransient(h, a);
            check(h, DisplayHud.getHuds(a).isEmpty(), "Lifecycle removal clears this owner's HUD");
            check(h, item(h, b, CombatHud.READY_ID).getEntityId() == bId, "Other owner's banner remains");
            CombatHud.update(a);
            noTransient(h, a);
            readyAppearance(h, a);
            owners.done(() -> {
                chargeEdge(h, a);
                check(h, item(h, b, CombatHud.READY_ID).getEntityId() == bId,
                        "Another owner's new charge cannot restart this banner");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void nonGuardianClearsTransientStateAndReturningFullIsBaseline(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.ARC);
            chargeEdge(h, owner);
            Guardians.data(owner).setGuardianClass(GuardianClass.NONE);
            CombatHud.update(owner);
            noTransient(h, owner);
            check(h, DisplayHud.getHud(owner, CombatHud.ABILITIES_ID) == null, "Non-guardian loses ability cluster");
            item(h, owner, CombatHud.HEALTH_ID);
            Guardians.data(owner).setGuardianClass(GuardianClass.HUNTER);
            CombatHud.update(owner);
            owners.done(() -> {
                noTransient(h, owner);
                readyAppearance(h, owner);
                chargeEdge(h, owner);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void spectatorAndDeathRemoveTransientStateWithoutReplayingOnReturn(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer spectator = owners.create(Element.SOLAR), dead = owners.create(Element.VOID);
            chargeEdge(h, spectator);
            chargeEdge(h, dead);
            spectator.setGameMode(GameType.SPECTATOR);
            dead.setHealth(0);
            for (ServerPlayer owner : List.of(spectator, dead)) {
                CombatHud.update(owner);
                noTransient(h, owner);
                check(h, DisplayHud.getHuds(owner).isEmpty(), "Invalid owner has no combat HUD");
            }
            spectator.setGameMode(GameType.SURVIVAL);
            dead.setHealth(dead.getMaxHealth());
            owners.done(() -> {
                for (ServerPlayer owner : List.of(spectator, dead)) {
                    CombatHud.update(owner);
                    noTransient(h, owner);
                    readyAppearance(h, owner);
                    chargeEdge(h, owner);
                }
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void realSuperActivationRemovesReadyAndHudCleanupPreservesPostEffects(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.ARC);
            chargeEdge(h, owner);
            Identifier unrelated = Identifier.parse("minecraft:creeper");
            owner.addPostEffect(unrelated);
            check(h, AbilityService.use(owner, AbilitySlot.SUPER) == AbilityService.Result.OK,
                    "Activate the real equipped Arc Staff through AbilityService");
            check(h, AbilityService.inSuper(owner) && Guardians.data(owner).superEnergy() == 0f,
                    "Real activation starts a session and consumes full charge");
            CombatHud.update(owner);
            noReady(h, owner);
            int castEntity = item(h, owner, CombatHud.CAST_ID).getEntityId();
            for (int i = 0; i < 16; i++) {
                CombatHud.update(owner);
                check(h, item(h, owner, CombatHud.CAST_ID).getEntityId() == castEntity,
                        "Same-tick active updates reuse the cast flash");
            }
            Guardians.data(owner).setSuperEnergy(1f);
            CombatHud.update(owner);
            noReady(h, owner);
            check(h, owner.getPostEffects().containsAll(List.of(unrelated, PostEffects.superEffect(Element.ARC))),
                    "HUD updates preserve unrelated and active-super post effects");
            CombatHud.remove(owner);
            noTransient(h, owner);
            check(h, owner.getPostEffects().containsAll(List.of(unrelated, PostEffects.superEffect(Element.ARC))),
                    "HUD lifecycle cleanup must not end post effects or the active session");
            CombatHud.update(owner);
            noReady(h, owner);
            Guardians.data(owner).setSuperEnergy(0f);
            AbilityService.endSuper(owner);
            owners.done(() -> {
                CombatHud.update(owner);
                noReady(h, owner);
                check(h, owner.getPostEffects().contains(unrelated), "Ending super preserves external post effect");
                check(h, !owner.getPostEffects().contains(PostEffects.superEffect(Element.ARC)),
                        "Real session end removes only its active-super grade");
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void classChangeDiscardsOldReadyBannerWithoutReplayingHunterBaseline(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.ARC);
            chargeEdge(h, owner);
            Guardians.data(owner).setGuardianClass(GuardianClass.TITAN);
            CombatHud.update(owner);
            noReady(h, owner);
            Guardians.data(owner).setGuardianClass(GuardianClass.HUNTER);
            CombatHud.update(owner);
            owners.done(() -> {
                noTransient(h, owner);
                readyAppearance(h, owner);
                chargeEdge(h, owner);
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 35)
    public void oneShotVoidReleaseSurvivesSessionEndThenExpires(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.VOID);
            chargeEdge(h, owner);
            check(h, AbilityService.use(owner, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real Void activation");
            int castEntity = item(h, owner, CombatHud.CAST_ID).getEntityId();
            AbilityService.perform(owner, kim.biryeong.destiny.input.GuardianAction.PRIMARY);
            for (int i = 0; i < kim.biryeong.destiny.fx.ShadowshotTiming.RELEASE_TICKS; i++)
                AbilityService.tickPlayer(owner);
            check(h, !AbilityService.inSuper(owner), "One-shot session ends at bow release, not on button press");
            check(h, item(h, owner, CombatHud.CAST_ID).getEntityId() == castEntity,
                    "Normal session end must not truncate short release");
            noReady(h, owner);
            owners.after(11, () -> {
                CombatHud.update(owner);
                check(h, item(h, owner, CombatHud.CAST_ID).getEntityId() == castEntity, "Release lasts eleven ticks");
            });
            owners.after(13, () -> owners.done(() -> {
                CombatHud.update(owner);
                noTransient(h, owner);
            }));
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void loadoutChangeDropsStaleBannerAndKeepsNewReadyIconWithoutReplay(GameTestHelper h) {
        scenario(h, owners -> {
            ServerPlayer owner = owners.create(Element.ARC);
            chargeEdge(h, owner);
            for (Element element : List.of(Element.SOLAR, Element.VOID)) {
                Guardians.data(owner).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(element));
                CombatHud.update(owner);
                noTransient(h, owner);
                readyAppearance(h, owner);
                Identifier iconModel = item(h, owner, ICON).getItem().get(DataComponents.ITEM_MODEL);
                check(h, iconModel != null && iconModel.getPath().endsWith(element == Element.SOLAR ? "/gun" : "/bow"),
                        "Full-charge icon follows the new equipped super");
                for (int i = 0; i < 8; i++) CombatHud.update(owner);
                noTransient(h, owner);
                chargeEdge(h, owner);
            }
            owners.done(() -> { });
        });
    }
}
