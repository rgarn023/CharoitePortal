package games.charoite.touhoupocket

import android.content.Intent
import android.content.res.ColorStateList
import android.graphics.Color
import android.graphics.Typeface
import android.graphics.drawable.GradientDrawable
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.OpenableColumns
import android.view.View
import android.view.WindowInsets
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.documentfile.provider.DocumentFile

/** Alpha UI: imports, recognizes and stages files. No Windows runtime is bundled yet. */
class MainActivity : ComponentActivity() {
    private val background = Color.rgb(13, 17, 30)
    private val panel = Color.rgb(28, 36, 57)
    private val accent = Color.rgb(119, 85, 205)
    private lateinit var library: LocalLibrary
    private lateinit var results: LinearLayout
    private lateinit var status: TextView

    private val chooseFolder = registerForActivityResult(ActivityResultContracts.OpenDocumentTree()) { uri ->
        if (uri != null) importFolder(uri)
    }
    private val chooseInstaller = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) stage(uri, patch = false)
    }
    private val choosePatch = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri ->
        if (uri != null) stage(uri, patch = true)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        library = LocalLibrary(this)
        window.statusBarColor = background
        window.navigationBarColor = background
        val scroll = ScrollView(this).apply {
            setBackgroundColor(this@MainActivity.background)
            isFillViewport = true
        }
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(18), dp(26), dp(18), dp(26))
        }
        if (Build.VERSION.SDK_INT >= 30) {
            root.setOnApplyWindowInsetsListener { view, insets ->
                val sys = insets.getInsets(WindowInsets.Type.systemBars() or WindowInsets.Type.displayCutout())
                view.setPadding(dp(18) + sys.left, dp(26) + sys.top, dp(18) + sys.right, dp(26) + sys.bottom)
                insets
            }
        }
        scroll.addView(root)
        setContentView(scroll)

        root.addView(text("CHAROITE GAMES", 12f, Color.rgb(174, 149, 243), true))
        root.addView(text("Touhou Pocket Launcher", 26f, Color.WHITE, true))
        root.addView(text("Android · Early alpha", 14f, Color.rgb(178, 186, 206)))
        root.addView(space(18))

        val info = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            background = panelBg()
            setPadding(dp(16), dp(16), dp(16), dp(16))
        }
        info.addView(text("CURRENT BUILD: LIBRARY & FILE IMPORT", 14f, Color.WHITE, true))
        info.addView(text(
            "This first milestone can recognize selected game folders and inspect/stage EXE or ZIP files. " +
                "Windows execution, installation, and English patch application are NOT integrated yet.",
            13f, Color.rgb(200, 208, 225)
        ))
        root.addView(info)
        root.addView(space(18))

        root.addView(action("Import installed game folder") { chooseFolder.launch(null) })
        root.addView(action("Import Windows installer (.exe)") { chooseInstaller.launch(arrayOf("*/*")) })
        root.addView(action("Inspect / stage English patch (.zip)") { choosePatch.launch(arrayOf("*/*")) })
        root.addView(space(12))
        status = text("Ready. Select a folder or file to begin.", 13f, Color.rgb(179, 201, 255))
        root.addView(status)
        root.addView(space(18))
        root.addView(text("GAME LIBRARY", 17f, Color.WHITE, true))
        results = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(results)
        root.addView(space(18))
        root.addView(text("Next: Wine/Box64 runtime, actual game installation, game-specific English patches, then Extended DLL testing.",
            12f, Color.rgb(167, 175, 197)))
        redrawLibrary()
    }

    private fun importFolder(uri: Uri) {
        status.text = "Scanning selected folder…"
        Thread {
            runCatching {
                contentResolver.takePersistableUriPermission(uri, Intent.FLAG_GRANT_READ_URI_PERMISSION)
                val doc = requireNotNull(DocumentFile.fromTreeUri(this, uri)) { "Unable to open game folder" }
                val scan = GameScanner.scan(doc)
                LocalLibrary.Entry(uri.toString(), scan.identification.title, scan.identification.profile, scan.filesChecked)
            }.onSuccess { entry ->
                library.put(entry)
                runOnUiThread {
                    status.text = "Recognized: ${entry.title} (${entry.filesChecked} files checked)."
                    redrawLibrary()
                }
            }.onFailure { error -> runOnUiThread { status.text = "Import failed: ${error.message}" } }
        }.start()
    }

    private fun stage(uri: Uri, patch: Boolean) {
        status.text = if (patch) "Inspecting English patch archive…" else "Staging Windows installer…"
        Thread {
            runCatching {
                val name = nameFor(uri)
                if (patch) {
                    require(name.endsWith(".zip", ignoreCase = true)) { "Choose a ZIP patch. EXE patchers require Wine (next milestone)." }
                    val summary = contentResolver.openInputStream(uri).use { input ->
                        ArchiveInspector.inspect(requireNotNull(input) { "Unable to read ZIP file" })
                    }
                    val staged = StagingStore.stage(this, uri, name)
                    "Patch '${staged.name}' staged (${summary.entries} entries, SHA-256 ${staged.sha256.take(12)}…). Not applied."
                } else {
                    require(name.endsWith(".exe", ignoreCase = true)) { "Choose a Windows .exe installer" }
                    val staged = StagingStore.stage(this, uri, name)
                    "Installer '${staged.name}' staged (${staged.bytes / 1024} KB). Not executed; runtime pending."
                }
            }.onSuccess { value -> runOnUiThread { status.text = value } }
                .onFailure { error -> runOnUiThread { status.text = "Import failed: ${error.message}" } }
        }.start()
    }

    private fun nameFor(uri: Uri): String {
        contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
            if (cursor.moveToFirst()) return cursor.getString(0) ?: "unknown"
        }
        return uri.lastPathSegment ?: "unknown"
    }

    private fun redrawLibrary() {
        results.removeAllViews()
        val entries = library.all()
        if (entries.isEmpty()) {
            results.addView(text("No games imported yet.", 13f, Color.rgb(178, 186, 206)))
            return
        }
        for (entry in entries) {
            val card = LinearLayout(this).apply {
                orientation = LinearLayout.VERTICAL
                background = panelBg()
                setPadding(dp(14), dp(12), dp(14), dp(12))
                val params = LinearLayout.LayoutParams(-1, -2)
                params.topMargin = dp(10)
                layoutParams = params
            }
            card.addView(text(entry.title, 15f, Color.WHITE, true))
            card.addView(text("Profile: ${entry.profile} · Checked ${entry.filesChecked} files", 12f,
                Color.rgb(189, 197, 219)))
            card.addView(text("Play unavailable: runtime not yet integrated", 12f,
                Color.rgb(255, 199, 121)))
            results.addView(card)
        }
    }

    private fun text(value: String, fontSize: Float, color: Int, bold: Boolean = false): TextView =
        TextView(this).apply {
            text = value
            textSize = fontSize
            setTextColor(color)
            if (bold) typeface = Typeface.DEFAULT_BOLD
            setLineSpacing(dp(3).toFloat(), 1f)
        }

    private fun action(value: String, clicked: () -> Unit): Button = Button(this).apply {
        text = value
        isAllCaps = false
        setTextColor(Color.WHITE)
        backgroundTintList = ColorStateList.valueOf(accent)
        minHeight = dp(52)
        setOnClickListener { clicked() }
        val lp = LinearLayout.LayoutParams(-1, -2)
        lp.bottomMargin = dp(8)
        layoutParams = lp
    }

    private fun panelBg(): GradientDrawable = GradientDrawable().apply {
        setColor(panel)
        cornerRadius = dp(14).toFloat()
    }

    private fun space(height: Int): View = View(this).apply {
        layoutParams = LinearLayout.LayoutParams(1, dp(height))
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density + 0.5f).toInt()
}
