package kim.biryeong.destiny.weapon;

import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;

/** Exercise the installed BetterModel skin-data implementation, not a mocked layout. */
public final class SkinArmsW204GameTests {
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100)
    public void installedBetterModelForearmsMatchSharedSkinPixelContract(GameTestHelper h) {
        var skin=kr.toxicity.model.api.BetterModel.platform().skinManager().fallback();
        int n=skin.profile().skin().slim()?96:112;
        for(var arm:java.util.List.of(skin.rightForeArm(),skin.leftForeArm())) {
            var item=((kr.toxicity.model.api.mod.platform.ModItemStack)arm.itemStack()).source();
            var data=item.get(DataComponents.CUSTOM_MODEL_DATA);
            var colors=WeaponSkinArms.flatten(data,n,true);
            h.assertTrue(colors.size()==n, Component.literal("Installed BetterModel RGB/alpha contract"));
            var bare=WeaponSkinArms.flatten(data,n,false);
            h.assertTrue(bare.equals(data.colors().subList(0,n)),Component.literal("Hidden sleeve preserves original skin pixels"));
        }
        h.succeed();
    }
}
