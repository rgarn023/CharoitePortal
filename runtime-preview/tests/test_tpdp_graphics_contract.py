"""Verify TPDP black-screen backend selection never modifies existing Wine prefixes."""
import pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
CORE=(ROOT/"charoite-core/CharoiteCore.java").read_text()
SESSION=(ROOT/"charoite-core/CharoiteGameSessions.java").read_text()
PORTAL=(ROOT/"TouhouEntryActivity.java").read_text()
OVERLAY=(ROOT/"overlay.py").read_text()
DIAGNOSTICS=(ROOT/"charoite-core/CharoiteDiagnostics.java").read_text()

class TpdpDirectx9GraphicsContract(unittest.TestCase):
    def test_opt_in_and_reversible_graphics_modes(self):
        for token in (
            'TPDP_GRAPHICS_SAVED = 0','TPDP_GRAPHICS_DXVK_TURNIP = 1',
            'TPDP_GRAPHICS_WINED3D_VIRGL = 2',
            '"tpdp_graphics_mode"',
            'scopedKey(host, TPDP_GRAPHICS_KEY)',
            'setTpdpGraphicsMode(AppCompatActivity host, int mode)',
            'tpdpGraphicsModeForLaunch(AppCompatActivity host',
            'isTpdpGameExecutable(executable)',
            'filename',):
            if token == "filename": continue
            self.assertIn(token,CORE)
        self.assertIn('file.equals("gn_enbu.exe")',CORE)
        self.assertIn('file.equals("enbu_ap.exe")',CORE)
        self.assertIn('TPDP_GRAPHICS_WINED3D_VIRGL : TPDP_GRAPHICS_SAVED',CORE)
        self.assertIn('TPDP GRAPHICS: ',PORTAL)
        self.assertIn('cycleTpdpGraphics()',PORTAL) if False else None
        self.assertIn('this::cycleTpdpGraphics',PORTAL)

    def test_session_scopes_only_known_exes(self):
        self.assertIn('play.putExtra("charoite_tpdp_graphics_mode"',SESSION)
        self.assertIn('CharoiteCore.tpdpGraphicsModeForLaunch(host, executable)',SESSION)
        self.assertIn('if (getIntent().hasExtra("exec_path")',OVERLAY)
        self.assertIn('isTpdpGameExecutable(',OVERLAY)
        self.assertIn('getIntExtra("charoite_tpdp_graphics_mode", 0)',OVERLAY)
        for token in (
            'GraphicsDrivers.TURNIP',
            'DXWrappers.DXVK',
            'GraphicsDrivers.VIRGL',
            'DXWrappers.WINED3D',
            'dxwrapperConfig = "";',
            'graphicsDriverConfig = "";',
        ):
            self.assertIn(token,OVERLAY)
        self.assertIn('assert code.count(tpdp_backend_anchor) == 1',OVERLAY)
        self.assertIn('this.graphicsDriver = GraphicsDrivers.parseIdentifiers(graphicsDriver);',OVERLAY)
        self.assertNotIn('container.setDXWrapper(',SESSION)
        self.assertNotIn('container.saveData(',SESSION)
        self.assertNotIn('container.setGraphicsDriver(',SESSION)

    def test_graphics_diagnostics_available_after_success(self):
        self.assertIn('recordGraphicsBackend(Context context, String wrapper',DIAGNOSTICS)
        self.assertIn('GRAPHICS BACKEND:',DIAGNOSTICS)
        self.assertIn('p.getString("charoite_last_graphics_backend"',DIAGNOSTICS)
        self.assertIn('CharoiteDiagnostics.recordGraphicsBackend(',OVERLAY)
        self.assertIn('this.dxwrapper, this.graphicsDriver[0]',OVERLAY)


    def test_tpdp_touch_keyboard_uses_real_key_hold_and_release(self):
        # UI comes from Charoite Core and injects Android key events into
        # upstream XServer keyboard, not a second XInput controller.
        keys=(ROOT/"charoite-core/CharoiteTpdpTouchControls.java").read_text()
        for marker in (
            "KeyEvent.KEYCODE_DPAD_UP", "KeyEvent.KEYCODE_DPAD_DOWN",
            "KeyEvent.KEYCODE_DPAD_LEFT", "KeyEvent.KEYCODE_DPAD_RIGHT",
            "KeyEvent.KEYCODE_Z", "KeyEvent.KEYCODE_X",
            "KeyEvent.KEYCODE_S", "KeyEvent.KEYCODE_C",
            "KeyEvent.KEYCODE_A", "KeyEvent.KEYCODE_D",
            "KeyEvent.KEYCODE_SPACE", "KeyEvent.KEYCODE_SHIFT_LEFT",
            "KeyEvent.KEYCODE_ENTER", "KeyEvent.KEYCODE_ESCAPE",
            "MotionEvent.ACTION_DOWN", "MotionEvent.ACTION_UP",
            "MotionEvent.ACTION_CANCEL", "releaseAll.run()",
            "HIDE KEYS", "SHOW KEYS", "sink.send(code,pressed)",
        ):
            self.assertIn(marker,keys)
        self.assertIn("com.charoitegames.core.CharoiteTpdpTouchControls.attach(",OVERLAY)
        self.assertIn("xServer.keyboard.onKeyEvent(",OVERLAY)
        self.assertIn("tpdp_touch_target.write_bytes(tpdp_touch_source.read_bytes())",OVERLAY)
        self.assertIn("isTpdpGameExecutable(",OVERLAY)
        self.assertIn('!getIntent().getBooleanExtra("touhou_desktop_window", false)',OVERLAY)
        self.assertNotIn("setKeysyms(",keys)
        self.assertNotIn("container.saveData(",keys)

if __name__=="__main__": unittest.main()
