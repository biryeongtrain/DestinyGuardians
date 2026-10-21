package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/**
 * 26.3 포스트 이펙트 켜기·끄기 (docs/design/07). 효과 정의는 리소스팩 assets/destiny/post_effect 에 있다.
 * 서버는 실제 적용 여부를 알 수 없다.
 */
public final class PostEffects {
    private PostEffects() {
    }

    public static Identifier superEffect(Element element) {
        return DestinyGuardians.id("super/" + element.getSerializedName() + "_active");
    }

    public static void enter(ServerPlayer player, Element element) {
        player.addPostEffect(superEffect(element));
    }

    public static void exit(ServerPlayer player, Element element) {
        player.removePostEffect(superEffect(element));
    }
}
