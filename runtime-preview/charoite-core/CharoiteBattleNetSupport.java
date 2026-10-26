package com.charoitegames.core;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.net.HttpURLConnection;
import java.net.URI;
import java.net.URL;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.util.Locale;

/**
 * First-party-source Battle.net Windows installer support in Charoite Core.
 * Launcher downloads are user initiated; NEVER run an EXE automatically.
 * The installed Blizzard Windows app owns its game/install self-updates.
 * No Blizzard account tokens or credentials are handled by Charoite.
 *
 * Not a claim of Diablo IV / DirectX 12 compatibility on ARM Android.
 */
public final class CharoiteBattleNetSupport {
    private CharoiteBattleNetSupport() {}

    // Blizzard's official live Windows installer redirect (not pinned to a
    // numbered EXE). Resolve again for EACH user-initiated refresh.
    public static final String LIVE_WINDOWS_INSTALLER =
            "https://downloader.battle.net/download/getInstallerForGame" +
            "?os=win&gameProgram=BATTLENET_APP&version=Live";
    public static final String WINDOWS_DOWNLOAD_PAGE =
            "https://download.battle.net/en-us/desktop";
    private static final String FILENAME = "Battle.net-Setup.exe";
    private static final long MIN_INSTALLER = 64L * 1024L;
    private static final long MAX_INSTALLER = 100L * 1024L * 1024L;

    public static File installer(File containerRoot) throws IOException {
        File drive = wineDrive(containerRoot);
        File downloads = new File(drive, "CharoitePortal/BattleNet/Installer").getCanonicalFile();
        if (!downloads.getPath().startsWith(drive.getCanonicalPath() + File.separator))
            throw new IOException("Installer path escaped the active Wine drive");
        return new File(downloads, FILENAME);
    }

    private static File wineDrive(File root) throws IOException {
        if (root == null) throw new IOException("Battle.net environment is not prepared");
        File drive = new File(root, ".wine/drive_c").getCanonicalFile();
        if (!drive.isDirectory()) throw new IOException("Prepare this environment before downloading Battle.net");
        return drive;
    }

    public static File downloadedInstaller(File root) {
        try {
            File file = installer(root);
            return file.isFile() && file.length() >= MIN_INSTALLER && validPe(file)
                    ? file : null;
        } catch (Exception ignored) {
            return null;
        }
    }

    /** Only look for actual installed launchers, not the setup executable. */
    public static File installedLauncher(File root) {
        try {
            File drive = wineDrive(root);
            String[] folders = {"Program Files (x86)/Battle.net", "Program Files/Battle.net"};
            String[] files = {"Battle.net Launcher.exe", "Battle.net.exe"};
            for (String folder : folders) for (String name : files) {
                File exe = new File(drive, folder + "/" + name).getCanonicalFile();
                if (exe.getPath().startsWith(drive.getPath() + File.separator) &&
                        exe.isFile()) return exe;
            }
        } catch (IOException ignored) {}
        return null;
    }

    private static boolean trustedWindowsDownload(URL target) {
        if (target == null || !"https".equalsIgnoreCase(target.getProtocol()) ||
                target.getPort() != -1 && target.getPort() != 443)
            return false;
        String host = target.getHost().toLowerCase(Locale.ROOT);
        // Only official Blizzard endpoints; never follow an unrelated host
        // from a redirect or download arbitrary executable URLs.
        return host.equals("downloader.battle.net") ||
                host.equals("download.battle.net") ||
                host.equals("dist.blizzard.com");
    }

    /** Strictly check that the downloaded file is a Windows PE executable. */
    private static boolean validPe(File file) {
        if (file == null || !file.isFile() || file.length() < MIN_INSTALLER ||
                file.length() > MAX_INSTALLER) return false;
        try (java.io.RandomAccessFile in = new java.io.RandomAccessFile(file, "r")) {
            if (in.readUnsignedByte() != 0x4d || in.readUnsignedByte() != 0x5a)
                return false;
            in.seek(0x3c);
            long peOffset = Integer.toUnsignedLong(Integer.reverseBytes(in.readInt()));
            if (peOffset < 0x40 || peOffset > 65536 ||
                    peOffset + 4 > in.length()) return false;
            in.seek(peOffset);
            return in.readUnsignedByte() == 'P' && in.readUnsignedByte() == 'E' &&
                    in.readUnsignedByte() == 0 && in.readUnsignedByte() == 0;
        } catch (IOException ignored) {
            return false;
        }
    }

    public static final class Download {
        public final File file;
        public final long bytes;
        public final String sha256;
        Download(File file, long bytes, String sha256) {
            this.file = file; this.bytes = bytes; this.sha256 = sha256;
        }
    }

    /**
     * Run ONLY on a background worker after a deliberate download tap.
     * Fetch the latest Blizzard redirect, stage to a temporary file, check
     * the PE structure and length, then replace ONLY the previous installer.
     * Installed Battle.net, game content and saves are never modified.
     */
    public static Download downloadLatestInstaller(File containerRoot) throws Exception {
        File destination = installer(containerRoot);
        File parent = destination.getParentFile();
        if (!parent.isDirectory() && !parent.mkdirs())
            throw new IOException("Cannot create Battle.net download directory");
        File part = new File(parent, FILENAME + ".part");
        if (part.exists() && !part.delete())
            throw new IOException("Cannot replace an incomplete previous download");
        URL url = new URL(LIVE_WINDOWS_INSTALLER);
        MessageDigest digest = MessageDigest.getInstance("SHA-256");
        long received = 0;
        try {
            HttpURLConnection connection = null;
            for (int redirect = 0; redirect < 6; redirect++) {
                if (!trustedWindowsDownload(url))
                    throw new IOException("Battle.net download redirected outside Blizzard");
                connection = (HttpURLConnection)url.openConnection();
                connection.setInstanceFollowRedirects(false);
                connection.setConnectTimeout(20000);
                connection.setReadTimeout(45000);
                connection.setRequestProperty("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64)");
                int code = connection.getResponseCode();
                if (code == 301 || code == 302 || code == 303 || code == 307 || code == 308) {
                    String location = connection.getHeaderField("Location");
                    if (location == null || location.trim().isEmpty())
                        throw new IOException("Blizzard returned an empty installer redirect");
                    URL next = new URL(url, location);
                    connection.disconnect();
                    connection = null;
                    url = next;
                    continue;
                }
                if (code != 200) throw new IOException("Blizzard installer request returned HTTP " + code);
                long advertised = connection.getContentLengthLong();
                if (advertised > MAX_INSTALLER)
                    throw new IOException("Battle.net installer exceeds safety download limit");
                try (InputStream input = connection.getInputStream();
                     FileOutputStream out = new FileOutputStream(part)) {
                    byte[] buffer = new byte[65536];
                    for (int n; (n = input.read(buffer)) >= 0;) {
                        if (n == 0) continue;
                        received += n;
                        if (received > MAX_INSTALLER)
                            throw new IOException("Unexpectedly large Battle.net installer");
                        out.write(buffer, 0, n);
                        digest.update(buffer, 0, n);
                    }
                    out.getFD().sync();
                } finally { connection.disconnect(); }
                connection = null;
                if (received < MIN_INSTALLER || !validPe(part))
                    throw new IOException("The download is not a valid Windows Battle.net installer");
                try {
                    Files.move(part.toPath(), destination.toPath(),
                            StandardCopyOption.REPLACE_EXISTING,
                            StandardCopyOption.ATOMIC_MOVE);
                } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                    Files.move(part.toPath(), destination.toPath(),
                            StandardCopyOption.REPLACE_EXISTING);
                }
                StringBuilder sha = new StringBuilder();
                for (byte b : digest.digest())
                    sha.append(String.format(Locale.ROOT, "%02x", b & 0xff));
                return new Download(destination, received, sha.toString());
            }
            throw new IOException("Too many Battle.net installer redirects");
        } finally {
            // Never touch the last successful installer after network errors.
            if (part.exists()) part.delete();
        }
    }
}
