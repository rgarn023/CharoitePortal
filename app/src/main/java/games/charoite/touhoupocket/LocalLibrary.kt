package games.charoite.touhoupocket

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Keeps SAF URIs, not bundled game data. Users retain ownership of their game files. */
class LocalLibrary(context: Context) {
    private val prefs = context.getSharedPreferences("library-v1", Context.MODE_PRIVATE)

    data class Entry(val uri: String, val title: String, val profile: String, val filesChecked: Int)

    fun all(): List<Entry> {
        val json = JSONArray(prefs.getString("entries", "[]"))
        return (0 until json.length()).map { n ->
            val obj = json.getJSONObject(n)
            Entry(obj.getString("uri"), obj.getString("title"), obj.getString("profile"), obj.getInt("filesChecked"))
        }
    }

    fun put(entry: Entry) {
        val entries = all().filter { it.uri != entry.uri } + entry
        val json = JSONArray()
        for (item in entries) json.put(JSONObject().apply {
            put("uri", item.uri)
            put("title", item.title)
            put("profile", item.profile)
            put("filesChecked", item.filesChecked)
        })
        prefs.edit().putString("entries", json.toString()).apply()
    }
}
