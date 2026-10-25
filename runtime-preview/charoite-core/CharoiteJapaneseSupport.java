package com.charoitegames.core;


import android.content.Context;

import com.winlator.container.Container;
import com.winlator.core.FileUtils;
import com.winlator.core.TarCompressorUtils;
import com.winlator.core.WineRegistryEditor;
import com.winlator.core.WineUtils;
import com.winlator.xenvironment.RootFS;

import java.io.File;
import java.io.IOException;

/**
 * Reusable opt-in Charoite Core Japanese text support. Installs SIL-OFL Noto fonts and glibc
 * ja_JP.utf8 without replacing or deleting the user's existing game prefix.
 *
 * Wine maps Japanese Shift-JIS/CP932 applications based on locale. Fonts are
 * separately needed so decoded characters can be displayed as Japanese glyphs.
 */
public final class CharoiteJapaneseSupport {
    private static final String FONT_NAME = "NotoSansCJKjp-Regular.otf";
    private static final String FONT_FAMILY = "Noto Sans CJK JP";
    private static final String ADDON = "japanese/japanese-support.tzst";
    private static final String DIALOG_FALLBACK_VERSION = "v5";
    private static final String IPA_GOTHIC = "IPAGothic";
    private static final String IPA_P_GOTHIC = "IPAPGothic";

    private CharoiteJapaneseSupport() {}

    public static synchronized void ensure(Context context, RootFS rootFS, Container container)
            throws IOException {
        File root = rootFS.getRootDir();
        File locale = new File(root, "usr/lib/locale/ja_JP.utf8/LC_CTYPE");
        File linuxFont = new File(root, "usr/share/fonts/opentype/noto/" + FONT_NAME);
        File ipaGothic = new File(root, "usr/share/fonts/truetype/ipa/ipag.ttf");
        File ipaPGothic = new File(root, "usr/share/fonts/truetype/ipa/ipagp.ttf");
        if (!locale.isFile() || !linuxFont.isFile() || !ipaGothic.isFile() || !ipaPGothic.isFile()) {
            CharoiteDiagnostics.recordLine("Installing bundled Japanese locale and Noto font...");
            if (!TarCompressorUtils.extract(TarCompressorUtils.Type.ZSTD,
                    context, ADDON, root)) {
                throw new IOException("Unable to extract Japanese locale/font pack");
            }
        }
        if (!locale.isFile() || !linuxFont.isFile() || linuxFont.length() < 4000000) {
            throw new IOException("Japanese locale or font installation incomplete");
        }

        if (!ipaGothic.isFile() || !ipaPGothic.isFile() ||
                ipaGothic.length() < 3000000 || ipaPGothic.length() < 3000000)
            throw new IOException("Required IPA Gothic Japanese TrueType font missing");
        installFontConfigFallback(root);

        File prefix = new File(container.getRootDir(), ".wine");
        File userReg = new File(prefix, "user.reg");
        File systemReg = new File(prefix, "system.reg");
        if (!prefix.isDirectory() || !userReg.isFile() || !systemReg.isFile()) {
            throw new IOException("Wine prefix not initialized for Japanese font registration");
        }
        File windowsFonts = new File(prefix, "drive_c/windows/Fonts");
        if (!windowsFonts.isDirectory() && !windowsFonts.mkdirs()) {
            throw new IOException("Cannot create Windows Japanese Fonts folder");
        }
        File windowsFont = new File(windowsFonts, FONT_NAME);
        // Read-only Win32 probe gets a file in this Wine C: drive; it never
        // changes the original Windows setup.exe or its destination.
        File probe = new File(prefix, "drive_c/touhou_probe.exe");
        if (!probe.isFile() || probe.length() < 10000) {
            FileUtils.copy(context, "japanese/touhou_probe.exe", probe);
            if (!probe.isFile() || probe.length() < 10000)
                CharoiteDiagnostics.recordLine("Optional Japanese probe asset copy failed.");
        }
        // Older installations keep app-owned helper binaries in C: across
        // APK updates. Refresh them once per helper release, not only when
        // missing, so the multi-page Japanese font repair actually upgrades.
        // Do not touch the user's games, installers, directories or saves.
        File helperVersion = new File(prefix, ".touhou-japanese-helpers-v11");
        if (!helperVersion.isFile()) {
            for (String helper : new String[]{
                    "touhou_probe.exe",
                    "touhou_font_helper32.exe", "touhou_font_helper64.exe",
                    "touhou_font_hook32.dll", "touhou_font_hook64.dll"}) {
                File target = new File(prefix, "drive_c/" + helper);
                FileUtils.copy(context, "japanese/" + helper, target);
                if (
                        !target.isFile() || target.length() < 5000)
                    throw new IOException("Unable to refresh Japanese compatibility helper: " + helper);
            }
            if (!FileUtils.writeString(helperVersion, "v11\n"))
                throw new IOException("Cannot mark Japanese helper upgrade complete");
            CharoiteDiagnostics.recordLine("Charoite Core Japanese installer compatibility helpers upgraded to v11.");
        }
        for (String logName : new String[]{
                "touhou_probe.log", "touhou_font_hook.log", "touhou_font_helper.log"}) {
            File previousLog = new File(prefix, "drive_c/" + logName);
            if (previousLog.isFile() && !previousLog.delete())
                CharoiteDiagnostics.recordLine("Previous report could not be cleared: " + logName);
        }
        File registrationMarker = new File(prefix, ".touhou-japanese-fonts-v5");
        File winIPA = new File(windowsFonts, "ipag.ttf");
        File winIPAP = new File(windowsFonts, "ipagp.ttf");
        if (registrationMarker.isFile() && windowsFont.isFile()
                && windowsFont.length() == linuxFont.length()
                && winIPA.isFile() && winIPA.length() == ipaGothic.length()
                && winIPAP.isFile() && winIPAP.length() == ipaPGothic.length()) {
            // The legacy fonts-v5 marker predates Notepad's independent
            // document-font preference. Run its one-time default migration
            // even for already-installed prefixes; never reformat a prefix.
            configureJapaneseNotepadDefaults(userReg);
            CharoiteDiagnostics.recordLine("Japanese TrueType fonts installed (v5).");
            return;
        }
        if (!FileUtils.copy(linuxFont, windowsFont)
                || windowsFont.length() != linuxFont.length()) {
            throw new IOException("Unable to copy Japanese font into Windows prefix");
        }
        if ((!winIPA.isFile() || winIPA.length() != ipaGothic.length()) &&
                (!FileUtils.copy(ipaGothic, winIPA) || winIPA.length() != ipaGothic.length()))
            throw new IOException("Cannot install IPA Gothic TrueType font");
        if ((!winIPAP.isFile() || winIPAP.length() != ipaPGothic.length()) &&
                (!FileUtils.copy(ipaPGothic, winIPAP) || winIPAP.length() != ipaPGothic.length()))
            throw new IOException("Cannot install IPA P Gothic TrueType font");

        // Register the OpenType font and the traditional face names requested
        // by old non-Unicode Touhou installers (not an MS proprietary font).
        try (WineRegistryEditor system = new WineRegistryEditor(systemReg)) {
            for (String key : new String[]{
                    "Software\\Microsoft\\Windows\\CurrentVersion\\Fonts",
                    "Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts"}) {
                system.setStringValue(key, FONT_FAMILY + " (OpenType)", FONT_NAME);
                system.setStringValue(key, IPA_GOTHIC + " (TrueType)", "ipag.ttf");
                system.setStringValue(key, IPA_P_GOTHIC + " (TrueType)", "ipagp.ttf");
            }
            final String fontSubstitutes =
                    "Software\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes";
            for (String alias : new String[]{
                    "MS Gothic", "MS Mincho", "ＭＳ ゴシック", "ＭＳ 明朝"}) {
                system.setStringValue(fontSubstitutes, alias, IPA_GOTHIC);
            }
            for (String alias : new String[]{
                    "MS PGothic", "MS UI Gothic", "ＭＳ Ｐゴシック", "ＭＳ ＵＩ ゴシック",
                    "MS Shell Dlg", "MS Shell Dlg 2", "Tahoma", "Meiryo", "Meiryo UI",
                    "Yu Gothic", "Yu Gothic UI", "Microsoft Sans Serif", "MS Sans Serif"}) {
                system.setStringValue(fontSubstitutes, alias, IPA_P_GOTHIC);
            }
            // Wine uses code page 932 for many non-Unicode Japanese setup
            // programs. Wine should infer ACP from LANG, but these explicit
            // NLS keys help preserve existing prefixes created under English.
            final String nls = "System\\CurrentControlSet\\Control\\Nls\\CodePage";
            system.setStringValue(nls, "ACP", "932");
            system.setStringValue(nls, "OEMCP", "932");
        }
        try (WineRegistryEditor user = new WineRegistryEditor(userReg)) {
            user.setStringValue("Control Panel\\International", "Locale", "00000411");
            user.setStringValue("Control Panel\\International", "LocaleName", "ja-JP");
            WineUtils.setSystemFont(user, IPA_P_GOTHIC);

            // Winetricks fakejapanese uses HKCU Wine\Fonts\Replacements:
            // the Windows FontSubstitutes key alone does not cover all Wine
            // GDI edit controls, especially Japanese installation paths.
            String replacements = "Software\\Wine\\Fonts\\Replacements";
            for (String face : new String[]{
                    "MS Gothic", "MS Mincho", "ＭＳ ゴシック", "ＭＳ 明朝"}) {
                user.setStringValue(replacements, face, IPA_GOTHIC);
            }
            for (String face : new String[]{
                    "MS PGothic", "MS UI Gothic", "ＭＳ Ｐゴシック", "ＭＳ ＵＩ ゴシック",
                    "MS Shell Dlg", "MS Shell Dlg 2", "Tahoma", "Meiryo", "Meiryo UI",
                    "Yu Gothic", "Yu Gothic UI", "MS PMincho", "ＭＳ Ｐ明朝",
                    "Microsoft Sans Serif", "MS Sans Serif"}) {
                user.setStringValue(replacements, face, IPA_P_GOTHIC);
            }
        }
        // Notepad's edit control does not use the system dialog font.
        // Seed a Japanese-capable font only if Notepad has no custom choice.
        configureJapaneseNotepadDefaults(userReg);
        if (!FileUtils.writeString(registrationMarker, DIALOG_FALLBACK_VERSION + "\n")) {
            throw new IOException("Could not mark Japanese font registration complete");
        }
        CharoiteDiagnostics.recordLine("Japanese UI fonts registered (" + DIALOG_FALLBACK_VERSION +
                "): IPA Gothic/IPA P Gothic, ACP=932, MS Shell Dlg.");
    }

    /**
     * Wine's built-in Notepad reads HKCU\\Software\\Microsoft\\Notepad
     * lfFaceName and lfCharSet for its document Edit control. Its stock face
     * is "System", which lacks the Japanese glyphs used by Shift-JIS README
     * files even when localized menus and the Wine CP932 locale are correct.
     *
     * Only the uncustomized default may be upgraded. Preserve deliberately
     * chosen fonts/charsets, every game file and all unrelated Wine apps.
     * The installer font hook and Wine-wide font substitution are unchanged.
     */
    private static void configureJapaneseNotepadDefaults(File userReg) {
        final String key = "Software\\\\Microsoft\\\\Notepad";
        try (WineRegistryEditor registry = new WineRegistryEditor(userReg)) {
            String face = registry.getStringValue(key, "lfFaceName", "");
            if (face == null) face = "";
            face = face.trim();
            if (!face.isEmpty() && !face.equalsIgnoreCase("System")) {
                // A prior choice such as Consolas or MS Gothic is user-owned.
                return;
            }
            registry.setStringValue(key, "lfFaceName", IPA_GOTHIC);
            Integer charset = registry.getDwordValue(key, "lfCharSet");
            // 1=DEFAULT_CHARSET, 0=ANSI_CHARSET, 128=SHIFTJIS_CHARSET.
            if (charset == null || charset == 0 || charset == 1)
                registry.setDwordValue(key, "lfCharSet", 128);
            CharoiteDiagnostics.recordLine(
                    "Japanese Notepad default: IPAGothic, Shift-JIS compatible font; " +
                    "readme bytes and custom Notepad preferences preserved.");
        }
    }

    /** Fontconfig is used by Wine/Freetype for font selection. This only
     * creates a Touhou-specific fallback file; it never modifies OS fonts. */
    private static void installFontConfigFallback(File root) throws IOException {
        File target = new File(root, "etc/fonts/conf.d/66-touhou-japanese.conf");
        // Refresh an older Noto-based fallback for existing Wine prefixes.
        // This file is app-specific; no OS-level font settings are changed.
        File parent = target.getParentFile();
        if (!parent.isDirectory() && !parent.mkdirs())
            throw new IOException("Could not prepare Wine Fontconfig directory");
        String xml = "<?xml version=\"1.0\"?>\n" +
                "<!DOCTYPE fontconfig SYSTEM \"fonts.dtd\">\n" +
                "<fontconfig>\n" +
                "  <alias binding=\"strong\">\n" +
                "    <family>MS Shell Dlg</family><prefer><family>IPAPGothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias binding=\"strong\">\n" +
                "    <family>MS Shell Dlg 2</family><prefer><family>IPAPGothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias binding=\"strong\">\n" +
                "    <family>Tahoma</family><prefer><family>IPAPGothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias><family>sans-serif</family><prefer><family>IPAPGothic</family></prefer></alias>\n" +
                "</fontconfig>\n";
        if (!FileUtils.writeString(target, xml))
            throw new IOException("Unable to install Touhou Fontconfig fallback");
    }
}
