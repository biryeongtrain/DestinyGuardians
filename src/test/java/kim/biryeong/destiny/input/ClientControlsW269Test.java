package kim.biryeong.destiny.input;

import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class ClientControlsW269Test {
    @Test void clientVersionCannotInjectFormattingAndHasBoundedLength() {
        assertEquals("4.0.0+26.3-beta.1", ClientControls.versionLabel("4.0.0+26.3-beta.1"));
        assertEquals("", ClientControls.versionLabel(null));
        assertEquals("", ClientControls.versionLabel("unknown"));
        assertEquals(64, ClientControls.versionLabel("a".repeat(500)).length());
        assertFalse(ClientControls.versionLabel("<red>4.0.0</red>\n").contains("<"));
    }

    @Test void versionIsBlueAndPlayerNameIsPreservedAsPlainComponent() {
        var message = ClientControls.installedMessage(Component.literal("andlist"), "4.0.0");
        assertEquals("andlist 유저가 GCB 모드 4.0.0 를 설치했습니다.", message.getString());
        var version = message.getSiblings().stream().filter(c -> c.getString().equals("4.0.0")).findFirst().orElseThrow();
        assertEquals(0x5555FF, version.getStyle().getColor().getValue());
        assertNull(version.getStyle().getClickEvent());
    }

    @Test void recommendationLinksOnlyToRequestedReleasePage() {
        var message = ClientControls.recommendation();
        var download = message.getSiblings().stream().filter(c -> c.getStyle().getClickEvent() != null).findFirst().orElseThrow();
        var event = assertInstanceOf(ClickEvent.OpenUrl.class, download.getStyle().getClickEvent());
        assertEquals(ClientControls.DOWNLOAD_URL, event.uri().toString());
        assertTrue(message.getString().contains("기본 키로 플레이할 수 있습니다"));
    }
}
