"""Regression: Hide Keys hides the soft-keyboard shortcut with handheld buttons.

The separate PORTAL and SHOW KEYS controls must stay reachable. This is a
source contract for the common Core overlay, not a physical-device UI test.
"""
from pathlib import Path
import unittest

CONTROLS = (
    Path(__file__).resolve().parents[1]
    / "charoite-core" / "CharoiteTpdpTouchControls.java"
).read_text(encoding="utf-8")


class HandheldKeyboardVisibilityContract(unittest.TestCase):
    def test_hide_keys_includes_keyboard_and_restore_shows_it(self):
        toggle = CONTROLS.split("toggle.setOnClickListener(v -> {", 1)[1].split(
            "\n        });", 1
        )[0]
        self.assertIn("boolean show = select.getVisibility() != View.VISIBLE;", toggle)
        self.assertIn("keyboard.setVisibility(show ? View.VISIBLE : View.GONE);", toggle)
        self.assertIn('toggle.setText(show ? "HIDE KEYS" : "SHOW KEYS");', toggle)
        self.assertIn("more.setVisibility(show ? View.VISIBLE : View.GONE);", toggle)
        self.assertIn("for (Button button : extras) button.setVisibility(View.GONE);", toggle)
        self.assertNotIn("portal.setVisibility(", toggle)
        self.assertNotIn("toggle.setVisibility(", toggle)

    def test_keyboard_remains_usable_when_buttons_are_shown(self):
        self.assertIn("root.addView(keyboard);", CONTROLS)
        self.assertIn("keyboard.setOnClickListener(v -> {", CONTROLS)
        self.assertIn("CharoiteSoftKeyboard.show(host);", CONTROLS)
        self.assertIn("portal.setOnClickListener(v -> {", CONTROLS)


if __name__ == "__main__":
    unittest.main()
