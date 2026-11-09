package kim.biryeong.destiny.world.template;

import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import xyz.nucleoid.map_templates.MapTemplate;

import java.util.List;
import java.util.Optional;

/** Immutable, map-owned death volumes. Region bounds use the template's world coordinates. */
public record TemplateHazards(List<DeathRegion> deaths) {
    public record DeathRegion(String id, AABB bounds) { }

    public TemplateHazards { deaths = List.copyOf(deaths); }

    public static TemplateHazards from(MapTemplate template) {
        return new TemplateHazards(template.getMetadata().getRegions("death")
                .map(r -> new DeathRegion(r.getData() == null ? "death" : r.getData().getStringOr("id", "death"),
                        r.getBounds().asBox())).toList());
    }

    /** Feet crossing a volume are lethal; jumps above the map have no ceiling boundary. */
    public Optional<DeathRegion> deathAt(Vec3 feet) {
        return deaths.stream().filter(r -> r.bounds().contains(feet)).findFirst();
    }
}
