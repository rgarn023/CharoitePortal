package games.charoite.touhoupocket

import java.nio.file.Files
import org.junit.Assert.*
import org.junit.Test

class NotkeyLinkManagerTest {
    @Test fun makesRelativeIdempotentLink() {
        val drive = Files.createTempDirectory("wine-drive-c-")
        try {
            val focas = Files.createDirectories(drive.resolve("game/FocasLens"))
            val base = Files.createDirectories(focas.resolve("幻想人形演舞"))
            val expansion = Files.createDirectories(focas.resolve("幻想人形演舞-ユメノカケラ-"))
            assertEquals(NotkeyLinkManager.Status.CREATED, NotkeyLinkManager.ensure(drive, base, expansion))
            assertTrue(Files.isSameFile(expansion.resolve("notkey"), base))
            assertFalse(Files.readSymbolicLink(expansion.resolve("notkey")).isAbsolute)
            assertEquals(NotkeyLinkManager.Status.ALREADY_VALID, NotkeyLinkManager.ensure(drive, base, expansion))
        } finally { drive.toFile().deleteRecursively() }
    }

    @Test fun refusesToOverwriteExistingEntry() {
        val drive = Files.createTempDirectory("wine-drive-c-")
        try {
            val base = Files.createDirectory(drive.resolve("base"))
            val expansion = Files.createDirectory(drive.resolve("expansion"))
            Files.createFile(expansion.resolve("notkey"))
            assertThrows(IllegalArgumentException::class.java) {
                NotkeyLinkManager.ensure(drive, base, expansion)
            }
        } finally { drive.toFile().deleteRecursively() }
    }

    @Test fun refusesOutsideDrive() {
        val drive = Files.createTempDirectory("wine-drive-c-")
        val other = Files.createTempDirectory("outside-drive-")
        try {
            val expansion = Files.createDirectory(drive.resolve("expansion"))
            assertThrows(IllegalArgumentException::class.java) {
                NotkeyLinkManager.ensure(drive, other, expansion)
            }
        } finally {
            drive.toFile().deleteRecursively()
            other.toFile().deleteRecursively()
        }
    }
}
