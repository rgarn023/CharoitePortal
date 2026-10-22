package games.charoite.touhoupocket

import java.io.InputStream
import java.util.zip.ZipInputStream

/** Inspection only; no patch files are written to a game directory. */
object ArchiveInspector {
    data class Summary(val entries: Int, val sample: List<String>)

    /** Defensive against ZIP-slip, absolute paths, Windows drive prefixes and NUL. */
    fun safeRelativePath(name: String): Boolean {
        if (name.isBlank() || name.contains('\u0000') || name.startsWith('/') || name.startsWith('\\')) return false
        val segments = name.replace('\\', '/').split('/')
        if (segments.firstOrNull()?.contains(':') == true) return false
        return segments.none { it == ".." || it == "." }
    }

    fun inspect(stream: InputStream, maxEntries: Int = 10_000): Summary {
        val sample = mutableListOf<String>()
        var count = 0
        ZipInputStream(stream.buffered()).use { zip ->
            while (true) {
                val entry = zip.nextEntry ?: break
                if (!safeRelativePath(entry.name)) throw IllegalArgumentException("Unsafe path in archive: ${entry.name}")
                count++
                if (count > maxEntries) throw IllegalArgumentException("Archive contains too many entries")
                if (sample.size < 8) sample.add(entry.name)
                zip.closeEntry()
            }
        }
        if (count == 0) throw IllegalArgumentException("Empty or invalid ZIP")
        return Summary(count, sample)
    }
}
