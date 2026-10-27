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
     * Status of the Charoite-owned in-session observer. This small local
     * state record exists even if WinHandler never starts the guest probe.
     * No Blizzard files, process logs or personal data are read or modified.
     */
    public static void noteLiveAgentMonitorState(File root, String state) {
        if (!state.matches("ARMED|WAITING_FOR_WINE|WINE_BRIDGE_TIMEOUT|" +
                "COMMAND_SENT|PREPARE_FAILED")) return;
        try {
            File drive = wineDrive(root);
            File folder = new File(drive, "CharoitePortal/Diagnostics");
            if (!folder.isDirectory() && !folder.mkdirs()) return;
            File status = new File(folder, "charoite_bnet_monitor_state.txt");
            String message = "monitor_android_state=" + state + "\n" +
                    "monitor_android_state_epoch_ms=" +
                    System.currentTimeMillis() + "\n";
            Files.write(status.toPath(),
                    message.getBytes(java.nio.charset.StandardCharsets.US_ASCII));
        } catch (IOException ignored) {
            // Monitoring is diagnostic only; never block a Battle.net launch.
        }
    }

    private static String describeLiveAgentMonitorState(File drive) {
        File status = new File(drive,
                "CharoitePortal/Diagnostics/charoite_bnet_monitor_state.txt");
        if (!status.isFile() || status.length() > 256) {
            return "Android monitor launcher state: never recorded. " +
                    "The installed app may predate live monitoring, or " +
                    "Battle.net has not been opened since this APK update.\n";
        }
        try {
            String data = new String(Files.readAllBytes(status.toPath()),
                    java.nio.charset.StandardCharsets.US_ASCII);
            java.util.regex.Matcher code = java.util.regex.Pattern.compile(
                    "monitor_android_state=(ARMED|WAITING_FOR_WINE|" +
                    "WINE_BRIDGE_TIMEOUT|COMMAND_SENT|PREPARE_FAILED)")
                    .matcher(data);
            if (!code.find()) return "Android monitor launcher state: invalid.\n";
            String state = code.group(1);
            return "Android monitor launcher state: " + state + "\n" +
                    "  Status timestamp: " +
                    new java.util.Date(status.lastModified()) + "\n" +
                    (state.equals("WINE_BRIDGE_TIMEOUT") ?
                    "  Wine's keyboard/command bridge was not ready in " +
                    "time; no process monitor could be started.\n" :
                    state.equals("PREPARE_FAILED") ?
                    "  Charoite could not prepare its own read-only probe.\n" :
                    state.equals("COMMAND_SENT") ?
                    "  Charoite requested the monitor process; Wine execution " +
                    "is not confirmed until a report file exists.\n" :
                    "  Waiting for the Wine-side command bridge.\n");
        } catch (IOException error) {
            return "Android monitor launcher state: unreadable.\n";
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
            String androidState = describeLiveAgentMonitorState(drive);
            if (!report.isFile() || report.length() > 8192)
                return "BATTLE.NET LIVE AGENT MONITOR\n" + androidState +
                        "No Wine-side monitor samples received yet. Open the " +
                        "installed Battle.net client, leave its window open " +
                        "briefly, then return to this dedicated monitor view.\n";
            String data = new String(Files.readAllBytes(report.toPath()),
                    java.nio.charset.StandardCharsets.US_ASCII);
            StringBuilder out = new StringBuilder("BATTLE.NET LIVE AGENT MONITOR\n");
            out.append(androidState);
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

    /**
     * Browser preferences are not the same thing as a command-line GPU flag:
     * Battle.net.exe may be re-launched by its bootstrapper and not inherit
     * all Chrome switches. Inspect effective persisted settings read-only.
     * Never print profile names, configuration contents, auth tokens or IDs.
     */
    public static String inspectBrowserPreferences(File root) {
        final File drive;
        try { drive = wineDrive(root); }
        catch (IOException error) { return "BROWSER SETTINGS: Wine drive unavailable.\n"; }
        int files=0, disabled=0, enabled=0, missing=0, invalid=0;
        int streamingOff=0, streamingOn=0;
        File users = new File(drive, "users");
        File[] profiles = users.listFiles();
        java.util.HashSet<String> visited = new java.util.HashSet<>();
        if (profiles != null) for (File profile : profiles) {
            if (files >= 8) break;
            if (!profile.isDirectory() || Files.isSymbolicLink(profile.toPath())) continue;
            for (String location : new String[]{
                    "AppData/Roaming/Battle.net/Battle.net.config",
                    "Application Data/Battle.net/Battle.net.config"}) {
                File candidate = new File(profile, location);
                if (!candidate.isFile() || candidate.length() > 262144 ||
                        Files.isSymbolicLink(candidate.toPath())) continue;
                try {
                    File cfg=candidate.getCanonicalFile();
                    if (!cfg.getPath().startsWith(drive.getPath()+File.separator) ||
                            !visited.add(cfg.getPath())) continue;
                    files++;
                    org.json.JSONObject json=new org.json.JSONObject(
                            new String(Files.readAllBytes(cfg.toPath()),
                                    java.nio.charset.StandardCharsets.UTF_8));
                    org.json.JSONObject client=json.optJSONObject("Client");
                    if (client == null || !client.has("HardwareAcceleration")) missing++;
                    else {
                        String value=client.optString("HardwareAcceleration","").toLowerCase(Locale.ROOT);
                        if ("false".equals(value)) disabled++;
                        else if ("true".equals(value)) enabled++;
                        else invalid++;
                    }
                    if (client != null) {
                        org.json.JSONObject streaming=client.optJSONObject("Streaming");
                        if (streaming != null && streaming.has("StreamingEnabled")) {
                            if ("false".equalsIgnoreCase(
                                    streaming.optString("StreamingEnabled"))) streamingOff++;
                            else if ("true".equalsIgnoreCase(
                                    streaming.optString("StreamingEnabled"))) streamingOn++;
                        }
                    }
                } catch (Exception unreadable) { invalid++; }
                if (files>=8) break;
            }
        }
        return "BATTLE.NET PERSISTED BROWSER SETTINGS\n" +
                "  Configuration files examined: " + files + "\n" +
                "  Browser hardware acceleration OFF: " + disabled + "\n" +
                "  Browser hardware acceleration ON: " + enabled + "\n" +
                "  Browser hardware acceleration unspecified: " + missing + "\n" +
                "  Invalid/unreadable setting files: " + invalid + "\n" +
                "  Streaming disabled: " + streamingOff + "\n" +
                "  Streaming enabled: " + streamingOn + "\n" +
                "Command-line --disable-gpu is separate from this saved browser " +
                "setting. No preferences were changed during inspection.\n";
    }

    /**
     * Bound inspection to Blizzard's local client logs and report only error
     * CATEGORIES, never raw lines, URLs, sessions, usernames or log paths.
     * The absence of a category is not proof that CEF rendering is healthy.
     */
    public static String inspectBrowserLogCategories(File root) {
        final File drive;
        try { drive = wineDrive(root); }
        catch (IOException error) { return "BATTLE.NET CLIENT LOGS: Wine drive unavailable.\n"; }
        java.util.ArrayList<File> logs=new java.util.ArrayList<>();
        File users=new File(drive,"users");
        File[] profiles=users.listFiles();
        if (profiles!=null) for (File profile:profiles) {
            if(!profile.isDirectory() || Files.isSymbolicLink(profile.toPath())) continue;
            for(String relative:new String[]{
                    "AppData/Local/Battle.net/Logs",
                    "AppData/Roaming/Battle.net/Logs",
                    "AppData/Local/Blizzard Entertainment/Battle.net/Logs"}) {
                File dir=new File(profile,relative);
                if(!dir.isDirectory() || Files.isSymbolicLink(dir.toPath())) continue;
                File[] entries=dir.listFiles();
                if(entries==null) continue;
                for(File entry:entries) {
                    if(logs.size()>=100) break;
                    if(!entry.isFile() || Files.isSymbolicLink(entry.toPath()) ||
                            entry.length()==0) continue;
                    String name=entry.getName().toLowerCase(Locale.ROOT);
                    if(name.endsWith(".log") || name.endsWith(".txt"))
                        logs.add(entry);
                }
            }
        }
        logs.sort((x,y)->Long.compare(y.lastModified(),x.lastModified()));
        int sampled=0, errors=0, cef=0, rendering=0, ipc=0, network=0;
        int crash=0, gpu=0, login=0;
        for(int i=0;i<Math.min(logs.size(),6);i++) {
            File file=logs.get(i);
            try(java.io.RandomAccessFile input=new java.io.RandomAccessFile(file,"r")) {
                long begin=Math.max(0,input.length()-32768);
                input.seek(begin);
                byte[] bytes=new byte[(int)(input.length()-begin)];
                input.readFully(bytes);
                String sample=new String(bytes,
                        java.nio.charset.StandardCharsets.UTF_8).toLowerCase(Locale.ROOT);
                sampled++;
                for(String line:sample.split("\\r?\\n")) {
                    if(!(line.contains("error") || line.contains("fail") ||
                            line.contains("exception") || line.contains("crash") ||
                            line.contains("fatal") || line.contains("assert")))
                        continue;
                    errors++;
                    if(line.contains("cef") || line.contains("chromium") ||
                            line.contains("tassadar") || line.contains("browser")) cef++;
                    if(line.contains("render") || line.contains("d3d") ||
                            line.contains("opengl") || line.contains("vulkan")) rendering++;
                    if(line.contains("ipc") || line.contains("pipe") ||
                            line.contains("socket") || line.contains("agent")) ipc++;
                    if(line.contains("timeout") || line.contains("dns") ||
                            line.contains("connect") || line.contains("network")) network++;
                    if(line.contains("crash") || line.contains("exception") ||
                            line.contains("access violation")) crash++;
                    if(line.contains("gpu") || line.contains("compositor")) gpu++;
                    if(line.contains("login") || line.contains("auth")) login++;
                }
            } catch(IOException ignored) {}
        }
        return "BATTLE.NET CLIENT ERROR CATEGORIES\n" +
                "  Recent client log files sampled: " + sampled + "\n" +
                "  Error-like entries: " + errors + "\n" +
                "  Browser/CEF references: " + cef + "\n" +
                "  Rendering references: " + rendering + "\n" +
                "  GPU/compositor references: " + gpu + "\n" +
                "  Agent/IPC references: " + ipc + "\n" +
                "  Network references: " + network + "\n" +
                "  Crash/exception references: " + crash + "\n" +
                "  Login/authentication references: " + login + "\n" +
                "This is a read-only categorization, not a diagnosis or a " +
                "copy of raw Blizzard logs.\n";
    }


    /**
     * Classify the newest Battle.net UI logs. Do not reveal raw lines, URLs,
     * usernames, tokens, login details, or file paths. This is read-only.
     * Agent process presence does not prove CEF loaded the login page.
     */
    public static String inspectBrowserClientLogs(File root) {
        final File drive;
        try { drive = wineDrive(root); }
        catch (Exception e) { return "BATTLE.NET UI LOG CHECK unavailable.\\n"; }
        java.util.ArrayList<File> files = new java.util.ArrayList<>();
        File[] profiles = new File(drive, "users").listFiles();
        if (profiles != null) for (File profile : profiles) {
            if (!profile.isDirectory() ||
                    java.nio.file.Files.isSymbolicLink(profile.toPath())) continue;
            File logFolder = new File(profile, "AppData/Local/Battle.net/Logs");
            File[] logs = logFolder.listFiles();
            if (logs == null) continue;
            for (File log : logs)
                if (log.isFile() && !java.nio.file.Files.isSymbolicLink(log.toPath())
                        && (log.getName().endsWith(".log") ||
                            log.getName().endsWith(".txt")))
                    files.add(log);
        }
        files.sort((a,b) -> Long.compare(b.lastModified(), a.lastModified()));
        int samples = Math.min(6,files.size());
        int login=0, cef=0, agent=0, network=0, errors=0;
        for (int i=0;i<samples;i++) {
            try (java.io.RandomAccessFile in =
                    new java.io.RandomAccessFile(files.get(i),"r")) {
                long pos = Math.max(0,in.length() - 48*1024);
                in.seek(pos);
                byte[] bytes = new byte[(int)(in.length()-pos)];
                in.readFully(bytes);
                String data = new String(bytes,
                        java.nio.charset.StandardCharsets.UTF_8)
                        .toLowerCase(Locale.ROOT);
                for (String line : data.split("\\r?\\n")) {
                    if (line.length()>4096) continue;
                    boolean relevant = line.contains("error") ||
                            line.contains("fail") || line.contains("exception") ||
                            line.contains("unable") || line.contains("empty") ||
                            line.contains("crash") || line.contains("timeout");
                    if (!relevant) continue;
                    errors++;
                    if (line.contains("tassadar") || line.contains("bnlogin") ||
                            line.contains("login url") || line.contains("loginurl"))
                        login++;
                    if (line.contains("cef") || line.contains("chromium") ||
                            line.contains("gpu process") || line.contains("browser"))
                        cef++;
                    if (line.contains("agent") || line.contains("ipc") ||
                            line.contains("localhost") || line.contains("127.0.0.1") ||
                            line.contains("1120"))
                        agent++;
                    if (line.contains("http") || line.contains("connection") ||
                            line.contains("network") || line.contains("timeout") ||
                            line.contains("certificate"))
                        network++;
                }
            } catch (IOException ignored) {}
        }
        StringBuilder result=new StringBuilder("BATTLE.NET UI / LOGIN LOG CHECK\\n");
        result.append("Recent client logs examined: ").append(samples).append("\\n");
        if (samples > 0) result.append("Latest client log timestamp: ")
                .append(new java.util.Date(files.get(0).lastModified())).append("\\n");
        result.append("Error-like entries: ").append(errors).append("\\n");
        result.append("  Login/Tassadar references: ").append(login).append("\\n");
        result.append("  CEF/browser/GPU references: ").append(cef).append("\\n");
        result.append("  Agent/IPC references: ").append(agent).append("\\n");
        result.append("  Network/TLS references: ").append(network).append("\\n");
        result.append("Counts are not diagnoses; zero means no matches in the sampled " +
                "log tails. No client logs or personal data were modified.\\n");
        return result.toString();
    }

    /**
     * Local-app browser cache repair: an OPT-IN reversible rename, not deletion.
     * Never move ProgramData/Battle.net, Agent, settings, CachedData.db, or games.
     * The user must close Blizzard before pressing the confirmation button.
     */
    public static String backupAndResetBrowserCache(File root) throws IOException {
        File drive=wineDrive(root);
        File[] profiles=new File(drive,"users").listFiles();
        if (profiles==null) return "No Wine users available; no changes made.";
        int moved=0,missing=0,skipped=0;
        String suffix=".charoite-backup-"+System.currentTimeMillis();
        for (File profile:profiles) {
            if (!profile.isDirectory() ||
                    Files.isSymbolicLink(profile.toPath())) continue;
            File parent=new File(profile,"AppData/Local/Battle.net").getCanonicalFile();
            if (!parent.getPath().startsWith(drive.getPath()+File.separator))
                continue;
            for (String cacheName:new String[]{"Cache","BrowserCaches","GPUCache","Code Cache"}) {
                File original=new File(parent,cacheName);
                if (!original.exists()) { missing++; continue; }
                if (!original.isDirectory() ||
                        Files.isSymbolicLink(original.toPath())) { skipped++; continue; }
                File backup=new File(parent,cacheName+suffix);
                if (backup.exists()) { skipped++; continue; }
                // Rename on the SAME C: filesystem; never overwrite or delete.
                try {
                    Files.move(original.toPath(),backup.toPath(),
                            StandardCopyOption.ATOMIC_MOVE);
                } catch (java.nio.file.AtomicMoveNotSupportedException ex) {
                    Files.move(original.toPath(),backup.toPath());
                }
                moved++;
            }
        }
        return "Battle.net browser caches backed up (not deleted): "+moved+
                " folder(s) moved; "+missing+" missing; "+skipped+
                " skipped for safety. Original folders remain as " +
                "Cache/BrowserCaches/GPUCache/Code Cache.charoite-backup-<timestamp>. " +
                "Other Blizzard settings, Agent, games and saves were untouched. " +
                "Battle.net may recreate caches at next startup.";
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
