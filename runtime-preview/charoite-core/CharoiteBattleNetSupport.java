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
        File downloads = CharoiteEnvironments.storageFolder(
                containerRoot, CharoiteEnvironments.BATTLE_NET, "Installers");
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
            if (file.isFile() && validPe(file)) return file;
            // Previously downloaded setup files are not moved or deleted.
            // Preserve legacy install/retry until the user downloads a new EXE.
            File legacy = new File(wineDrive(root),
                    "CharoitePortal/BattleNet/Installer/" + FILENAME).getCanonicalFile();
            File drive = wineDrive(root);
            return legacy.getPath().startsWith(drive.getPath() + File.separator) &&
                    validPe(legacy) ? legacy : null;
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

    /**
     * Bounded, privacy-preserving summary of the newest Agent log files.
     * Never display raw lines, URLs, usernames, paths, credentials or tokens.
     * Categories represent log text only, NOT proof of a live Agent process.
     */
    private static String inspectRecentAgentErrors(File programData) {
        java.util.ArrayList<File> candidates = new java.util.ArrayList<>();
        File[] versions = programData.listFiles();
        if (versions != null) for (File version : versions) {
            if (java.nio.file.Files.isSymbolicLink(version.toPath()) ||
                    !version.isDirectory() ||
                    !version.getName().matches("Agent\\.[0-9]+")) continue;
            File[] logs = new File(version, "Logs").listFiles();
            if (logs == null) continue;
            for (File log : logs) if (log.isFile() &&
                    !java.nio.file.Files.isSymbolicLink(log.toPath()) &&
                    (log.getName().endsWith(".log") || log.getName().endsWith(".txt")))
                candidates.add(log);
        }
        candidates.sort((x, y) -> Long.compare(y.lastModified(), x.lastModified()));
        int sample = Math.min(4, candidates.size());
        int network = 0, tls = 0, dll = 0, agent = 0, cef = 0, errors = 0;
        java.util.TreeSet<String> blizzardCodes = new java.util.TreeSet<>();
        for (int i=0; i<sample; i++) {
            File file = candidates.get(i);
            try (java.io.RandomAccessFile input =
                    new java.io.RandomAccessFile(file, "r")) {
                long begin = Math.max(0, input.length() - 32 * 1024);
                input.seek(begin);
                byte[] raw = new byte[(int)(input.length() - begin)];
                input.readFully(raw);
                String data = new String(raw,
                        java.nio.charset.StandardCharsets.UTF_8).toLowerCase(Locale.ROOT);
                for (String line : data.split("\\r?\\n")) {
                    boolean failed = line.contains("error") ||
                            line.contains("fail") || line.contains("exception") ||
                            line.contains("unable") || line.contains("crash");
                    if (!failed) continue;
                    errors++;
                    if (line.contains("network") || line.contains("connect") ||
                            line.contains("timeout") || line.contains("http") ||
                            line.contains("curl")) network++;
                    if (line.contains("tls") || line.contains("ssl") ||
                            line.contains("certificate")) tls++;
                    if (line.contains("dll") || line.contains("module") ||
                            line.contains("loadlibrary")) dll++;
                    if (line.contains("agent") || line.contains("updater") ||
                            line.contains("service")) agent++;
                    if (line.contains("cef") || line.contains("browser") ||
                            line.contains("tassadar") || line.contains("chromium")) cef++;
                    java.util.regex.Matcher code = java.util.regex.Pattern.compile(
                            "blz[a-z0-9]{8,22}").matcher(line);
                    while (code.find() && blizzardCodes.size() < 5)
                        blizzardCodes.add(code.group().toUpperCase(Locale.ROOT));
                }
            } catch (IOException ignored) {}
        }
        StringBuilder summary = new StringBuilder();
        summary.append("Recent Agent logs examined: ").append(sample).append("\n");
        summary.append("Error-like log entries: ").append(errors).append("\n");
        summary.append("  Network/timeout references: ").append(network).append("\n");
        summary.append("  TLS/certificate references: ").append(tls).append("\n");
        summary.append("  DLL/module references: ").append(dll).append("\n");
        summary.append("  Agent/updater references: ").append(agent).append("\n");
        summary.append("  CEF/browser references: ").append(cef).append("\n");
        if (!blizzardCodes.isEmpty())
            summary.append("Blizzard error codes: ")
                    .append(blizzardCodes).append("\n");
        summary.append("Log-only indicators; actual Agent process status not verified.\n");
        return summary.toString();
    }

    /**
     * Run the installed Battle.net.exe client directly when the Blizzard
     * bootstrap launcher stays at the loading emblem. Lutris documents this
     * fallback; it must not launch the setup program or replace the install.
     */
    public static File installedDirectClient(File root) {
        try {
            File drive = wineDrive(root);
            for (String folder : new String[]{
                    "Program Files (x86)/Battle.net", "Program Files/Battle.net"}) {
                File exe = new File(drive, folder + "/Battle.net.exe").getCanonicalFile();
                if (exe.getPath().startsWith(drive.getPath() + File.separator) &&
                        exe.isFile() && !java.nio.file.Files.isSymbolicLink(exe.toPath()))
                    return exe;
            }
        } catch (IOException ignored) {}
        return null;
    }

    /**
     * Agent diagnostic is deliberately READ-ONLY. The same Blizzard error
     * can mean an Agent process failed, DLLs are unavailable, or the updater
     * cannot communicate; never delete ProgramData or a Wine prefix merely
     * because the installer reports BLZBNTBTS0000005C.
     */
    public static String inspectAgent(File root) {
        final File drive;
        try { drive = wineDrive(root); }
        catch (Exception error) {
            return "Battle.net diagnostics unavailable: " + error.getMessage();
        }
        StringBuilder report = new StringBuilder();
        report.append("BATTLE.NET UPDATE AGENT\n");
        report.append("Installer error BLZBNTBTS0000005C indicates that the " +
                "Blizzard Update Agent did not start or communicate.\n");
        File programData = new File(drive, "ProgramData/Battle.net/Agent");
        report.append("Agent directory exists: ").append(programData.isDirectory()).append("\n");
        java.io.File[] versions = programData.listFiles();
        int agents = 0, logs = 0, errors = 0;
        long newestLog = 0;
        if (versions != null) {
            for (File item : versions) {
                if (java.nio.file.Files.isSymbolicLink(item.toPath())) continue;
                if (item.isFile() && item.getName().equalsIgnoreCase("Agent.exe"))
                    agents++;
                if (!item.isDirectory() ||
                        !item.getName().matches("Agent\\.[0-9]+")) continue;
                File exe = new File(item, "Agent.exe");
                if (exe.isFile() && !java.nio.file.Files.isSymbolicLink(exe.toPath()))
                    agents++;
                File logFolder = new File(item, "Logs");
                File[] recent = logFolder.listFiles();
                if (recent != null) for (File log : recent) {
                    if (log.isFile() && !java.nio.file.Files.isSymbolicLink(log.toPath())
                            && (log.getName().endsWith(".log") ||
                                log.getName().endsWith(".txt"))) {
                        logs++;
                        if (log.getName().toLowerCase(Locale.ROOT).contains("error"))
                            errors++;
                        newestLog = Math.max(newestLog, log.lastModified());
                    }
                }
            }
        }
        report.append("Agent.exe copies detected: ").append(agents).append("\n");
        report.append(inspectRecentAgentErrors(programData));
        report.append("Agent log files: ").append(logs)
                .append(" (error-named: ").append(errors).append(")\n");
        if (newestLog > 0) report.append("Newest log modified: ")
                .append(new java.util.Date(newestLog)).append("\n");
        report.append("Launcher executable detected: ")
                .append(installedLauncher(root) != null).append("\n");
        report.append("No game files, logs or Agent state have been changed.\n");
        report.append("Check System > Launch Diagnostics for Wine process/DLL " +
                "errors. If Agent.exe exists but cannot execute, this may be " +
                "a Wine/Box64 runtime incompatibility rather than a bad download. " +
                "DirectX 12 game compatibility is still unverified.");
        return report.toString();
    }

    /**
     * Apply Lutris' documented Battle.net browser hardware-acceleration
     * setting to EXISTING config files, after explicit user confirmation.
     * Make a one-time rollback copy first. Preserve all other JSON keys.
     * Do not delete Blizzard caches, tokens, accounts, Agent or game data.
     */
    public static String applyBrowserSoftwareSetting(File root) throws Exception {
        File drive = wineDrive(root);
        File users = new File(drive, "users");
        File[] profiles = users.listFiles();
        if (profiles == null) throw new IOException("Wine user profiles unavailable");
        int updated = 0, unchanged = 0, invalid = 0;
        java.util.HashSet<String> visited = new java.util.HashSet<>();
        for (File profile : profiles) {
            if (!profile.isDirectory() || java.nio.file.Files.isSymbolicLink(profile.toPath()))
                continue;
            for (String location : new String[]{
                    "AppData/Roaming/Battle.net/Battle.net.config",
                    "Application Data/Battle.net/Battle.net.config"}) {
                File file = new File(profile, location);
                if (!file.isFile() || java.nio.file.Files.isSymbolicLink(file.toPath()) ||
                        file.length() > 256 * 1024) continue;
                // Wine usually symlinks Application Data to AppData/Roaming:
                // never follow a duplicate or backup path outside drive_c.
                File canonical = file.getCanonicalFile();
                if (!canonical.getPath().startsWith(drive.getPath() + File.separator))
                    continue;
                if (!visited.add(canonical.getPath()))
                    continue;
                byte[] bytes = java.nio.file.Files.readAllBytes(canonical.toPath());
                org.json.JSONObject config;
                try { config = new org.json.JSONObject(
                        new String(bytes, java.nio.charset.StandardCharsets.UTF_8)); }
                catch (org.json.JSONException bad) { invalid++; continue; }
                org.json.JSONObject client = config.optJSONObject("Client");
                if (client == null) {
                    client = new org.json.JSONObject();
                    config.put("Client", client);
                }
                if ("false".equalsIgnoreCase(client.optString("HardwareAcceleration"))) {
                    unchanged++;
                    continue;
                }
                File backup = new File(canonical.getParentFile(),
                        "Battle.net.config.charoite-backup-v1");
                if (!backup.exists()) {
                    java.nio.file.Files.copy(canonical.toPath(), backup.toPath());
                }
                client.put("HardwareAcceleration", "false");
                File pending = new File(canonical.getParentFile(),
                        "Battle.net.config.charoite-tmp");
                java.nio.file.Files.write(pending.toPath(),
                        config.toString(2).getBytes(java.nio.charset.StandardCharsets.UTF_8));
                try {
                    java.nio.file.Files.move(pending.toPath(), canonical.toPath(),
                            java.nio.file.StandardCopyOption.ATOMIC_MOVE,
                            java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                } catch (java.nio.file.AtomicMoveNotSupportedException unsupported) {
                    java.nio.file.Files.move(pending.toPath(), canonical.toPath(),
                            java.nio.file.StandardCopyOption.REPLACE_EXISTING);
                }
                updated++;
                break; // only a single profile's equivalent config
            }
        }
        return "Battle.net browser acceleration setting: " + updated +
                " configuration(s) updated, " + unchanged + " already disabled, " +
                invalid + " unreadable JSON file(s) left unchanged. " +
                "Backups are Battle.net.config.charoite-backup-v1. " +
                "No Agent, games, cache, session data or Wine prefix was removed.";
    }

    /**
     * User-initiated Wine guest network probe. Installs only a Charoite-owned
     * executable in this container's C: diagnostics directory. No Blizzard
     * files or Wine registry settings are touched.
     */
    public static File prepareGuestNetworkProbe(android.content.Context context,
                                                 File root) throws IOException {
        File drive = wineDrive(root);
        File folder = new File(drive, "CharoitePortal/Diagnostics");
        if (!folder.isDirectory() && !folder.mkdirs())
            throw new IOException("Cannot create Core diagnostics directory");
        File probe = new File(folder, "charoite_bnet_network_probe.exe");
        File pending = new File(folder, "charoite_bnet_network_probe.tmp");
        try (InputStream input = context.getAssets().open(
                    "diagnostics/charoite_bnet_network_probe.exe");
             FileOutputStream out = new FileOutputStream(pending)) {
            byte[] buffer = new byte[8192];
            int n;
            while ((n = input.read(buffer)) != -1) out.write(buffer, 0, n);
        }
        if (pending.length() < 5000) {
            pending.delete();
            throw new IOException("Incomplete Wine network diagnostic");
        }
        try {
            Files.move(pending.toPath(), probe.toPath(),
                    StandardCopyOption.ATOMIC_MOVE,
                    StandardCopyOption.REPLACE_EXISTING);
        } catch (java.nio.file.AtomicMoveNotSupportedException unsupported) {
            Files.move(pending.toPath(), probe.toPath(),
                    StandardCopyOption.REPLACE_EXISTING);
        }
        return probe;
    }

    /**
     * Trust only the fixed ASCII numeric status fields emitted by OUR probe.
     * Do not display raw Wine process lists, URLs, IPs or arbitrary log data.
     * The report records observed guest conditions, not login success.
     */
    public static String inspectGuestNetworkProbe(File root) {
        try {
            File drive = wineDrive(root);
            File report = new File(drive,
                    "CharoitePortal/Diagnostics/charoite_bnet_network_report.txt");
            if (!report.isFile() || report.length() > 4096)
                return "WINE GUEST PROBE: No valid result yet. Run the probe " +
                        "inside this Battle.net environment, return to Portal, then recheck.";
            String raw = new String(Files.readAllBytes(report.toPath()),
                    java.nio.charset.StandardCharsets.US_ASCII);
            StringBuilder result = new StringBuilder("WINE GUEST NETWORK + AGENT TEST\n");
            result.append("Report timestamp: ")
                    .append(new java.util.Date(report.lastModified())).append("\n");
            for (String line : raw.split("\\r?\\n")) {
                if (line.matches("[a-z_0-9]{3,60}=[0-9]{1,12}"))
                    result.append("  ").append(line).append("\n");
            }
            result.append("HTTP phase 7 means the guest received an HTTP response. " +
                    "Even 403/404 proves HTTPS connectivity; it does not prove " +
                    "Blizzard authentication or Agent IPC. Agent process count " +
                    "reflects only the instant the guest probe ran. " +
                    "Win32 errors identify Wine networking failures.");
            return result.toString();
        } catch (Exception error) {
            return "WINE GUEST PROBE unavailable: " +
                    error.getClass().getSimpleName();
        }
    }

    /**
     * Report data collected from the SAME Wine session as Battle.net.
     * This is distinct from the standalone network probe, which showed zero
     * processes simply because it was launched as a separate Wine activity.
     * Accept fixed, local numeric fields only; never copy raw process lists.
     */
    public static String inspectInSessionAgentMonitor(File root) {
        try {
            File drive = wineDrive(root);
            File report = new File(drive,
                    "CharoitePortal/Diagnostics/charoite_bnet_launch_monitor.txt");
            if (!report.isFile() || report.length() > 8192)
                return "BATTLE.NET LIVE AGENT MONITOR\nNo live-session record yet. " +
                        "Open Battle.net, leave its window open briefly, " +
                        "then return to Portal diagnostics.\n";
            String data = new String(Files.readAllBytes(report.toPath()),
                    java.nio.charset.StandardCharsets.US_ASCII);
            StringBuilder out = new StringBuilder("BATTLE.NET LIVE AGENT MONITOR\n");
            out.append("Sample timestamp: ")
                    .append(new java.util.Date(report.lastModified())).append("\n");
            for (String line : data.split("\\r?\\n")) {
                if (!line.matches("monitor_[a-z_0-9]{3,55}=[0-9]{1,12}"))
                    continue;
                if (line.startsWith("monitor_sample_")) continue;
                out.append("  ").append(line).append("\n");
            }
            long age = System.currentTimeMillis() - report.lastModified();
            if (age > 60 * 60 * 1000L)
                out.append("This monitor record is older than one hour.\n");
            if (data.contains("monitor_complete=1")) {
                out.append("Monitoring completed during one active Wine session. " +
                        "If the Agent appeared in no samples while the launcher did, " +
                        "focus on Agent startup and IPC instead of general HTTPS.\n");
            } else out.append("Monitor incomplete (launcher closed or session interrupted).\n");
            out.append("These counts cannot establish why a process exits or " +
                    "whether Blizzard login completed.\n");
            return out.toString();
        } catch (Exception error) {
            return "BATTLE.NET LIVE AGENT MONITOR unavailable: " +
                    error.getClass().getSimpleName();
        }
    }

    /**
     * Read-only browser/CEF state summary, with no Blizzard session tokens,
     * usernames, saved passwords, log contents, or account files included.
     * A spinner can be due to CEF rendering, Wine compatibility or networking.
     * We deliberately do NOT delete the Battle.net cache or reset Agent.
     */
    public static String inspectLauncherStartup(File root) {
        File drive;
        try { drive = wineDrive(root); }
        catch (Exception error) { return "Battle.net startup: " + error.getMessage(); }
        StringBuilder out = new StringBuilder("BATTLE.NET BROWSER STARTUP\n");
        File launcher = installedLauncher(root);
        out.append("Installed launcher: ")
                .append(launcher == null ? "not found" : launcher.getName()).append("\n");
        out.append("Blizzard safe-browser --disable-gpu option: available\n");
        out.append("Existing prefix/Agent are not modified by Safe Browser.\n");
        out.append("Local browser and Agent directory presence (not contents):\n");
        for (String relative : new String[]{
                "ProgramData/Battle.net",
                "ProgramData/Blizzard Entertainment",
                "Program Files (x86)/Battle.net",
                "Program Files/Battle.net"}) {
            File folder = new File(drive, relative);
            out.append("  ").append(relative).append(": ")
                    .append(folder.isDirectory() ? "present" : "absent").append("\n");
        }
        File users = new File(drive, "users");
        File[] profiles = users.listFiles();
        int userProfiles = 0, appDataDirs = 0, crashFolders = 0;
        if (profiles != null) for (File profile : profiles) {
            if (!profile.isDirectory() ||
                    java.nio.file.Files.isSymbolicLink(profile.toPath()))
                continue;
            userProfiles++;
            if (new File(profile, "AppData/Roaming/Battle.net").isDirectory())
                appDataDirs++;
            if (new File(profile,
                    "AppData/Local/Blizzard Entertainment").isDirectory())
                crashFolders++;
        }
        out.append("Wine user profile folders: ").append(userProfiles).append("\n");
        out.append("Roaming Battle.net data folders: ").append(appDataDirs).append("\n");
        out.append("Local Blizzard data folders: ").append(crashFolders).append("\n");
        out.append("A spinning icon is not proof of a broken installation. " +
                "Hardware-accelerated CEF, Wine runner version and Blizzard network " +
                "access can each cause it. This report does not read or delete data.");
        return out.toString();
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
