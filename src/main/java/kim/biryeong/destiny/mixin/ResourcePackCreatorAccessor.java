package kim.biryeong.destiny.mixin;

import eu.pb4.polymer.resourcepack.api.ResourcePackCreator;
import org.spongepowered.asm.mixin.Mixin;
import org.spongepowered.asm.mixin.gen.Accessor;
import java.nio.file.Path;
import java.util.Set;

@Mixin(value = ResourcePackCreator.class, remap = false)
public interface ResourcePackCreatorAccessor {
    @Accessor("sourcePaths") Set<Path> destiny$sourcePaths();
}
