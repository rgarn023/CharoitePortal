"""Regressions: Windows game and installer screens must show their own realm.

The Portal uses Activity.getPreferences() historically, which is keyed to the
activity's local class name. The Windows renderer is a DIFFERENT activity.
Never create a second registry from XServerDisplayActivity preferences.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ENV = (ROOT/"charoite-core/CharoiteEnvironments.java").read_text()
SESSIONS = (ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
PRELOADER = (ROOT/"CharoiteStartupScreen.java").read_text()
OVERLAY = (ROOT/"overlay.py").read_text()
PORTAL = (ROOT/"TouhouEntryActivity.java").read_text()
CORE = (ROOT/"charoite-core/CharoiteCore.java").read_text()


class ActiveRealmSessionContract(unittest.TestCase):
    def test_portal_and_renderer_share_original_preferences_file(self):
        self.assertIn('private static final String PORTAL_PREFS = "TouhouEntryActivity";', ENV)
        self.assertIn('host.getSharedPreferences(PORTAL_PREFS, AppCompatActivity.MODE_PRIVATE)', ENV)
        self.assertNotIn('return host.getPreferences(AppCompatActivity.MODE_PRIVATE);', ENV)
        self.assertIn('CharoiteEnvironments.initialize(this);', PORTAL)
        self.assertIn('CharoiteEnvironments.switchTo(this, id)', PORTAL)
        self.assertIn('getSharedPreferences("TouhouEntryActivity", Context.MODE_PRIVATE)', CORE)

    def test_each_session_gets_selected_realm_identity_not_hardcoded_touhou(self):
        for prop, expr in (
            ('charoite_environment_id', 'CharoiteEnvironments.activeId(host)'),
            ('charoite_environment_name', 'CharoiteEnvironments.activeName(host)'),
            ('charoite_environment_theme', 'CharoiteEnvironments.activeTheme(host)'),
        ):
            self.assertIn('play.putExtra("'+prop+'", '+expr+');', SESSIONS)
        self.assertIn('play.putExtra("container_id", containerId);', SESSIONS)
        self.assertIn('play.putExtra("exec_path", executable);', SESSIONS)
        self.assertIn('launch(host, target, containerId, executable, installer, true);', SESSIONS)
        self.assertNotIn('play.putExtra("charoite_environment_name", "Touhou Realm")', SESSIONS)

    def test_preloader_shows_session_name_then_shared_registry_fallback(self):
        self.assertIn('activity.getIntent().getStringExtra("charoite_environment_name")', PRELOADER)
        self.assertIn('activity.getIntent().getStringExtra("charoite_environment_theme")', PRELOADER)
        self.assertIn('CharoiteEnvironments.activeName(portalHost)', PRELOADER)
        self.assertIn('CharoiteEnvironments.activeTheme(portalHost)', PRELOADER)
        self.assertNotIn('text(activity, "Touhou Realm"', PRELOADER)
        self.assertIn('CharoiteStartupScreen.create(activity)', OVERLAY)

    def test_no_game_container_or_save_changes(self):
        self.assertNotIn('deleteRecursively(', ENV)
        self.assertNotIn('setContainerId(', SESSIONS)
        self.assertNotIn('container.saveData(', SESSIONS)
        self.assertNotIn('setDXWrapper(', PRELOADER)
        self.assertNotIn('getSharedPreferences("XServerDisplayActivity"', PRELOADER)


if __name__ == "__main__":
    unittest.main()
