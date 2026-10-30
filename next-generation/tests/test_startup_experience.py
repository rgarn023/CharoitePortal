"""Next boot: exact approved launcher icon, full-bleed splash, no warm replay."""
from pathlib import Path
import hashlib
import importlib.util
import tempfile
import unittest
import wave

ROOT = Path(__file__).resolve().parents[1]
BOOT = (ROOT / "CharoiteNextBootActivity.java").read_text(encoding="utf-8")
PREP = (ROOT / "prepare_next.py").read_text(encoding="utf-8")
ART = ROOT / "assets/charoite_next_boot_reference.jpg"
ART_SHA = "2f368b7731f8ff96db03842e0f36b62bc9d22c48fcdb77ed864846d6be44b748"
spec = importlib.util.spec_from_file_location("startup_audio", ROOT / "generate_crystal_startup.py")
audio = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audio)
art_spec = importlib.util.spec_from_file_location("boot_art", ROOT / "make_fullbleed_boot.py")
art = importlib.util.module_from_spec(art_spec)
art_spec.loader.exec_module(art)
portrait_spec = importlib.util.spec_from_file_location("portrait_art", ROOT / "make_portrait_boot.py")
portrait_art = importlib.util.module_from_spec(portrait_spec)
portrait_spec.loader.exec_module(portrait_art)


class StartupExperienceTest(unittest.TestCase):
    def test_original_launcher_artwork_preserved_exactly(self):
        from PIL import Image
        with Image.open(ART) as picture:
            picture.load()
            self.assertEqual(picture.size, (1536,1536))
            self.assertEqual(picture.format, "JPEG")
        self.assertEqual(hashlib.sha256(ART.read_bytes()).hexdigest(), ART_SHA)
        self.assertIn("boot_art.write_bytes(image_bytes)", PREP)
        self.assertIn("next_launcher_icon.write_bytes(image_bytes)", PREP)
        self.assertIn("generate_fullbleed_boot(approved_art", PREP)
        self.assertIn("charoite_next_boot_unframed.png", PREP)
        self.assertIn("charoite_next_boot_backdrop.jpg", PREP)
        self.assertIn("versionCode 67", PREP)
        self.assertIn("11.2-next.0.36", PREP)

    def test_boot_foreground_has_no_black_outside_and_backdrop_fills_screen(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            front = Path(td) / "unframed.png"
            back = Path(td) / "backdrop.jpg"
            art.generate(ART, front, back)
            with Image.open(front) as image:
                self.assertEqual(image.size, (1536,1536))
                self.assertEqual(image.mode, "RGBA")
                for xy in ((0,0),(0,1535),(1535,0),(1535,1535)):
                    self.assertLess(image.getpixel(xy)[3], 8)
                self.assertGreater(image.getpixel((768,768))[3], 250)
            with Image.open(back) as image:
                self.assertEqual(image.size, (900,1600))
                for xy in ((0,0),(899,0),(0,1599),(899,1599)):
                    self.assertGreater(max(image.getpixel(xy)), 12)
        self.assertIn("R.drawable.charoite_next_boot_unframed", BOOT)
        self.assertNotIn("R.drawable.charoite_next_boot_backdrop", BOOT)
        self.assertIn("ImageView.ScaleType.CENTER_CROP", BOOT)
        self.assertIn("PORTRAIT_ART_WIDTH = 960f", BOOT)
        self.assertIn("charoite_next_boot_portrait", BOOT)
        self.assertIn("ViewGroup.LayoutParams.MATCH_PARENT", BOOT)

    def test_true_portrait_asset_eliminates_visible_icon_frame(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "portrait.jpg"
            portrait_art.generate(ART, target)
            with Image.open(target) as image:
                image.load()
                self.assertEqual(image.size, (960,1840))
                self.assertEqual(image.mode, "RGB")
                # The four corners no longer use the old black rounded
                # square of the launcher icon; the extension fills them.
                for xy in ((0,0),(959,0),(0,1839),(959,1839)):
                    self.assertGreater(max(image.getpixel(xy)), 20)
                # The approved art stays in the central source region.
                self.assertGreater(max(image.getpixel((480,930))), 40)
                # The upper and lower extensions are content-rich source
                # textures, not large featureless painted bands.
                from PIL import ImageStat
                for box in ((80, 30, 880, 350), (80, 1390, 880, 1800)):
                    stats = ImageStat.Stat(image.crop(box))
                    self.assertGreater(max(stats.stddev), 13)

        self.assertIn("generate_portrait_boot(approved_art, boot_portrait)", PREP)
        self.assertIn("make_portrait_boot", PREP)
        # Prevent recreating the visibly rectangular inset: a single,
        # uninterrupted source image must fill the portrait canvas.
        generator_source = (ROOT / "make_portrait_boot.py").read_text(encoding="utf-8")
        self.assertIn("SOURCE_X = (114, 1422)", generator_source)
        self.assertIn("SOURCE_Y = (113, 1434)", generator_source)
        self.assertIn("TOP_EXTENSION = 410", generator_source)
        self.assertIn("uniform_scale=width/src_width", generator_source)
        self.assertIn("core_height=round(src_height*uniform_scale)", generator_source)
        self.assertIn("_sky_extension(core,TOP_EXTENSION)", generator_source)
        self.assertIn("_glass_extension(core,bottom_height)", generator_source)
        self.assertNotIn("DEST_Y", generator_source)
        self.assertNotIn("for band in range(len(SOURCE_Y)-1)", generator_source)
        self.assertNotIn("core_top = ", generator_source)


    def test_gateway_keeps_original_aspect_ratio_without_pixel_stretch(self):
        from PIL import Image, ImageStat, ImageChops
        x0,x1 = portrait_art.SOURCE_X
        y0,y1 = portrait_art.SOURCE_Y
        scale = portrait_art.PORTRAIT_SIZE[0] / (x1-x0)
        natural_height = round((y1-y0)*scale)
        self.assertEqual(portrait_art.TOP_EXTENSION, 410)
        self.assertGreater(natural_height, 900)
        self.assertLess(natural_height, 1020)
        self.assertLess(abs(natural_height/(y1-y0)-scale), 0.001)
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/"portrait.jpg"
            portrait_art.generate(ART,out)
            with Image.open(ART) as master:
                expected=master.convert("RGB").crop((x0,y0,x1,y1))
                expected=expected.resize((960,natural_height),Image.Resampling.LANCZOS)
            with Image.open(out) as picture:
                core=picture.crop((0,410,960,410+natural_height))
                # JPEG encoding is allowed to vary a few levels. Compare
                # untouched, centered interior; no stretch or aspect warp.
                area=(180,140,780,natural_height-140)
                error=ImageChops.difference(expected.crop(area), core.crop(area))
                self.assertLess(max(ImageStat.Stat(error).mean), 5.0)

    def test_crystal_title_has_contrasting_dark_faceted_plaque(self):
        view = BOOT.split("private static final class CrystalWordmark extends View {",1)[1].split("private static final class CrystalShimmer",1)[0]
        self.assertIn('WORDMARK = "CHAROITE PORTAL"', view)
        self.assertIn("panel.setShader(new LinearGradient(", view)
        self.assertIn("canvas.drawRoundRect(plateLeft, plateTop", view)
        self.assertIn("Color.argb(247, 12, 6, 42)", view)
        self.assertIn("canvas.drawText(WORDMARK, x, y, lettering)", view)
        self.assertIn("diamond(canvas,", view)
        self.assertIn("setContentDescription(\"Charoite Portal\")", BOOT)
        self.assertNotIn("ProgressBar", view)

    def test_seven_second_boot_once_per_real_session(self):
        self.assertIn("BOOT_DURATION_MS = 7000L", BOOT)
        self.assertIn("handler.postDelayed(openMain, BOOT_DURATION_MS)", BOOT)
        self.assertIn("CrystalShimmer extends View", BOOT)
        self.assertNotIn("slowReveal.setDuration(", BOOT)
        self.assertIn("hasLivePortalInSameTask(this)", BOOT)
        self.assertIn("portal.getTaskId() == launcher.getTaskId()", BOOT)
        self.assertIn("onPortalCreated(Activity portal, Bundle state)", BOOT)
        self.assertIn("pendingColdFallbackOwner = portal", BOOT)
        self.assertIn("onPortalPostCreated(Activity portal)", BOOT)
        self.assertIn(".onPortalPostCreated(this)", PREP)
        self.assertIn("onPostCreate(android.os.Bundle savedInstanceState)", PREP)
        self.assertIn("super.onPostCreate(savedInstanceState)", PREP)
        self.assertIn("markBootShown(this)", BOOT)
        self.assertIn("LAST_BOOT_VERSION", BOOT)
        self.assertIn("installedVersion(portal)", BOOT)
        self.assertIn("if (state != null && seen == version) return;", BOOT)
        self.assertIn("portal.isTaskRoot()", BOOT)
        self.assertIn("activeColdFallback", BOOT)
        self.assertIn("Portal exited; launcher task root closed", BOOT)
        self.assertIn("if (completed)", BOOT)
        self.assertIn("super.onResume()", BOOT)
        # The root boot Activity must not finish immediately after opening
        # Portal; otherwise Samsung can resume Portal forever without boot.
        launch = BOOT.split("startActivity(main);",1)[1].split("};\n        handler.postDelayed(openMain",1)[0]
        self.assertNotIn("finish();", launch)
        fallback = BOOT.split("public static void onPortalCreated(Activity portal, Bundle state) {",1)[1].split("public static void onPortalPostCreated",1)[0]
        self.assertIn("pendingColdFallbackOwner = portal", fallback)
        self.assertIn("portal.isChangingConfigurations()", fallback)
        self.assertIn('Already running in same task; boot skipped', BOOT)
        self.assertIn("currentPortal.get()", BOOT)
        self.assertIn("portal.isDestroyed()", BOOT)
        self.assertIn("notePortalDestroyed(this)", PREP)
        self.assertIn(".onPortalResumed(this)", PREP)
        self.assertIn(".onPortalCreated(this, savedInstanceState)", PREP)
        self.assertNotIn("showOnBackgroundReentryIfNeeded", BOOT)
        self.assertNotIn("activeReentryOverlay", BOOT)
        self.assertNotIn("REENTRY_NEEDED", BOOT)
        self.assertNotIn(".notePortalPaused(this)", PREP)
        self.assertNotIn(".onPortalRestart(this)", PREP)
        self.assertNotIn(".noteUserLeaving(this)", PREP)
        self.assertNotIn(".noteLauncherIntent(intent)", PREP)
        resume = BOOT.split("public static void onPortalResumed(Activity portal) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("createBootView(",resume)
        self.assertIn("playArrivalChimeIfRequested(portal)",resume)

    def test_reference_portal_only_is_packaged_and_original_title_is_preserved(self):
        import hashlib
        renderer = (ROOT.parent / "docs/previews/render_crystal_awakening.py").read_text(encoding="utf-8")
        self.assertIn("WIDTH, HEIGHT, FPS, SECONDS = 480, 920, 30, 7", renderer)
        self.assertIn("Charoite_C_Energy_Reference_Portal_7s.mp4", renderer)
        self.assertIn("charoite_user_edited_portal_v33.webp", renderer)
        self.assertNotIn("draw_plaque(", renderer, "Do not replace native title with video plaque")
        self.assertIn("def crystal_phase(t):", renderer)
        self.assertIn("def crystal_glow_layers():", renderer)
        self.assertIn("OUTER_C_RIM", renderer)
        self.assertIn("def advect_energy(source, age, seed=0.):", renderer)
        self.assertIn("INNER_C_RIM", renderer)
        self.assertIn("def rim_source(i):", renderer)
        self.assertIn("def make_energy_streams(t):", renderer)
        self.assertNotIn("def make_clouds(", renderer)
        self.assertNotIn("cv2.circle(black", renderer)
        self.assertIn("cv2.polylines(filaments", renderer)
        self.assertIn("mask = opening_mask()", renderer)
        self.assertIn("4.85", renderer)
        self.assertIn("def render_overlay(t, base, portal_source):", renderer)
        self.assertIn("cv2.remap(portal_source,", renderer)
        self.assertIn("return scene", renderer)
        self.assertIn('movie_raw = app / "res/raw/charoite_c_energy_reference_portal_7s.mp4"', PREP)
        self.assertIn("CHAROITE_NEXT_C_ENERGY_REFERENCE_PORTAL_7_SECONDS=PASS", PREP)
        self.assertIn("new CrystalPortalMovie(activity)", BOOT)
        self.assertIn("com.winlator.R.raw.charoite_c_energy_reference_portal_7s", BOOT)
        self.assertIn("MediaPlayer.MEDIA_INFO_VIDEO_RENDERING_START", BOOT)
        self.assertIn("player.setVolume(0f, 0f)", BOOT)
        self.assertIn("player.setLooping(false)", BOOT)
        self.assertIn("getWidth() <= getHeight()", BOOT)
        self.assertIn("fadingForBootEnd", BOOT)
        self.assertIn("BOOT_DURATION_MS = 7000L", BOOT)
        self.assertIn("portalMovie.postDelayed(portalMovie::fadeForBootEnd, BOOT_DURATION_MS - 950L)", BOOT)
        # The Java title must render ABOVE the video: exactly one native title.
        boot = BOOT.split("private static FrameLayout createBootView(Activity activity) {",1)[1].split("private static final class CrystalArtwork",1)[0]
        self.assertEqual(boot.count("new CrystalWordmark(activity)"), 1)
        self.assertLess(boot.index("boot.addView(portalMovie"), boot.index("boot.addView(title"))
        self.assertNotIn("new CrystalCloudMovie", BOOT)

    def test_portal_pastes_only_user_reference_into_c_without_touching_title(self):
        import importlib.util
        import numpy as np
        source = ROOT.parent / "docs/previews/render_crystal_awakening.py"
        spec = importlib.util.spec_from_file_location("reference_portal_only", source)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.portal_phase(0), 0)
        self.assertGreater(mod.portal_phase(3.5), .99)
        self.assertEqual(mod.portal_phase(6.35), 0)
        image = mod.make_portal_source()
        self.assertEqual(image.shape, (160, 160, 3))
        # Base pixels change only at C crystal glow and enlarged portal feeder zone.
        base = np.full((mod.HEIGHT, mod.WIDTH, 3), 110., dtype=np.float32)
        rendered = mod.render_overlay(3.5, base, image)
        x0, x1 = 50, 455
        y0, y1 = 196, 639
        changes = np.any(rendered != base, axis=2)
        self.assertTrue(changes[mod.FEED_Y0:mod.FEED_Y1,mod.FEED_X0:mod.FEED_X1].any(),
                        "Expanded reference vortex and feeding clouds must be visible")
        self.assertGreater(mod.PORTAL_RX, 95)
        self.assertGreater(mod.PORTAL_RY, 108)
        self.assertGreater(mod.crystal_phase(3.5), .95)
        material,aura,highlight=mod.crystal_glow_layers()
        self.assertGreater(float(material.max()),.95)
        self.assertGreater(float(highlight.max()),.05)
        # The new stronger bloom must visibly brighten the same C mask.
        a = mod.render_overlay(3.5,base,image)
        glow_zone = (mod.crystal_glow_layers()[2]>.30)
        self.assertGreater(float((a[glow_zone]-base[glow_zone]).mean()),20.)
        changes[y0:y1,x0:x1] = False
        self.assertFalse(changes.any(), "Title, sky and unrelated scenery must remain unchanged")
        self.assertTrue(np.array_equal(mod.render_overlay(0, base, image), base))
        self.assertTrue(np.array_equal(mod.render_overlay(6.35, base, image), base))
        self.assertGreater(float(np.abs(mod.render_overlay(2.5,base,image) -
                                        mod.render_overlay(3.5,base,image)).sum()), 1000.)

    def test_energy_ribbons_feed_c_center_ccw_and_fade_with_audio(self):
        import importlib.util
        import math
        import numpy as np
        script = ROOT.parent / "docs/previews/render_crystal_awakening.py"
        spec = importlib.util.spec_from_file_location("c_edge_fed_portal", script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        self.assertEqual(mod.energy_phase(0), 0.)
        self.assertGreater(mod.energy_phase(2.5), .99)
        self.assertGreater(mod.energy_phase(4.8), .99)
        self.assertLess(mod.energy_phase(5.5), .6)
        self.assertEqual(mod.energy_phase(6.25), 0.)
        self.assertEqual(mod.portal_phase(6.25), 0.)
        self.assertEqual(mod.crystal_phase(6.30), 0.)
        for i in (0,7,18,32,51):
            edge = mod.rim_source(i)
            start=mod.advect_energy(edge, 0.)
            later=mod.advect_energy(edge, .5)
            def polar(p):
                return (math.hypot((p[0]-mod.PORTAL_X)/127.,
                                   (p[1]-mod.PORTAL_Y)/130.),
                        math.atan2(-(p[1]-mod.PORTAL_Y)/130.,
                                   (p[0]-mod.PORTAL_X)/127.))
            r0, theta0 = polar(start)
            r1, theta1 = polar(later)
            self.assertLess(r1, r0, "Energy must be pulled inward")
            turn=(theta1-theta0+math.pi)%(2*math.pi)-math.pi
            self.assertGreater(turn, .4, "Energy must circulate counterclockwise")
        mask=mod.opening_mask()
        self.assertGreater(mask.max(),.99)
        self.assertEqual(mask.shape, (mod.FEED_Y1-mod.FEED_Y0,
                                      mod.FEED_X1-mod.FEED_X0))
        halo, filaments, sparks=mod.make_energy_streams(3.)
        self.assertGreater(float(halo.max()),.01)
        self.assertGreater(float(filaments.max()),.02)
        self.assertGreater(float(sparks.max()),.02)
        self.assertGreater(float(np.count_nonzero(filaments>.06)),100)
        self.assertTrue(np.all(halo>=0.))
        self.assertTrue(np.all(filaments>=0.))
        # The actual seven-second source audio ends in digital silence.
        self.assertEqual(audio.sample(6.35), 0.)

    def test_cinematic_full_screen_crystal_reveal_has_no_loading_bar(self):
        # Portrait source is a proper 960x1840 composition, not a zoomed
        # square icon or a second floating image on blurred wallpaper.
        view = BOOT.split("private static FrameLayout createBootView(Activity activity) {",1)[1].split("private static int density(Activity activity, int size)",1)[0]
        self.assertEqual(view.count("new CrystalArtwork(activity)"), 1)
        self.assertEqual(view.count("ImageView.ScaleType.CENTER_CROP"), 1)
        self.assertIn("R.drawable.charoite_next_boot_portrait", view)
        self.assertIn("R.drawable.charoite_next_boot_unframed", view)
        self.assertIn("setImageResource(w <= h", view)
        self.assertNotIn("ImageView.ScaleType.MATRIX", view)
        self.assertIn("new CrystalWordmark(activity)", view)
        self.assertIn('WORDMARK = "CHAROITE PORTAL"', view)
        self.assertIn("new LinearGradient(", view)
        self.assertIn("canvas.drawText(WORDMARK, x, y, lettering)", view)
        self.assertIn("diamond(canvas,", view)
        self.assertIn("R.drawable.charoite_next_boot_unframed", view)
        self.assertIn("ViewGroup.LayoutParams.MATCH_PARENT", view)
        self.assertIn("boot.addView(artwork", view)
        self.assertIn("boot.addView(shimmer", view)
        self.assertIn("boot.addView(title", view)
        self.assertIn("new CrystalShimmer(activity)", view)
        self.assertNotIn("ImageView.ScaleType.FIT_CENTER", view)
        self.assertNotIn("ART_CROP_RELIEF", view)
        self.assertNotIn("R.drawable.charoite_next_boot_backdrop", view)
        self.assertNotIn("LinearLayout emblem", view)
        self.assertNotIn("FrameLayout scene", view)
        self.assertNotIn("scaleX", view)
        self.assertNotIn("scaleY", view)
        self.assertNotIn("ObjectAnimator", view)
        self.assertNotIn("AnimatorSet", view)
        self.assertNotIn("ProgressBar", view)
        self.assertNotIn("progressBarStyleHorizontal", view)
        self.assertNotIn("STARTING CHAROITE CORE", view)
        self.assertNotIn('title.setText(', view)

    def test_crystal_glow_is_gentle_time_bounded_and_aligned_to_cropped_artwork(self):
        effect = BOOT.split("private static final class CrystalShimmer extends View {",1)[1].split("private static int density(Activity activity, int size)",1)[0]
        self.assertIn("CRYSTAL_TIPS", effect)
        self.assertIn("RadialGradient", effect)
        # Map crystal-tip coordinates to the original center of the
        # generated 960x1840 image rather than the old square icon.
        self.assertIn("PORTRAIT_ART_WIDTH", effect)
        self.assertIn("PORTRAIT_ART_HEIGHT", effect)
        self.assertIn("crystalX(.505f, w, h)", effect)
        self.assertIn("crystalY(.46f, w, h)", effect)
        self.assertIn("crystalX(CRYSTAL_TIPS[i][0], w, h)", effect)
        self.assertIn("crystalY(CRYSTAL_TIPS[i][1], w, h)", effect)
        self.assertIn("float sourceY = fraction * 1536f", effect)
        self.assertIn("410f + (sourceY - 113f) * (960f / 1308f)", effect)
        self.assertNotIn("845f / 800f", effect)
        self.assertNotIn("1020f / 1406f", effect)
        self.assertIn("crystalX(CRYSTAL_TIPS[i][0], w, h)", effect)
        self.assertIn("crystalY(CRYSTAL_TIPS[i][1], w, h)", effect)
        self.assertIn("postInvalidateOnAnimation()", effect)
        self.assertIn("elapsed < BOOT_DURATION_MS", effect)
        self.assertIn("isAttachedToWindow()", effect)
        self.assertIn("onDetachedFromWindow()", effect)
        self.assertIn("Eight subdued crystal-tip glints", BOOT)
        self.assertNotIn("ProcessBuilder", effect)
        self.assertNotIn("java.util.Random", effect)

    def test_direct_task_fallback_occurs_only_on_creation(self):
        # Regression for 0.16: finishing the launcher while Portal remains
        # alive prevented the next genuinely fresh task from showing splash.
        direct = BOOT.split("public static void onPortalCreated(Activity portal, Bundle state) {",1)[1].split("public static void onPortalPostCreated",1)[0]
        self.assertIn("onPortalCreated", BOOT)
        self.assertIn("state != null && seen == version", direct)
        self.assertIn("pendingColdFallbackOwner = portal", direct)
        self.assertIn("portal.isTaskRoot()", direct)
        self.assertIn("installedVersion", direct)
        self.assertIn("intent.getBooleanExtra(EXTRA_PLAY_CHIME, false)", direct)
        resume = BOOT.split("public static void onPortalResumed(Activity portal) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("showColdPortalFallback", resume)
        self.assertNotIn("createBootView(", resume)
        # New Portal starts from the launcher; switching apps is just resume.
        self.assertNotIn(".notePortalPaused(this)", PREP)
        self.assertNotIn(".noteUserLeaving(this)", PREP)

    def test_fallback_covers_first_frame_without_portal_flash(self):
        # v0.17 was delayed by at least 80 ms after window attachment,
        # exposing the main page before the splash appeared.
        start = BOOT.split("public static void onPortalPostCreated(Activity portal) {",1)[1]
        install = start.split("OVERLAY_HANDLER.postDelayed",1)[0]
        self.assertIn("pendingColdFallbackOwner != portal", install)
        self.assertIn("content.addView(splash", install)
        self.assertIn("splash.bringToFront()", install)
        self.assertIn("markBootShown(portal)", install)
        self.assertNotIn("decorView().post", install)
        self.assertNotIn("postDelayed(() ->", install)
        self.assertNotIn("isAttachedToWindow()", install)
        # install must finish *before* the 5-second dismissal is scheduled
        self.assertLess(install.index("content.addView(splash"),
                        install.index("markBootShown(portal)"))
        self.assertIn("onPortalPostCreated(this)", PREP)
        self.assertNotIn("showColdPortalFallback(", BOOT)
        self.assertIn("pendingColdFallbackOwner = null", BOOT)

    def test_seven_second_audio_starts_under_splash_and_ends_before_portal(self):
        from array import array
        import math
        self.assertIn("BOOT_DURATION_MS = 7000L", BOOT)
        self.assertIn("playCrystalChime(this);", BOOT)
        self.assertIn("playCrystalChime(portal);", BOOT)
        self.assertIn("stopBootSound(this);", BOOT)
        self.assertIn("stopBootSound(portal);", BOOT)
        self.assertIn("new android.media.AudioTrack.Builder()", BOOT)
        self.assertIn("android.media.AudioTrack.MODE_STATIC", BOOT)
        self.assertIn("MediaPlayer.create(activity", BOOT)
        self.assertIn("R.raw.charoite_crystal_startup", BOOT)
        self.assertIn("AudioAttributes.USAGE_MEDIA", BOOT)
        self.assertIn("activity.getWindow().getDecorView().post(() ->", BOOT)
        self.assertNotIn("COLD_ARRIVAL_SOUND_PENDING", BOOT)
        self.assertNotIn("playPendingColdArrivalIfReady", BOOT)
        self.assertNotIn("main.putExtra(EXTRA_PLAY_CHIME, true)", BOOT)
        main_launch = BOOT.split("openMain = () -> {",1)[1].split("handler.postDelayed(openMain",1)[0]
        self.assertIn("stopBootSound(this);", main_launch)
        self.assertNotIn("playCrystalChime(", main_launch)

        arrival = BOOT.split("public static void playArrivalChimeIfRequested(Activity activity) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("playCrystalChime(", arrival)
        self.assertNotIn("postDelayed", arrival)
        focus = BOOT.split("public static void onPortalWindowFocusChanged(Activity portal, boolean focused) {",1)[1].split("\n    }",1)[0]
        self.assertNotIn("playCrystalChime(", focus)
        self.assertNotIn("postDelayed", focus)
        self.assertIn("stopBootSound(portal);", BOOT)
        self.assertIn("splash.animate().alpha(0f).setDuration(650L)", BOOT)
        self.assertIn("BOOT_DURATION_MS - 650L", BOOT)

        with tempfile.TemporaryDirectory() as td:
            wav = Path(td)/"startup.wav"
            self.assertEqual(audio.generate(wav),308700)
            with wave.open(str(wav),"rb") as tone:
                self.assertEqual(tone.getnchannels(),1)
                self.assertEqual(tone.getsampwidth(),2)
                self.assertEqual(tone.getframerate(),44100)
                self.assertEqual(tone.getnframes(),308700)
                decoded = array("h")
                decoded.frombytes(tone.readframes(tone.getnframes()))
                def rms(a,b):
                    subset=decoded[round(a*44100):round(b*44100):60]
                    return math.sqrt(sum(x*x for x in subset)/len(subset))/32768
                self.assertGreater(rms(.5,2.5), .015)
                self.assertGreater(rms(3.3,4.7), .008,
                                   "Seven-second crystal sound must remain audible before final fade")
                self.assertLess(rms(6.55,6.95), rms(4.3,4.7)*.05,
                                "Crystal ambience must fade cleanly at boot end")

    def test_no_access_to_saved_games(self):
        for forbidden in ("ProcessBuilder", "deleteRecursively", "finishAffinity()",
                          "finishAndRemoveTask()", "clearApplicationUserData", "WINEPREFIX"):
            self.assertNotIn(forbidden, BOOT)
        self.assertIn("applicationId 'com.charoitx'", PREP)


if __name__ == "__main__":
    unittest.main()
