package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.app.job.JobInfo;
import android.app.job.JobParameters;
import android.app.job.JobScheduler;
import android.app.job.JobService;
import android.content.ComponentName;
import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.security.keystore.KeyGenParameterSpec;
import android.security.keystore.KeyProperties;
import android.text.InputType;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.ByteArrayOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.security.KeyStore;
import java.security.MessageDigest;
import java.security.SecureRandom;
import java.util.Base64;
import java.util.Locale;
import java.util.concurrent.atomic.AtomicBoolean;
import javax.crypto.Cipher;
import javax.crypto.KeyGenerator;
import javax.crypto.SecretKey;
import javax.crypto.spec.GCMParameterSpec;
import org.json.JSONObject;

/**
 * Opt-in reporter targeting the PUBLIC CharoitePortal issue tracker.
 * Read-only for precisely two existing v9 logs. Only allowlisted booleans
 * and counts leave the device, NEVER raw logs, paths, prefix, or credentials.
 * Does not execute Wine, create a scratch directory or clear previous evidence.
 */
public final class CharoiteNextAutoReports {
    private static final String PACKAGE = "com.charoitx";
    private static final String PREFERENCES = "charoite-next-auto-reports-v1";
    private static final String ENABLED = "enabled";
    private static final String TOKEN = "encrypted_github_issue_token";
    private static final String LAST_ACK = "last_acknowledged_report_id";
    private static final String LAST_STATUS = "last_result_status";
    private static final String ALIAS = "charoite-next-github-issues-v1";
    private static final String GITHUB_ISSUES =
            "https://api.github.com/repos/rgarn023/CharoitePortal/issues";
    private static final String V9 =
            "charoite-next-wine28-pe-help-v9-builtin-boot";
    private static final int JOB_ID = 280054;
    private static final long PERIOD_MS = 15L * 60L * 1000L;
    private static final AtomicBoolean SENDING = new AtomicBoolean(false);
    private CharoiteNextAutoReports() {}

    private static SharedPreferences prefs(Context ctx) {
        return ctx.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE);
    }
    public static boolean enabled(Context ctx) {
        return PACKAGE.equals(ctx.getPackageName())
                && prefs(ctx).getBoolean(ENABLED, false)
                && prefs(ctx).contains(TOKEN);
    }

    private static String readExisting(File base, String name, int max) throws Exception {
        File file = new File(base, name);
        if (!base.getCanonicalFile().equals(base.getAbsoluteFile())
                || !file.getCanonicalFile().equals(file.getAbsoluteFile())
                || !file.getCanonicalFile().getParentFile().equals(base.getCanonicalFile())
                || !file.isFile() || file.length() < 1 || file.length() > max)
            throw new SecurityException("No valid bounded v9 log");
        ByteArrayOutputStream out = new ByteArrayOutputStream((int) file.length());
        try (FileInputStream in = new FileInputStream(file)) {
            byte[] buf = new byte[4096];
            int count;
            while ((count = in.read(buf)) != -1) {
                if (out.size() + count > max)
                    throw new SecurityException("Log grew beyond cap");
                out.write(buf, 0, count);
            }
        }
        return new String(out.toByteArray(), StandardCharsets.UTF_8);
    }
    private static boolean has(String log, String term) {
        return log.toLowerCase(Locale.US).contains(term.toLowerCase(Locale.US));
    }
    private static int count(String log, String term) {
        int n = 0, at = 0;
        while ((at = log.indexOf(term, at)) >= 0) { n++; at += term.length(); }
        return n;
    }

    /** No arbitrary values or raw lines from the phone logs enter the payload. */
    public static JSONObject sanitizedReport(Context ctx) throws Exception {
        if (!PACKAGE.equals(ctx.getPackageName()))
            throw new SecurityException("Not Charoite Next");
        File base = new File(ctx.getNoBackupFilesDir(), V9);
        if (!base.isDirectory() || !base.getCanonicalFile().equals(base.getAbsoluteFile()))
            throw new SecurityException("Preserved v9 directory unavailable");
        String pe = readExisting(base, "v9-wine-pe-help.log", 2 * 1024 * 1024);
        String server = readExisting(base, "v9-foreground-wineserver.log", 256 * 1024);
        JSONObject j = new JSONObject();
        j.put("schema", "charoite-next.phone-diagnostics.v1");
        j.put("package", PACKAGE);
        j.put("generation", "wine28-v9-readonly");
        j.put("read_only", true);
        j.put("collector_executed_wine", false);
        j.put("pe_bytes", pe.getBytes(StandardCharsets.UTF_8).length);
        j.put("server_bytes", server.getBytes(StandardCharsets.UTF_8).length);
        j.put("server_new_process_calls", count(server, "new_process( "));
        j.put("server_new_process_success", has(server, "new_process() = 0 {"));
        j.put("internal_child_failed", has(server,
                "get_new_process_info() = 0 { success=0, exit_code=1 }"));
        j.put("pe_kernel32_missing", has(pe,
                "could not load kernel32.dll, status c0000135"));
        j.put("pe_apiset_failed", has(pe,
                "load_apiset_dll failed to load apiset: c000000f"));
        j.put("server_no_such_file", count(server, " = NO_SUCH_FILE"));
        j.put("internal_wineboot_init", has(server, "wineboot.exe") && has(server, "--init"));
        j.put("prefix_read", false);
        j.put("games_or_saves_read", false);
        return j;
    }

    private static String id(String json) throws Exception {
        byte[] bytes = MessageDigest.getInstance("SHA-256")
                .digest(json.getBytes(StandardCharsets.UTF_8));
        StringBuilder b = new StringBuilder();
        for (int i = 0; i < 12; i++)
            b.append(String.format(Locale.US, "%02x", bytes[i] & 255));
        return b.toString();
    }
    public static String preview(Context ctx) {
        try { return sanitizedReport(ctx).toString(2); }
        catch (Exception ex) {
            return "Not uploadable: " + ex.getClass().getSimpleName()
                    + " (no data changed)";
        }
    }
    public static String status(Context ctx) {
        return (enabled(ctx) ? "Enabled" : "Disabled")
                + "\nDestination: PUBLIC github.com/rgarn023/CharoitePortal/issues"
                + "\nUploads: limited v9 diagnostic indicators only; no raw traces."
                + "\nLast result: " + prefs(ctx).getString(LAST_STATUS, "not sent")
                + "\nNever runs or reruns Wine.";
    }

    private static SecretKey key() throws Exception {
        KeyStore store = KeyStore.getInstance("AndroidKeyStore");
        store.load(null);
        KeyStore.Entry old = store.getEntry(ALIAS, null);
        if (old instanceof KeyStore.SecretKeyEntry)
            return ((KeyStore.SecretKeyEntry) old).getSecretKey();
        KeyGenerator gen = KeyGenerator.getInstance("AES", "AndroidKeyStore");
        gen.init(new KeyGenParameterSpec.Builder(ALIAS,
                KeyProperties.PURPOSE_ENCRYPT | KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true).build());
        return gen.generateKey();
    }
    private static String protect(String plain) throws Exception {
        byte[] iv = new byte[12];
        new SecureRandom().nextBytes(iv);
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.ENCRYPT_MODE, key(), new GCMParameterSpec(128, iv));
        return Base64.getEncoder().encodeToString(iv) + ":"
                + Base64.getEncoder().encodeToString(
                        c.doFinal(plain.getBytes(StandardCharsets.UTF_8)));
    }
    private static String unprotect(String saved) throws Exception {
        String[] pieces = saved.split(":", -1);
        if (pieces.length != 2) throw new SecurityException("Invalid token envelope");
        byte[] iv = Base64.getDecoder().decode(pieces[0]);
        if (iv.length != 12) throw new SecurityException("Invalid token IV");
        Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
        c.init(Cipher.DECRYPT_MODE, key(), new GCMParameterSpec(128, iv));
        return new String(c.doFinal(Base64.getDecoder().decode(pieces[1])),
                StandardCharsets.UTF_8);
    }

    /** Every reason here is safe to display: no part of the secret is echoed. */
    private static final class TokenInputException extends Exception {
        TokenInputException(String explanation) { super(explanation); }
    }

    private static String normalizeFineGrainedToken(String input) throws TokenInputException {
        if (input == null || input.trim().isEmpty())
            throw new TokenInputException(
                    "Paste the actual GitHub fine-grained personal access token, not its name.");
        String value = input.trim();
        // Password managers sometimes copy the Authorization header or a
        // quoted secret. Accept only these harmless wrappers, not arbitrary URLs.
        if (value.regionMatches(true, 0, "Bearer ", 0, 7))
            value = value.substring(7).trim();
        if (value.length() >= 2 && value.startsWith("\"")
                && value.endsWith("\""))
            value = value.substring(1, value.length() - 1).trim();
        if (value.startsWith("ghp_"))
            throw new TokenInputException(
                    "This is a classic token (ghp_). Create a fine-grained token with Issues: read/write.");
        if (value.startsWith("http://") || value.startsWith("https://"))
            throw new TokenInputException(
                    "You pasted a web address. GitHub shows the token value once when it is generated.");
        if (!value.startsWith("github_pat_"))
            throw new TokenInputException(
                    "Expected a fine-grained token starting github_pat_. Use the value copied when GitHub created it.");
        // Format checks deliberately do not guess GitHub's exact token length.
        // GitHub's API, not this app, verifies authenticity and permissions.
        if (!value.matches("github_pat_[A-Za-z0-9_]{10,256}"))
            throw new TokenInputException(
                    "The fine-grained token looks incomplete or contains invalid characters. Copy its entire value.");
        return value;
    }

    private static void configure(Context ctx, String githubToken) throws Exception {
        String cleaned = normalizeFineGrainedToken(githubToken);
        sanitizedReport(ctx);
        String encrypted = protect(cleaned);
        if (!prefs(ctx).edit().putString(TOKEN, encrypted)
                .putBoolean(ENABLED, true).commit())
            throw new IllegalStateException("Protected preferences unavailable");
        schedule(ctx);
    }
    public static void disable(Context ctx) {
        prefs(ctx).edit().putBoolean(ENABLED, false).remove(TOKEN).commit();
        JobScheduler s = (JobScheduler) ctx.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (s != null) s.cancel(JOB_ID);
    }

    /** JobScheduler is allowed only after explicit opt-in; no repeat Wine probes. */
    public static void schedule(Context ctx) {
        if (!enabled(ctx)) return;
        JobScheduler s = (JobScheduler) ctx.getSystemService(Context.JOB_SCHEDULER_SERVICE);
        if (s != null) {
            JobInfo job = new JobInfo.Builder(JOB_ID,
                    new ComponentName(ctx, UploadJob.class))
                    .setRequiredNetworkType(JobInfo.NETWORK_TYPE_ANY)
                    .setPeriodic(PERIOD_MS).setPersisted(false).build();
            s.schedule(job);
        }
    }

    private static String record(SharedPreferences p, String message) {
        p.edit().putString(LAST_STATUS, message).apply();
        return message;
    }
    /** Post one deduplicated public GitHub issue; never read the response body. */
    public static String send(Context ctx) {
        if (!enabled(ctx)) return "Disabled; nothing transmitted";
        if (!SENDING.compareAndSet(false, true)) return "Another send is active";
        try {
            JSONObject safe = sanitizedReport(ctx);
            String report = safe.toString();
            String reportId = id(report);
            SharedPreferences p = prefs(ctx);
            if (reportId.equals(p.getString(LAST_ACK, "")))
                return "Already uploaded " + reportId;
            URL url = new URL(GITHUB_ISSUES);
            if (!"https".equals(url.getProtocol())
                    || !"api.github.com".equals(url.getHost()))
                throw new SecurityException("Untrusted destination");
            HttpURLConnection c = (HttpURLConnection) url.openConnection();
            try {
                c.setConnectTimeout(12000);
                c.setReadTimeout(12000);
                c.setInstanceFollowRedirects(false);
                c.setRequestMethod("POST");
                c.setDoOutput(true);
                c.setRequestProperty("Authorization", "Bearer "
                        + unprotect(p.getString(TOKEN, "")));
                c.setRequestProperty("Accept", "application/vnd.github+json");
                c.setRequestProperty("X-GitHub-Api-Version", "2022-11-28");
                c.setRequestProperty("Content-Type", "application/json; charset=utf-8");
                JSONObject issue = new JSONObject();
                issue.put("title", "[device-report] Wine28 v9 " + reportId);
                issue.put("body", "Automated Charoite Next phone diagnosis. Sanitized JSON only.\n\n"
                        + report + "\n\nReport ID " + reportId
                        + ". Wine v9 was not executed or retried.");
                byte[] bytes = issue.toString().getBytes(StandardCharsets.UTF_8);
                if (bytes.length > 8192) throw new SecurityException("Payload cap exceeded");
                c.setFixedLengthStreamingMode(bytes.length);
                try (OutputStream out = c.getOutputStream()) { out.write(bytes); }
                int status = c.getResponseCode();
                if (status != 201)
                    return record(p, "GitHub HTTP " + status + "; not acknowledged");
                p.edit().putString(LAST_ACK, reportId)
                        .putString(LAST_STATUS, "Uploaded " + reportId).apply();
                return "Uploaded " + reportId;
            } finally { c.disconnect(); }
        } catch (Exception ex) {
            // An error message might reveal URLs or credentials: omit it.
            return record(prefs(ctx), "Error: " + ex.getClass().getSimpleName());
        } finally { SENDING.set(false); }
    }

    public static class UploadJob extends JobService {
        @Override public boolean onStartJob(JobParameters params) {
            if (!enabled(this)) return false;
            new Thread(() -> {
                send(getApplicationContext());
                jobFinished(params, false);
            }, "CharoiteOptInDiagnosticUpload").start();
            return true;
        }
        @Override public boolean onStopJob(JobParameters params) { return true; }
    }

    public static void showSettings(Activity activity) {
        LinearLayout panel = new LinearLayout(activity);
        panel.setOrientation(LinearLayout.VERTICAL);
        int pad = (int) (16 * activity.getResources().getDisplayMetrics().density);
        panel.setPadding(pad, pad / 2, pad, pad / 2);
        TextView description = new TextView(activity);
        description.setText(status(activity) + "\n\n"
                + "One-time setup: a fine-grained GitHub token scoped ONLY to "
                + "rgarn023/CharoitePortal with Issues: read/write. The token is "
                + "encrypted with Android Keystore, never bundled in an APK. "
                + "A summary (not raw phone traces) becomes a PUBLIC issue.\n\n"
                + "GitHub displays the token VALUE only once when it is generated. "
                + "Paste that value here (it begins github_pat_), not its name or URL. "
                + "Preview first; uploads are disabled until you opt in.");
        panel.addView(description);
        EditText token = new EditText(activity);
        token.setHint("Paste GitHub token beginning github_pat_");
        token.setSingleLine(true);
        token.setInputType(InputType.TYPE_CLASS_TEXT
                | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        panel.addView(token);
        AlertDialog dialog = new AlertDialog.Builder(activity)
                .setTitle("Automated diagnostics — opt-in")
                .setView(panel)
                .setPositiveButton("Enable", null)
                .setNeutralButton("Preview", null)
                .setNegativeButton("Disable / Close", null).create();
        dialog.setOnShowListener(v -> {
            dialog.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener(x -> {
                try {
                    configure(activity, token.getText().toString());
                    token.setText("");
                    dialog.dismiss();
                    new Thread(() -> send(activity.getApplicationContext()),
                            "CharoiteFirstReport").start();
                } catch (TokenInputException ex) {
                    // Only our static user-guidance strings are displayed.
                    description.setText("Not enabled: " + ex.getMessage()
                            + "\\n\\nThe repository stays public. No report was sent.");
                    token.setError(ex.getMessage());
                } catch (Exception ex) {
                    description.setText("Not enabled: could not read the preserved v9 "
                            + "report or securely save the token. Open Preview first. "
                            + "Technical type: " + ex.getClass().getSimpleName()
                            + ". No report was sent.");
                    token.setError("Reporting is not enabled.");
                }
            });
            dialog.getButton(AlertDialog.BUTTON_NEUTRAL).setOnClickListener(x ->
                    new AlertDialog.Builder(activity)
                            .setTitle("Exact public report contents")
                            .setMessage(preview(activity))
                            .setPositiveButton("Close", null).show());
            dialog.getButton(AlertDialog.BUTTON_NEGATIVE).setOnClickListener(x -> {
                if (enabled(activity)) disable(activity);
                dialog.dismiss();
            });
        });
        dialog.show();
    }
}
