package kim.biryeong.destiny.fx;

/** W260 source final root heading inverse, applied only to the staged intro rig.
 * Derived from rotateZYX(finalRoot) * (0,0,-1), not an Euler-Y addition.
 * Raw source keys, timing and root translation are retained.
 */
final class IntroFacing {
    private IntroFacing() { }

    static float correctionRadians(String clip) {
        double degrees = switch (clip) {
            case "h15_intro_80b7bbc8" -> 28.154;
            case "h15_intro_80b7bbca" -> 50.605;
            case "h15_intro_80b7bbcc", "h15_intro_80b7bbd0" -> 60.190;
            case "h15_intro_80b7bbd4" -> 50.603;
            case "h15_intro_80b7bbdb" -> 28.152;
            // Briefing clips (h15_intro_brief_*) bake their camera-facing correction into the root; none here.
            default -> 0;
        };
        return (float) Math.toRadians(degrees);
    }
}
