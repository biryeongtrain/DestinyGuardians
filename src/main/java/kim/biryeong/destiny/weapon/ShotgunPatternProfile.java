package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Closed exact-item roster, historical S19 patterns; no claim of unchanged 2026 engine rules. */
public final class ShotgunPatternProfile {
    private record Row(String id,long hash,String frame,long intrinsic,String pattern,ShotgunSpread.Shape shape) {}
    private static final List<Row> EXPECTED=List.of(
            new Row("mindbender_s_ambition_adept",912150785L,"aggressive",3983457027L,"fixed_evenly_distributed_cone",ShotgunSpread.Shape.CONE),
            new Row("dust_rock_blues",636912560L,"precision",1636108362L,"vertical_oval",ShotgunSpread.Shape.VERTICAL_OVAL),
            new Row("first_in_last_out",3616586446L,"pinpoint_slug",918679156L,"single_slug",ShotgunSpread.Shape.SLUG),
            new Row("parcel_of_stardust_fell_to_earth",2217366863L,"lightweight",1458010786L,"diamond",ShotgunSpread.Shape.DIAMOND),
            new Row("ikelos_sg_v1_0_1",1887808042L,"rapid_fire",996573084L,"square",ShotgunSpread.Shape.SQUARE));
    private static final Map<String,Row> ROWS=load();
    private ShotgunPatternProfile() {}
    private static Map<String,Row> load() {
        var input=ShotgunPatternProfile.class.getResourceAsStream("/destiny/weapons/w105-shotgun-patterns.json");
        if(input==null)throw new IllegalStateException("Missing W105 shotgun profile");
        try(var reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            var d=JsonParser.parseReader(reader).getAsJsonObject();
            if(!"W105".equals(d.get("stage").getAsString())||d.get("schemaVersion").getAsInt()!=1
                    ||!"historical_S19_2022_12_01_qualitative_only".equals(d.get("patternScope").getAsString()))
                throw new IllegalStateException("Invalid W105 source scope");
            var rows=d.getAsJsonArray("weapons");
            if(rows.size()!=EXPECTED.size())throw new IllegalStateException("Invalid shotgun roster");
            var result=new LinkedHashMap<String,Row>();
            for(int i=0;i<EXPECTED.size();i++) {
                var e=EXPECTED.get(i);var r=rows.get(i).getAsJsonObject();boolean slug=e.shape==ShotgunSpread.Shape.SLUG;
                if(!e.id.equals(r.get("id").getAsString())||e.hash!=r.get("hash").getAsLong()
                        ||!e.frame.equals(r.get("frame").getAsString())||e.intrinsic!=r.get("intrinsicHash").getAsLong()
                        ||r.get("socket").getAsInt()!=0||!e.pattern.equals(r.get("pattern").getAsString())
                        ||r.get("singleSlugRound").getAsBoolean()!=slug
                        ||(slug?(!r.get("pelletCount").isJsonNull()||r.get("slugProjectileCount").getAsInt()!=1)
                        :(r.get("pelletCount").getAsInt()!=12||!r.get("slugProjectileCount").isJsonNull())))
                    throw new IllegalStateException("Invalid exact shotgun identity/count: "+e.id);
                var entry=WeaponCatalog.find(e.id).orElseThrow();
                if(!entry.family().equals("shotgun")||!entry.frame().equals(e.frame)
                        ||WeaponCharacteristics.of(entry).bungieHash()!=e.hash)
                    throw new IllegalStateException("Shotgun catalog mismatch: "+e.id);
                result.put(e.id,e);
            }
            var rules=d.getAsJsonObject("sourceRules");
            var unknown=Set.of("currentPelletCount","currentPatternUnchangedSinceS19","genericAdsShrinksPelletSpread",
                    "genericAdsSpreadMultiplier","pelletCoordinates","baseSpreadAngleDegrees","patternAspectRatios",
                    "sourceDamagePerPellet","sourceDamageScalars");
            if(!rules.keySet().equals(unknown)||rules.entrySet().stream().anyMatch(e->!e.getValue().isJsonNull()))
                throw new IllegalStateException("Unproven shotgun rules must remain unknown");
            return Map.copyOf(result);
        } catch(java.io.IOException ex) {throw new IllegalStateException(ex);}
    }
    public static Optional<ShotgunSpread.Shape> shape(WeaponCatalog.Entry e) {
        if(e==null||!e.family().equals("shotgun"))return Optional.empty();
        var r=ROWS.get(e.id());
        return r!=null&&r.frame.equals(e.frame())&&r.hash==WeaponCharacteristics.of(e).bungieHash()
                ?Optional.of(r.shape):Optional.empty();
    }
    /** Zero means unsupported; slug is one ray, never twelve pellets. */
    public static int pellets(WeaponCatalog.Entry e) {return shape(e).map(s->s==ShotgunSpread.Shape.SLUG?1:12).orElse(0);}
    /** Retains the pre-W105 local ADS factor ONCE. Not a sourced original-game spread scalar. */
    public static double spread(double base,float ads) {
        if(!Double.isFinite(base)||base<=0)return 0;
        return base*(1-.35*(Float.isFinite(ads)?Math.clamp(ads,0,1):0));
    }
}
