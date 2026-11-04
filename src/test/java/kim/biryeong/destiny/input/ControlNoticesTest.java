package kim.biryeong.destiny.input;

import net.minecraft.network.chat.Component;
import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class ControlNoticesTest {
    @Test void cinematicRecipientWaitsWithoutDelayingAnotherRecipient() {
        var busy = new ControlNotices(); var free = new ControlNotices();
        var id = UUID.randomUUID(); var message = Component.literal("installed");
        busy.announce(id, message); free.announce(id, message);
        for (int tick = 0; tick < 1200; tick++) assertTrue(busy.drain(true).isEmpty());
        assertEquals(java.util.List.of(message), free.drain(false));
        assertEquals(java.util.List.of(message), busy.drain(false));
        assertTrue(busy.drain(false).isEmpty());
    }

    @Test void lateHandshakeReplacesRecommendationAndDeduplicatesSubject() {
        var notices = new ControlNotices(); var id = UUID.randomUUID();
        notices.recommend(Component.literal("install GCB"));
        assertTrue(notices.drain(true).isEmpty());
        notices.installed();
        notices.announce(id, Component.literal("old"));
        notices.announce(id, Component.literal("new"));
        assertEquals(java.util.List.of("new"), notices.drain(false).stream().map(Component::getString).toList());
    }

    @Test void boundedAnnouncementsCannotEvictPersonalRecommendation() {
        var notices = new ControlNotices();
        notices.recommend(Component.literal("personal"));
        for (int i = 0; i < 1000; i++) notices.announce(new UUID(0, i), Component.literal("notice " + i));
        var result = notices.drain(false);
        assertEquals(ControlNotices.MAX_ANNOUNCEMENTS + 1, result.size());
        assertEquals("personal", result.getFirst().getString());
        assertEquals("notice 968", result.get(1).getString());
        assertEquals("notice 999", result.getLast().getString());
        assertTrue(notices.drain(false).isEmpty());
    }
}
