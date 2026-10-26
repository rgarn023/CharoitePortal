"""TPDP's native touch controls send held X11 keys through Winlator XServer."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
CONTROLS=(ROOT/"charoite-core/CharoiteTpdpTouchControls.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
PROFILES=(ROOT/"charoite-core/CharoiteGameControlProfiles.java").read_text()

class TpdpTouchContract(unittest.TestCase):
    def test_real_native_keyboard_keys(self):
        keys=(
            "KEYCODE_DPAD_UP","KEYCODE_DPAD_DOWN",
            "KEYCODE_DPAD_LEFT","KEYCODE_DPAD_RIGHT","KEYCODE_Z",
            "KEYCODE_X","KEYCODE_C","KEYCODE_S","KEYCODE_A",
            "KEYCODE_D","KEYCODE_SPACE","KEYCODE_SHIFT_LEFT",
            "KEYCODE_ENTER","KEYCODE_ESCAPE",
        )
        for key in keys:
            self.assertIn("KeyEvent."+key,PROFILES)
        for event in ("MotionEvent.ACTION_DOWN","MotionEvent.ACTION_UP",
                      "MotionEvent.ACTION_CANCEL","releaseAll.run()",
                      "sink.send(code, true)", "sink.send(code, false)"):
            self.assertIn(event,CONTROLS)
        self.assertNotIn("setKeysyms(",CONTROLS)
        self.assertNotIn("boolean down = false;",CONTROLS)
        self.assertIn("sink.send(keyCode, pressed);",CONTROLS)
        self.assertIn("sink.send(code, true)",CONTROLS)
        self.assertIn("sink.send(code, false)",CONTROLS)
        self.assertIn('KeyEvent.KEYCODE_F11',CONTROLS)
        self.assertIn('"F11 Full"',CONTROLS)
        self.assertIn('button.setVisibility(View.GONE)',CONTROLS)
        self.assertIn('releaseAll.run()',CONTROLS)

    def test_handheld_sketch_abxy_and_ergonomics(self):
        # Button geometry stays fixed; executable-scoped mappings come from
        # Core instead of hard-coded literals in the UI.
        for code in ("KEYCODE_SHIFT_LEFT", "KEYCODE_Z", "KEYCODE_X",
                     "KEYCODE_C", "KEYCODE_S", "KEYCODE_A",
                     "KEYCODE_D", "KEYCODE_SPACE", "KEYCODE_CTRL_LEFT"):
            self.assertIn("KeyEvent."+code,PROFILES)
        for label in ("Esc", "Select", "Start", "Enter", "L", "R",
                      "↑", "←", "→", "↓", "Y", "X", "A", "B"):
            self.assertIn('button(host, "'+label+'", binding.apply(',CONTROLS)
        self.assertIn('CharoiteGameControlProfiles.keyFor(host, executable, index)',CONTROLS)
        self.assertIn('final Map<Integer, Integer> held = new HashMap<>();', CONTROLS)
        self.assertIn('GradientDrawable.OVAL',CONTROLS)
        self.assertIn('position(up, dpadCenterX, dpadCenterY - size - gap, size, size)',CONTROLS)
        self.assertIn('position(yButton, diamondX + size + gap, clusterY, size, size)',CONTROLS)
        self.assertIn('position(aButton, diamondX + (size + gap) * 2',CONTROLS)
        self.assertIn('position(bButton, diamondX + size + gap',CONTROLS)
        self.assertIn('root.addOnLayoutChangeListener(',CONTROLS)
        self.assertIn('root.post(relayout)',CONTROLS)
        self.assertIn('topControls',CONTROLS)
        self.assertIn('shoulderY',CONTROLS)
        self.assertIn('root.addView(more)',CONTROLS)
        # Esc / Select / Start / Enter are always visible in one centered row.
        self.assertIn('esc, select, start, enter, leftShoulder', CONTROLS)
        self.assertIn('position(esc, centerX, topControls', CONTROLS)
        self.assertIn('position(select, centerX + centerWidth + centerGap', CONTROLS)
        self.assertIn('position(start, centerX + 2 * (centerWidth + centerGap)', CONTROLS)
        self.assertIn('position(enter, centerX + 3 * (centerWidth + centerGap)', CONTROLS)
        self.assertIn('new Button[]{f11, screenshot};', CONTROLS)
        self.assertIn('new Button[]{f11, screenshot, backend, diagnostics}', CONTROLS)
        # A separate top-left Portal control never sends Esc to the game.
        self.assertIn('final Button portal = button(host, "PORTAL"', CONTROLS)
        self.assertIn('root.addView(portal);', CONTROLS)
        self.assertIn('position(portal, margin, margin, portalW, topButtonH)', CONTROLS)
        self.assertIn('portal.setOnClickListener(v -> {', CONTROLS)
        self.assertIn('returnToPortal.run();', CONTROLS)
        self.assertIn('Runnable returnToPortal, boolean tpdpMapping,', CONTROLS)
        self.assertIn('this::confirmReturnToCharoitePortal', OVERLAY)
        self.assertIn('private void confirmReturnToCharoitePortal()', OVERLAY)
        self.assertIn('.setNegativeButton("Keep Playing", null)', OVERLAY)
        self.assertIn('.setPositiveButton("Exit Game", (dialog, which) -> {', OVERLAY)
        self.assertIn('CharoiteDiagnostics.requestPortalExit(this);', OVERLAY)
        self.assertIn('exit();', OVERLAY)
        self.assertIn('ProcessHelper.removeDebugCallback(', OVERLAY)
        self.assertIn('startActivity(home);', OVERLAY)
        self.assertIn('finish();', OVERLAY)
        self.assertIn('root.addView(toggle)',CONTROLS)
        self.assertIn('more.setOnClickListener(',CONTROLS)
        self.assertIn('toggle.setOnClickListener(',CONTROLS)
        self.assertIn('if (!show) releaseAll.run()',CONTROLS)
        self.assertNotIn('"X Run"',CONTROLS)
        self.assertNotIn('"Z OK"',CONTROLS)

    def test_scope_handheld_to_games_and_preserve_tpdp_mapping(self):
        for token in ('com.charoitegames.core.CharoiteTpdpTouchControls.attach(',
                      'tpdp_touch_target.write_bytes(tpdp_touch_source.read_bytes())',
                      'getIntent().hasExtra("exec_path")',
                      'isTpdpGameExecutable(',
                      'getBooleanExtra("touhou_desktop_window", false)'):
            self.assertIn(token,OVERLAY)
        self.assertIn('file.equals("gn_enbu.exe")',CORE)
        self.assertIn('file.equals("enbu_ap.exe")',CORE)
        self.assertIn("TPDP_GRAPHICS_WINED3D_VIRGL",CORE)
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"',SESSION)
        self.assertIn('play.putExtra("charoite_handheld_game", !installer &&', SESSION)
        self.assertIn('getBooleanExtra("charoite_handheld_game", false)', OVERLAY)
        self.assertIn('xServer.injectKeyPress(key);', OVERLAY)
        self.assertIn('xServer.injectKeyRelease(key);', OVERLAY)
        self.assertNotIn('xServer.keyboard.onKeyEvent(new android.view.KeyEvent(', OVERLAY)
        self.assertIn('CharoiteWindowPolicy.configureSession(', OVERLAY)
        self.assertIn('main_menu_header.xml', OVERLAY)
        self.assertIn('android:text="Charoite Core"', OVERLAY)

    def test_runtime_not_mutated_by_overlay(self):
        for token in ("container.saveData(","setKeysyms(","deleteRecursively",
                      "FileOutputStream"):
            self.assertNotIn(token,CONTROLS)
        self.assertIn('HIDE KEYS',CONTROLS)
        self.assertIn('SHOW KEYS',CONTROLS)

if __name__=="__main__":
    unittest.main()
