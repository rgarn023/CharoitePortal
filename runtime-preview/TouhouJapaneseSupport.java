package com.winlator;

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
 * Local-only Japanese text support. Installs SIL-OFL Noto fonts and glibc
 * ja_JP.utf8 without replacing or deleting the user's existing game prefix.
 *
 * Wine maps Japanese Shift-JIS/CP932 applications based on locale. Fonts are
 * separately needed so decoded characters can be displayed as Japanese glyphs.
 */
public final class TouhouJapaneseSupport {
    private static final String FONT_NAME = "NotoSansCJKjp-Regular.otf";
    private static final String FONT_FAMILY = "Noto Sans CJK JP";
    private static final String ADDON = "japanese/japanese-support.tzst";
    private static final String DIALOG_FALLBACK_VERSION = "v4";
    private static final String IPA_GOTHIC = "IPA Gothic";
    private static final String IPA_P_GOTHIC = "IPA P Gothic";

    private TouhouJapaneseSupport() {}

    public static synchronized void ensure(Context context, RootFS rootFS, Container container)
            throws IOException {
        File root = rootFS.getRootDir();
        File locale = new File(root, "usr/lib/locale/ja_JP.utf8/LC_CTYPE");
        File linuxFont = new File(root, "usr/share/fonts/opentype/noto/" + FONT_NAME);
        File ipaGothic = new File(root, "usr/share/fonts/truetype/ipa/ipag.ttf");
        File ipaPGothic = new File(root, "usr/share/fonts/truetype/ipa/ipagp.ttf");
        if (!locale.isFile() || !linuxFont.isFile() || !ipaGothic.isFile() || !ipaPGothic.isFile()) {
            TouhouDiagnostics.recordLine("Installing bundled Japanese locale and Noto font...");
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
        File registrationMarker = new File(prefix, ".touhou-japanese-fonts-v4");
        File winIPA = new File(windowsFonts, "ipag.ttf");
        File winIPAP = new File(windowsFonts, "ipagp.ttf");
        if (registrationMarker.isFile() && windowsFont.isFile()
                && windowsFont.length() == linuxFont.length()
                && winIPA.isFile() && winIPA.length() == ipaGothic.length()
                && winIPAP.isFile() && winIPAP.length() == ipaPGothic.length()) {
            TouhouDiagnostics.recordLine("Japanese TrueType fonts installed (v4).");
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
        if (!FileUtils.writeString(registrationMarker, DIALOG_FALLBACK_VERSION + "\n")) {
            throw new IOException("Could not mark Japanese font registration complete");
        }
        TouhouDiagnostics.recordLine("Japanese UI fonts registered (" + DIALOG_FALLBACK_VERSION +
                "): IPA Gothic/IPA P Gothic, ACP=932, MS Shell Dlg.");
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
                "    <family>MS Shell Dlg</family><prefer><family>IPA P Gothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias binding=\"strong\">\n" +
                "    <family>MS Shell Dlg 2</family><prefer><family>IPA P Gothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias binding=\"strong\">\n" +
                "    <family>Tahoma</family><prefer><family>IPA P Gothic</family></prefer>\n" +
                "  </alias>\n" +
                "  <alias><family>sans-serif</family><prefer><family>IPA P Gothic</family></prefer></alias>\n" +
                "</fontconfig>\n";
        if (!FileUtils.writeString(target, xml))
            throw new IOException("Unable to install Touhou Fontconfig fallback");
    }
}
