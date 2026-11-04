package kim.biryeong.destiny.fx;

/** Screen-space animation of the same Golden Gun prop; never changes player aim/camera. */
public record GoldenGunHandPose(float x, float y, float size, float roll) {
    public static GoldenGunHandPose sample(int age, int sinceShot, int untilEnd, int sinceDissolve) {
        float summon = Math.clamp(age / (float) SuperAttackTiming.SOLAR_DEPLOY, 0, 1);
        float recoil = sinceShot < 0 ? 0 : sinceShot <= 1 ? 1 : Math.max(0, 1 - (sinceShot - 1) / 5f);
        float dissolve = sinceDissolve < 0 ? Math.clamp(untilEnd / 6f, 0, 1)
                : Math.clamp(1 - sinceDissolve / 6f, 0, 1);
        return new GoldenGunHandPose(1190 - 24 * recoil, 850 + (1 - summon) * 240 - 65 * recoil
                + (1 - dissolve) * 180, Math.max(1, 420 * summon * dissolve), -12 * recoil + (1 - summon) * 25);
    }
}
