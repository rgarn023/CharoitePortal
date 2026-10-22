package games.charoite.touhoupocket

import androidx.documentfile.provider.DocumentFile

object GameScanner {
    data class Scan(val identification: GameRecognizer.Identification, val filesChecked: Int)

    fun scan(folder: DocumentFile): Scan {
        val found = mutableListOf<String>()
        fun walk(parent: DocumentFile, depth: Int) {
            if (depth > 5 || found.size >= 4000) return
            for (child in parent.listFiles()) {
                if (found.size >= 4000) break
                val name = child.name ?: continue
                if (child.isFile) found.add(name)
                else if (child.isDirectory) walk(child, depth + 1)
            }
        }
        walk(folder, 0)
        return Scan(GameRecognizer.identify(found), found.size)
    }
}
