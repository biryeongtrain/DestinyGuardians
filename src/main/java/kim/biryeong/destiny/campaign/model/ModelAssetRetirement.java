package kim.biryeong.destiny.campaign.model;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;

/** Ownership-preserving migration for retired entries in any model catalog. */
final class ModelAssetRetirement {
    private ModelAssetRetirement() { }
    /** Retire only an unchanged managed file, preserving it outside the renderer's scan directory. */
    static boolean retireOwned(Path modelsDir, Path markerDir, String name) throws IOException {
        if (!name.matches("[a-z][a-z0-9_]*")) throw new IllegalArgumentException("Invalid model name");
        Path target = modelsDir.resolve(name + ".bbmodel"), marker = markerDir.resolve(name + ".sha256");
        if (!Files.isRegularFile(target, LinkOption.NOFOLLOW_LINKS)
                || !Files.isRegularFile(marker, LinkOption.NOFOLLOW_LINKS)) return false;
        String have = RisingModelAssets.sha256(Files.readAllBytes(target));
        if (!have.equals(Files.readString(marker, StandardCharsets.UTF_8).trim())) return false;
        Path archive = markerDir.resolve(name + "." + have + ".retired.bbmodel");
        if (Files.exists(archive, LinkOption.NOFOLLOW_LINKS)) {
            if (!Files.isRegularFile(archive, LinkOption.NOFOLLOW_LINKS)
                    || !have.equals(RisingModelAssets.sha256(Files.readAllBytes(archive)))) return false;
            Files.delete(target);
        } else Files.move(target, archive);
        return true;
    }

}
