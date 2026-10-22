package games.charoite.touhoupocket

import org.junit.Assert.*
import org.junit.Test

class GameRecognizerTest {
    @Test fun identifiesBase() {
        assertEquals("tpdp-base", GameRecognizer.identify(listOf("gn_enbu.exe", "config.ini")).profile)
    }
    @Test fun identifiesShard() {
        assertEquals("tpdp-sod", GameRecognizer.identify(listOf("enbu_ap.exe", "save/enbu_ap.sav")).profile)
    }
    @Test fun identifiesExtended() {
        assertEquals("tpdp-sod-extended", GameRecognizer.identify(listOf("enbu_ap.exe", "dxgi.dll")).profile)
    }
    @Test fun identifiesTouhou() {
        assertEquals("touhou-th16", GameRecognizer.identify(listOf("th16.exe")).profile)
    }
    @Test fun unsafePathsAreRejected() {
        listOf("../bad", "a/../../bad", "C:/bad", "\\\\server/file", "/etc/passwd", "a/./b")
            .forEach { assertFalse(it, ArchiveInspector.safeRelativePath(it)) }
        assertTrue(ArchiveInspector.safeRelativePath("patch/data/english.dat"))
    }
}
