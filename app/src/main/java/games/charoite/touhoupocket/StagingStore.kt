package games.charoite.touhoupocket

import android.content.Context
import android.net.Uri
import java.io.File
import java.security.MessageDigest

/** Copies user-selected installers/patches to private storage; never runs EXEs. */
object StagingStore {
    data class StagedFile(val name: String, val bytes: Long, val sha256: String)

    fun stage(context: Context, uri: Uri, displayName: String): StagedFile {
        val ext = displayName.substringAfterLast('.', "").lowercase()
        require(ext in setOf("exe", "zip")) { "Only EXE or ZIP inputs are supported in this milestone" }
        val destination = File(context.filesDir, "staged").apply { mkdirs() }
        val final = File(destination, "${System.currentTimeMillis()}-${(0..999999).random()}.$ext")
        val partial = File(destination, "${final.name}.partial")
        val sha = MessageDigest.getInstance("SHA-256")
        var bytes = 0L
        try {
            context.contentResolver.openInputStream(uri).use { input ->
                requireNotNull(input) { "Cannot open selected file" }
                partial.outputStream().use { output ->
                    val buf = ByteArray(64 * 1024)
                    while (true) {
                        val n = input.read(buf)
                        if (n < 0) break
                        bytes += n
                        require(bytes <= 2L * 1024 * 1024 * 1024) { "File exceeds 2 GB safety limit" }
                        sha.update(buf, 0, n)
                        output.write(buf, 0, n)
                    }
                }
            }
            require(partial.renameTo(final)) { "Unable to finalize staged file" }
            return StagedFile(displayName, bytes, sha.digest().joinToString("") { "%02x".format(it) })
        } finally {
            partial.delete()
        }
    }
}
