package kim.biryeong.destiny.compat.pack;

import org.junit.jupiter.api.Test;
import java.util.UUID;
import static org.junit.jupiter.api.Assertions.*;

class ActivityPackLoadTest {
    @Test void downloadAndAcceptanceNeverApproveTeleport() {
        var id = UUID.randomUUID(); var load = new ActivityPackLoad(id);
        load.response(id, "ACCEPTED"); assertFalse(load.ready());
        load.response(id, "DOWNLOADED"); assertFalse(load.ready());
        load.response(id, "SUCCESSFULLY_LOADED"); assertTrue(load.ready());
        load.response(id, "ACCEPTED"); load.response(id, "DOWNLOADED"); assertTrue(load.ready());
    }
    @Test void anOldRequestCannotApproveOrFailItsReplacement() {
        var id = UUID.randomUUID(); var old = UUID.randomUUID(); var load = new ActivityPackLoad(id);
        load.response(old, "SUCCESSFULLY_LOADED"); assertFalse(load.ready());
        load.response(old, "FAILED_DOWNLOAD"); assertNull(load.failure());
        load.response(id, "SUCCESSFULLY_LOADED"); assertTrue(load.ready());
    }
    @Test void failureIsTerminalAndDiscardingALoadedPackClosesTheGate() {
        for (String response : new String[]{"DECLINED", "FAILED_DOWNLOAD", "INVALID_URL", "FAILED_RELOAD", "DISCARDED"}) {
            var id = UUID.randomUUID(); var load = new ActivityPackLoad(id);
            load.response(id, "SUCCESSFULLY_LOADED"); load.response(id, response);
            assertFalse(load.ready()); assertEquals(response, load.failure());
            load.response(id, "SUCCESSFULLY_LOADED"); assertFalse(load.ready());
        }
    }
    @Test void oneMemberCannotReleaseAnotherMembersGate() {
        var first = new ActivityPackLoad(UUID.randomUUID()); var second = new ActivityPackLoad(UUID.randomUUID());
        first.response(first.request(), "SUCCESSFULLY_LOADED");
        second.response(first.request(), "SUCCESSFULLY_LOADED");
        assertTrue(first.ready()); assertFalse(second.ready());
        first.fail("cancelled"); assertFalse(first.ready()); assertNull(second.failure());
    }
}
