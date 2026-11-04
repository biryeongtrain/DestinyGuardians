package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;
import net.minecraft.world.item.ItemStack;

/** Official exact identities; quantitative rules below are authored Minecraft tuning, NOT D2 measurements. */
public final class TrackingProfile {
    public static final String ID="tracking_module";
    public static final long HASH=3977735242L, INTRINSIC_HASH=3419274965L;
    public static final int ACQUIRE_TICKS=20;
    public static final double RANGE=64, CONE_DEGREES=8, TURN_RADIANS=Math.toRadians(3);
    public static final float MIN_ADS=.95f;
    private static final List<WeaponPerks.Roll> EXPECTED=List.of(
            new WeaponPerks.Roll("bad_omens",991314988L,3,HASH,457210958L),
            new WeaponPerks.Roll("bellowing_giant",2186258845L,3,HASH,2605036073L));
    private static final List<WeaponPerks.Roll> ROLLS=load();
    private TrackingProfile() {}
    private static List<WeaponPerks.Roll> load() {
        var input=TrackingProfile.class.getResourceAsStream("/destiny/weapons/w104-tracking.json");
        if(input==null)throw new IllegalStateException("Missing W104 tracking profile");
        try(var reader=new InputStreamReader(input,StandardCharsets.UTF_8)) {
            var d=JsonParser.parseReader(reader).getAsJsonObject();
            var intrinsic=d.getAsJsonObject("intrinsic");var perk=d.getAsJsonObject("perk");
            if(!"W104".equals(d.get("stage").getAsString())||intrinsic.get("hash").getAsLong()!=INTRINSIC_HASH
                    ||!"Intrinsic".equals(intrinsic.get("type").getAsString())||!intrinsic.get("requiresAim").getAsBoolean()
                    ||!ID.equals(perk.get("id").getAsString())||perk.get("hash").getAsLong()!=HASH
                    ||perk.get("enhancedHash").getAsLong()!=406461158L||perk.get("enhancedImplemented").getAsBoolean()
                    ||!perk.get("requiresAim").getAsBoolean())throw new IllegalStateException("Invalid W104 identity");
            var rows=d.getAsJsonArray("intrinsicWeapons");
            if(rows.size()!=1)throw new IllegalStateException("Invalid intrinsic roster");
            var row=rows.get(0).getAsJsonObject();
            if(!"pyroclastic_flow".equals(row.get("id").getAsString())||row.get("hash").getAsLong()!=1289324202L
                    ||row.get("socket").getAsInt()!=0||row.get("intrinsicHash").getAsLong()!=INTRINSIC_HASH
                    ||!"initialIntrinsic".equals(row.get("proofMode").getAsString()))throw new IllegalStateException("Invalid precision source");
            var actual=new ArrayList<WeaponPerks.Roll>();
            for(var value:d.getAsJsonArray("weapons")) {
                var r=value.getAsJsonObject();
                if(!"randomized".equals(r.get("proofMode").getAsString()))throw new IllegalStateException("Invalid tracking pool proof");
                actual.add(new WeaponPerks.Roll(r.get("id").getAsString(),r.get("hash").getAsLong(),r.get("socket").getAsInt(),
                        r.get("perkHash").getAsLong(),r.get("plugSetHash").getAsLong()));
            }
            if(!actual.equals(EXPECTED))throw new IllegalStateException("Invalid tracking socket roster");
            for(var r:actual) {
                var e=WeaponCatalog.find(r.id()).orElseThrow();
                if(!e.family().equals("rocket_launcher")||WeaponCharacteristics.of(e).bungieHash()!=r.hash())
                    throw new IllegalStateException("Tracking catalog mismatch");
            }
            var rules=d.getAsJsonObject("sourceRules");
            if(!rules.get("requiresAim").getAsBoolean()||!rules.get("continuousAimAfterLaunchRequired").isJsonNull()
                    ||rules.getAsJsonObject("unknownSourceRules").size()!=17
                    ||rules.getAsJsonObject("unknownSourceRules").entrySet().stream().anyMatch(e->!e.getValue().isJsonNull()))
                throw new IllegalStateException("Unverified W104 numeric rule must remain unknown");
            return List.copyOf(actual);
        } catch(java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static List<WeaponPerks.Roll> rolls() {return ROLLS;}
    public static boolean supportsIntrinsic(WeaponCatalog.Entry e) {
        return e!=null&&e.id().equals("pyroclastic_flow")&&e.family().equals("rocket_launcher")
                &&WeaponCharacteristics.of(e).bungieHash()==1289324202L;
    }
    public static boolean supports(ItemStack stack) {
        return WeaponItems.entry(stack).filter(e->supportsIntrinsic(e)||WeaponPerks.selected(stack,ID).isPresent()).isPresent();
    }
}
