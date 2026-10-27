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
        self.assertIn('new Button[]{f11, screenshot, interior};', CONTROLS)
        self.assertIn('new Button[]{f11, screenshot, backend, diagnostics, interior}', CONTROLS)
        # A separate top-left Portal control never sends Esc to the game.
        self.assertIn('final Button portal = button(host, "PORTAL"', CONTROLS)
        self.assertIn('root.addView(portal);', CONTROLS)
        self.assertIn('position(portal, margin, margin, portalW, topButtonH)', CONTROLS)
        self.assertIn('portal.setOnClickListener(v -> {', CONTROLS)
        self.assertIn('returnToPortal.run();', CONTROLS)
        self.assertIn('Runnable returnToPortal, boolean tpdpMapping,', CONTROLS)
        self.assertIn('this::confirmReturnToCharoitePortal', OVERLAY)
        self.assertIn('private void confirmReturnToCharoitePortal()', OVERLAY)
        self.assertIn('.setNegativeButton("Stay Here", null)', OVERLAY)
        self.assertIn('.setPositiveButton("Return to Portal", (dialog, which) -> {', OVERLAY)
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
        self.assertIn('android:text="CHAROITE CORE"', OVERLAY)

    def test_landscape_panels_have_stable_minimum_width(self):
        # Previous source trusted projectedGameBounds for panel edges; on
        # Galaxy S26 landscape the projection was wrong and leftSideW=0,
        # producing 1px buttons and overlapping the game on the right.
        # Geometry now uses physical width and reserves center 51%.
        for clause in (
            'final int sidePanelExtent = Math.round(width * .245f);',
            'final int leftX = margin;',
            'final int leftSideW = Math.max(dp(host, 48),',
            'final int rightX = width - sidePanelExtent + margin;',
            'final int rightSideW = Math.max(dp(host, 48),',
            'final int leftPairW = (leftSideW - gap) / 2;',
            'final int rightPairW = (rightSideW - gap) / 2;',
            'position(esc, leftX, navY, leftPairW, landBarH)',
            'position(select, leftX + leftPairW + gap, navY,',
            'position(start, rightX, navY, rightPairW, landBarH)',
            'position(enter, rightX + rightPairW + gap, navY,',
            'position(leftShoulder, leftX + (leftSideW - shoulderW) / 2,',
            'position(rightShoulder, rightX +',
            'position(f11, leftX, menuY, leftPairW, landBarH)',
            'position(screenshot, leftX + leftPairW + gap, menuY,',
            'position(interior, rightX +',
            'final int keyboardY = height - margin - landBarH;',
            'position(keyboard, (width - keyboardW) / 2,',
            'if (portrait) {',
        ):
            self.assertIn(clause, CONTROLS)
        # The old zero-width fallback and wrong game-bottom anchor must
        # never reappear in the landscape placement branch.
        landscape = CONTROLS.split('final int sidePanelExtent =', 1)[1]
        self.assertNotIn('Math.max(1, leftSideW)', landscape)
        self.assertNotIn('rightX - gameLeft', landscape)
        self.assertNotIn('keyboardY = clamp(gameBottom', landscape)
        self.assertIn('root.post(relayout)', CONTROLS)

    def test_landscape_panel_geometry_in_landscape_and_dex(self):
        for width, height, density in ((1536, 709, 2.0),
                                       (1920, 1080, 1.5),
                                       (1000, 600, 1.6)):
            margin, gap = round(9 * density), round(5 * density)
            extent = round(width * .245)
            side_width = max(round(48*density), extent-2*margin)
            right_x = width - extent + margin
            left_edge_of_game = round(width * .27)
            right_edge_of_game = round(width * .73)
            left_end = margin + side_width
            assert left_end < left_edge_of_game, (width, left_end)
            assert right_x > right_edge_of_game, (width, right_x)
            pair = (side_width - gap) // 2
            assert pair >= round(40 * density), (width, pair)
            bar_height = max(round(28*density), min(round(33*density),
                                                   round(height*.087)))
            keyboard_y = height-margin-bar_height
            assert keyboard_y > height*.77, (width, keyboard_y)
            assert keyboard_y + bar_height <= height-margin

    def test_runtime_not_mutated_by_overlay(self):
        for token in ("container.saveData(","setKeysyms(","deleteRecursively",
                      "FileOutputStream"):
            self.assertNotIn(token,CONTROLS)
        self.assertIn('HIDE KEYS',CONTROLS)
        self.assertIn('SHOW KEYS',CONTROLS)

if __name__=="__main__":
    unittest.main()
