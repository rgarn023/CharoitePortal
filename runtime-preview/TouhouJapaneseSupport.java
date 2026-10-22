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

    private TouhouJapaneseSupport() {}

    public static synchronized void ensure(Context context, RootFS rootFS, Container container)
            throws IOException {
        File root = rootFS.getRootDir();
        File locale = new File(root, "usr/lib/locale/ja_JP.utf8/LC_CTYPE");
        File linuxFont = new File(root, "usr/share/fonts/opentype/noto/" + FONT_NAME);
        if (!locale.isFile() || !linuxFont.isFile()) {
            TouhouDiagnostics.recordLine("Installing bundled Japanese locale and Noto font...");
            if (!TarCompressorUtils.extract(TarCompressorUtils.Type.ZSTD,
                    context, ADDON, root)) {
                throw new IOException("Unable to extract Japanese locale/font pack");
            }
        }
        if (!locale.isFile() || !linuxFont.isFile() || linuxFont.length() < 4000000) {
            throw new IOException("Japanese locale or font installation incomplete");
        }

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
        File registrationMarker = new File(prefix, ".touhou-japanese-fonts-v2");
        if (registrationMarker.isFile() && windowsFont.isFile()
                && windowsFont.length() == linuxFont.length()) {
            return;
        }
        if (!FileUtils.copy(linuxFont, windowsFont)
                || windowsFont.length() != linuxFont.length()) {
            throw new IOException("Unable to copy Japanese font into Windows prefix");
        }

        // Register the OpenType font and the traditional face names requested
        // by old non-Unicode Touhou installers (not an MS proprietary font).
        try (WineRegistryEditor system = new WineRegistryEditor(systemReg)) {
            for (String key : new String[]{
                    "Software\\Microsoft\\Windows\\CurrentVersion\\Fonts",
                    "Software\\Microsoft\\Windows NT\\CurrentVersion\\Fonts"}) {
                system.setStringValue(key, FONT_FAMILY + " (OpenType)", FONT_NAME);
            }
            final String fontSubstitutes =
                    "Software\\Microsoft\\Windows NT\\CurrentVersion\\FontSubstitutes";
            for (String alias : new String[]{
                    "MS Gothic", "MS PGothic", "MS UI Gothic",
                    "Meiryo", "Yu Gothic", "ＭＳ ゴシック", "ＭＳ Ｐゴシック",
                    "ＭＳ ＵＩ ゴシック"}) {
                system.setStringValue(fontSubstitutes, alias, FONT_FAMILY);
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
            WineUtils.setSystemFont(user, FONT_FAMILY);

            // Winetricks fakejapanese uses HKCU Wine\Fonts\Replacements:
            // the Windows FontSubstitutes key alone does not cover all Wine
            // GDI edit controls, especially Japanese installation paths.
            String replacements = "Software\\Wine\\Fonts\\Replacements";
            for (String face : new String[]{
                    "MS Gothic", "MS PGothic", "MS UI Gothic",
                    "Meiryo", "Meiryo UI", "Yu Gothic", "Yu Gothic UI",
                    "MS Mincho", "MS PMincho",
                    "ＭＳ ゴシック", "ＭＳ Ｐゴシック", "ＭＳ ＵＩ ゴシック",
                    "ＭＳ 明朝", "ＭＳ Ｐ明朝", "Ｍｅｉｒｙｏ"}) {
                user.setStringValue(replacements, face, FONT_FAMILY);
            }
        }
        if (!FileUtils.writeString(registrationMarker, "v2\n")) {
            throw new IOException("Could not mark Japanese font registration complete");
        }
        TouhouDiagnostics.recordLine("Japanese locale and Noto font installed successfully.");
    }
}
