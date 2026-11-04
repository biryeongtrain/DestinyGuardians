package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.autohost.impl.AutoHost;
import kim.biryeong.destiny.DestinyGuardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.BetterModelPlatform;
import net.fabricmc.fabric.api.event.Event;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;

/** BetterModel 3.5.1 / Polymer 0.18.4+26.3 startup-order compatibility.
 * Only AutoHost.init's existing generation requests are intercepted. No config
 * changes, sleeps, retries, main-thread waits or generated-pack substitutions.
 */
public final class StartupPackCoordinator {
    private static final Identifier AFTER_MODELS = DestinyGuardians.id("pack_after_models_w121");
    private static volatile Session current;
    private static boolean listenerInstalled;

    private record Session(MinecraftServer server, StartupPackOrder order) {}

    private StartupPackCoordinator() {}

    public static void init() {
        // Entry-point order does not matter: all mod initializers have completed
        // before SERVER_STARTING. The handler captures no particular server.
        ServerLifecycleEvents.SERVER_STARTING.register(server -> {
            session(server);
            if (!listenerInstalled) {
                BetterModel.platform().addReloadEndHandler(result -> {
                    Session active = current;
                    if (active != null) active.order().observeReload(
                            result instanceof BetterModelPlatform.ReloadResult.Success);
                });
                listenerInstalled = true;
            }
        });
        // BetterModel's pinned synchronous SERVER_STARTED listener is DEFAULT.
        // Its reload resets isLoadingProvider before returning / end handlers.
        ServerLifecycleEvents.SERVER_STARTED.addPhaseOrdering(Event.DEFAULT_PHASE, AFTER_MODELS);
        ServerLifecycleEvents.SERVER_STARTED.register(AFTER_MODELS, server -> {
            Session active = session(server);
            apply(active, active.order().finishStartup(), "startup completion");
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            Session active = current;
            if (active != null && active.server() == server) active.order().stop();
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> {
            synchronized (StartupPackCoordinator.class) {
                if (current != null && current.server() == server) current = null;
            }
        });
    }

    /** Called only by the exact two AutoHost.init invocation sites. */
    public static void request(MinecraftServer server) {
        Session active = session(server);
        StartupPackOrder.Action action = active.order().request();
        if (action == StartupPackOrder.Action.NONE) {
            DestinyGuardians.LOGGER.info("W121 autohost startup generation deferred until BetterModel startup completes");
        }
        apply(active, action, "autohost request");
    }

    private static synchronized Session session(MinecraftServer server) {
        if (current == null) current = new Session(server, new StartupPackOrder());
        if (current.server() != server) {
            throw new IllegalStateException("W121 concurrent Minecraft server lifecycles are unsupported");
        }
        return current;
    }

    private static void apply(Session active, StartupPackOrder.Action action, String reason) {
        switch (action) {
            case START -> {
                DestinyGuardians.LOGGER.info("W121 autohost generation released after successful BetterModel startup ({})", reason);
                AutoHost.startResourcePackGeneration(active.server());
            }
            case BLOCK -> DestinyGuardians.LOGGER.error(
                    "W121 autohost generation blocked: BetterModel startup failed, was unobserved, or server stopped ({}). No automatic retry; inspect the preceding BetterModel error before operator regeneration.", reason);
            case NONE -> { }
        }
    }
}
