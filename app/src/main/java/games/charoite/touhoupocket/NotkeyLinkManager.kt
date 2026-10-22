package games.charoite.touhoupocket

import java.nio.file.Files
import java.nio.file.Path

/**
 * Workaround for older Wine versions which look for the TPDP base files at
 * <Shard of Dreams install>/notkey. Not a Windows product key or DRM bypass.
 *
 * Only operate on app-controlled Wine drive_c content. Never overwrite a real
 * existing file or redirect paths outside the drive root.
 */
object NotkeyLinkManager {
    enum class Status { CREATED, ALREADY_VALID }

    fun ensure(driveC: Path, baseGame: Path, shardOfDreams: Path): Status {
        val root = driveC.toRealPath()
        val base = baseGame.toRealPath()
        val expansion = shardOfDreams.toRealPath()
        require(Files.isDirectory(root) && Files.isDirectory(base) && Files.isDirectory(expansion)) {
            "Wine C drive, base game, and Shard of Dreams must be installed first"
        }
        require(base.startsWith(root) && expansion.startsWith(root) && base != expansion) {
            "Both installations must be within the same managed Wine drive"
        }
        val link = expansion.resolve("notkey")
        if (Files.isSymbolicLink(link) || Files.exists(link)) {
            require(Files.isSymbolicLink(link) && Files.isSameFile(link, base)) {
                "An unrelated notkey entry already exists; refusing to replace it"
            }
            return Status.ALREADY_VALID
        }
        // Path relative to the directory containing the link.
        Files.createSymbolicLink(link, expansion.relativize(base))
        check(Files.isSameFile(link, base)) { "The newly created notkey link did not resolve" }
        return Status.CREATED
    }
}
