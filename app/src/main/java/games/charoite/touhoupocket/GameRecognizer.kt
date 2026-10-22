package games.charoite.touhoupocket

/** Conservative heuristics: files are not assumed to be genuine until launched/tested. */
object GameRecognizer {
    data class Identification(val title: String, val profile: String, val details: String)

    fun identify(names: Collection<String>): Identification {
        val files = names.map { it.substringAfterLast('/').lowercase() }.toSet()
        val extended = files.any { it.contains("sod-extended") } ||
            ("dxgi.dll" in files && files.any { it.startsWith("enbu_ap") })
        if (extended) return Identification(
            "Touhou Puppet Dance Performance — Shard of Dreams Extended",
            "tpdp-sod-extended", "Extended mod candidate; verify game files and DLL compatibility"
        )
        if (files.any { it.startsWith("enbu_ap") } || files.any { it.contains("yume") && it.endsWith(".exe") }) {
            return Identification("Touhou Puppet Dance Performance — Shard of Dreams",
                "tpdp-sod", "Expansion candidate; English patch and runtime not yet verified")
        }
        if (files.any { it.startsWith("gn_enbu") }) {
            return Identification("Touhou Puppet Dance Performance", "tpdp-base",
                "Base-game candidate; Windows runtime not yet integrated")
        }
        val th = files.firstOrNull { Regex("th(0[6-9]|1[0-9]|20)\\.exe").matches(it) }
        if (th != null) return Identification("Touhou ${th.removeSuffix(".exe")}",
            "touhou-${th.removeSuffix(".exe")}", "Executable detected; compatibility untested")
        return Identification("Unrecognized Windows game", "generic", "No supported game signature found")
    }
}
