"""Meteoric (Home) Realm is preinstalled and default only for FRESH Portal installs."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENV = (ROOT / "charoite-core/CharoiteEnvironments.java").read_text()
PORTAL = (ROOT / "TouhouEntryActivity.java").read_text()
CORE = (ROOT / "charoite-core/CharoiteCore.java").read_text()


class DefaultEnvironmentContract(unittest.TestCase):
    def test_built_in_realms_available_on_first_launch(self):
        self.assertIn('METEORIC = "meteoric-realm"', ENV)
        self.assertIn('entries.put(make(GENERAL, GENERAL_NAME, "general", 0));', ENV)
        self.assertIn('HOME_NAME = "Meteoric (Home) Realm"', ENV)
        self.assertIn('entries.put(make(METEORIC, HOME_NAME, "general", 0));', ENV)
        self.assertIn('entries.put(make(TOUHOU, "Touhou Realm", "touhou",', ENV)
        first_general = ENV.index('entries.put(make(METEORIC, HOME_NAME')
        later_touhou = ENV.index('entries.put(make(TOUHOU, "Touhou Realm"')
        self.assertLess(first_general, later_touhou)
        self.assertIn('entries.put(make(BATTLE_NET, "Battle.net Gaming", "battlenet", 0));', ENV)
        self.assertIn('String initial = legacy == null ? METEORIC : TOUHOU;', ENV)
        self.assertIn('.putString(ACTIVE, initial).commit()', ENV)
        self.assertIn('getString(ACTIVE, METEORIC)', ENV)
        self.assertIn('getString("charoite_active_environment_v1"', CORE)

    def test_preexisting_realm_switch_is_persisted(self):
        self.assertIn('prefs(host).edit().putString(ACTIVE, id).commit()', ENV)
        self.assertIn('CharoiteEnvironments.initialize(this);', PORTAL)
        self.assertIn('CharoiteEnvironments.switchTo(this, id)', PORTAL)
        self.assertIn('private static final String ACTIVE = "charoite_active_environment_v1"', ENV)

    def test_upgrade_adds_missing_presets_without_resetting_active_or_wine(self):
        branch = ENV.split('if (p.contains(KEY)) {', 1)[1].split('int legacyId', 1)[0]
        self.assertIn('existing.put(make(GENERAL, GENERAL_NAME, "general", 0))', branch)
        self.assertIn('existing.put(make(METEORIC, HOME_NAME, "general", 0))', branch)
        self.assertIn('existing.put(make(TOUHOU, "Touhou Realm", "touhou", 0))', branch)
        self.assertIn('if (hasGeneral && hasTouhou && hasBattleNet && hasMeteoric && !restoredGeneralName) return;', branch)
        self.assertIn('if (GENERAL.equals(entry.optString("id")))', branch)
        self.assertIn('if (HOME_NAME.equals(entry.optString("name")))', branch)
        self.assertIn('entry.put("name", GENERAL_NAME)', branch)
        self.assertIn('if (!hasBattleNet)', branch)
        self.assertIn('existing.put(make(BATTLE_NET, "Battle.net Gaming", "battlenet", 0))', branch)
        self.assertNotIn('.putString(ACTIVE,', branch)
        self.assertNotIn('delete(', branch)
        self.assertNotIn('createContainer', branch)
        self.assertIn('int legacyId = p.getInt("touhou_container", 0)', ENV)
        self.assertIn('legacy == null ? 0 : legacy.id', ENV)

    def test_per_realm_settings_and_library_isolation(self):
        self.assertIn('return TOUHOU.equals(id) ? "game_library" : "charoite_library_" + id;', ENV)
        self.assertIn('CharoiteEnvironments.activeId(host) + "_" + key', CORE)
        self.assertIn('return active(host).optInt("containerId", 0);', ENV)
        self.assertIn('return active(host).optString("template", "general");', ENV)

if __name__ == "__main__":
    unittest.main()
