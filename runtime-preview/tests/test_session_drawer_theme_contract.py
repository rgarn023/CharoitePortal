"""Contract tests for the streamlined realm-themed Charoite Core drawer.

The Wine runtime remains unchanged: only the renderer's navigation view is
restyled, and the existing session teardown is routed through confirmation.
"""
from pathlib import Path
import unittest

OVERLAY = (Path(__file__).resolve().parents[1] / "overlay.py").read_text()
SESSIONS = (Path(__file__).resolve().parents[1] /
            "charoite-core/CharoiteGameSessions.java").read_text()


class CharoiteSessionMenuContract(unittest.TestCase):
    def test_menu_keeps_only_exit_and_contextual_phone_keyboard(self):
        # Handheld games already have their own popup keyboard. Android phone
        # login/install windows retain keyboard entry; DeX has physical input.
        self.assertIn('boolean charoitePhoneKeyboard =', OVERLAY)
        self.assertIn('!getIntent().getBooleanExtra("charoite_handheld_game", false)', OVERLAY)
        self.assertIn('!getIntent().getBooleanExtra("touhou_desktop_window", false)', OVERLAY)
        self.assertIn('for (int i = 0; i < menu.size(); i++)', OVERLAY)
        self.assertIn('entry.setVisible(entry.getItemId() == R.id.menu_item_exit ||', OVERLAY)
        self.assertIn('entry.getItemId() == R.id.menu_item_keyboard)', OVERLAY)
        self.assertIn('menu.findItem(R.id.menu_item_exit).setTitle("Return to Charoite Portal")', OVERLAY)
        self.assertNotIn('menu.findItem(R.id.menu_item_input_controls).setVisible(false)', OVERLAY)

    def test_theme_is_supplied_by_selected_environment_not_another_registry(self):
        for field in ('charoite_environment_name', 'charoite_environment_theme'):
            self.assertIn('play.putExtra("' + field + '"', SESSIONS)
            self.assertIn('getIntent().getStringExtra("' + field + '")', OVERLAY)
        self.assertIn('CharoiteThemes.realmBanner(charoiteTheme)', OVERLAY)
        self.assertIn('charoiteHeader.findViewById(R.id.charoite_session_environment)', OVERLAY)
        self.assertIn('charoiteSakura ? 0xff251B2B : 0xff1D1730', OVERLAY)
        self.assertIn('navigationView.setItemTextColor(', OVERLAY)
        self.assertIn('navigationView.setItemIconTintList(', OVERLAY)
        self.assertIn('navigationView.setItemBackground(', OVERLAY)
        self.assertIn('android:id="@+id/charoite_session_environment"', OVERLAY)
        self.assertNotIn('CharoiteEnvironments.activeName(this)', OVERLAY)

    def test_return_confirms_closing_all_session_types(self):
        exit_start = OVERLAY.index('drawer_exit_anchor =')
        exit_end = OVERLAY.index('# Winlator\'s TouchpadView', exit_start)
        exit_code = OVERLAY[exit_start:exit_end]
        self.assertIn('confirmReturnToCharoitePortal();', exit_code)
        self.assertNotIn('else exit();', exit_code)
        self.assertIn('Save game progress or finish any installation first', OVERLAY)
        self.assertIn('CharoiteDiagnostics.requestPortalExit(this);', OVERLAY)
        self.assertIn('exit();', OVERLAY)

    def test_does_not_change_session_launch_storage_or_input_mapping(self):
        # Cosmetics only: this overlay must still use upstream UI and
        # the existing external keyboard and handheld injection bridges.
        self.assertIn('tpdp_touch_source =', OVERLAY)
        self.assertIn('rootView.addView(inputControlsView);', OVERLAY)
        self.assertIn('CharoiteLegacyKeyboard.sendScan(', OVERLAY)
        self.assertIn('drawerLayout.closeDrawers();', OVERLAY)
        self.assertNotIn('clearApplicationUserData(', OVERLAY)


if __name__ == "__main__":
    unittest.main()
