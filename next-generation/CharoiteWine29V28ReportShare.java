package com.charoitegames.core;

import android.app.Activity;
import android.app.AlertDialog;
import android.content.Intent;
import android.net.Uri;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Locale;
import org.json.JSONObject;

/**
 * V28 report transport ONLY. Does not open prefixes, files, logs or start Wine.
 * Constructs strict fixed-marker JSON from the ALREADY RETURNED in-memory
 * short report, then opens a PUBLIC GitHub issue draft in the browser.
 * The owner must review and submit the issue manually; no token or upload API.
 */
public final class CharoiteWine29V28ReportShare {
    private static final String PREFIX = "[device-report] Wine29 V28 ";
    private static final String HEADER =
            "Handoff: https://github.com/rgarn023/CharoitePortal/blob/main/docs/CURRENT_HANDOFF.md\n"
            + "CHAROITE NEXT — ISOLATED WINE29 V28 ";
    private static final String END = "END OF SHORT V28 PREFIX SETUP SCM REPORT";
    private static final String ISSUE_URL =
            "https://github.com/rgarn023/CharoitePortal/issues/new";
    private static final String[][] MARKERS = {
        {"wineboot_finished", "Direct -i PE process completed within 45s: "},
        {"internal_defaultinstall_seen", "V28 internal DefaultInstall command marker observed: "},
        {"helper_attempted", "V28 independent DefaultInstall helper attempted: "},
        {"helper_finished", "V28 independent DefaultInstall helper completed within 35s: "},
        {"helper_log_cap", "V28 independent DefaultInstall helper log cap exceeded: "},
        {"helper_timeout", "V28 independent DefaultInstall helper timeout: "},
        {"inf_open_failure", "V28 helper trace INF open failure marker: "},
        {"setupapi_error", "V28 helper trace SetupAPI failure marker: "},
        {"arm64_section_seen", "V28 helper trace ARM64 DefaultInstall selection mention: "},
        {"rpcss_creation_attempt_seen", "V28 helper trace RpcSs service creation attempt mention: "},
        {"scm_query_attempted", "V28 independent sc.exe query RpcSs attempted: "},
        {"scm_error_1060", "V28 SCM error 1060 marker observed: "},
        {"scm_service_state", "V28 SCM output includes service state: "},
        {"rpcss_registry_root", "V28 POST-FINALIZATION exact RpcSs service-root section: "},
        {"rpcss_registry_imagepath", "V28 POST-FINALIZATION RpcSs ImagePath field present: "},
        {"rpcss_registry_start", "V28 POST-FINALIZATION RpcSs Start field present: "},
        {"rpcss_registry_type", "V28 POST-FINALIZATION RpcSs Type field present: "}
    };
    private CharoiteWine29V28ReportShare() {}

    private static Object fixedBoolean(String[] lines, String label) {
        for (String line : lines) {
            if (!line.startsWith(label)) continue;
            String text = line.substring(label.length()).trim();
            if ("true".equals(text) || text.startsWith("true "))
                return Boolean.TRUE;
            if ("false".equals(text) || text.startsWith("false "))
                return Boolean.FALSE;
            break;
        }
        // Missing marker is UNKNOWN, not false and not a success claim.
        return JSONObject.NULL;
    }

    private static String result(String[] lines) {
        for (String line : lines) {
            if (!line.startsWith("RESULT: ")) continue;
            for (String status : new String[]{"OBSERVED","PARTIAL","BLOCKED","FAIL"}) {
                if (line.equals("RESULT: " + status)
                        || line.startsWith("RESULT: " + status + " "))
                    return status;
            }
        }
        return "UNKNOWN";
    }

    /** NO raw device text or paths are copied into JSON; only fixed keys/values. */
    private static String safeJson(String report) throws Exception {
        if (report == null || report.length() > 9000
                || !report.startsWith(HEADER) || !report.contains(END))
            throw new SecurityException("Missing complete V28 short-report envelope");
        String[] lines = report.split("\n", -1);
        JSONObject j = new JSONObject();
        j.put("schema", "charoite-next.phone-wine29-v28.v1");
        j.put("package", "com.charoitx");
        j.put("generation", "wine29-v28");
        j.put("submission_read_only", true);
        j.put("collector_executed_wine", false);
        j.put("result", result(lines));
        for (String[] marker : MARKERS)
            j.put(marker[0], fixedBoolean(lines, marker[1]));
        String json = j.toString();
        if (json.length() > 2400)
            throw new SecurityException("Sanitized report size exceeded");
        return json;
    }

    private static String id(String json) throws Exception {
        byte[] hash = MessageDigest.getInstance("SHA-256")
                .digest(json.getBytes(StandardCharsets.UTF_8));
        StringBuilder id = new StringBuilder();
        for (int i=0; i<12; i++)
            id.append(String.format(Locale.US, "%02x", hash[i] & 255));
        return id.toString();
    }

    public static void reviewAndOpen(Activity activity, String shortReport) {
        try {
            if (!"com.charoitx".equals(activity.getPackageName()))
                throw new SecurityException("Not experimental Charoite Next");
            String json = safeJson(shortReport);
            String reportId = id(json);
            String body = "Charoite Next V28 report. Sanitized fixed markers only.\n\n"
                    + json + "\n\nReport ID " + reportId
                    + ". This issue does not authorize another Wine test.";
            if (body.getBytes(StandardCharsets.UTF_8).length > 4096)
                throw new SecurityException("Issue draft body too large");
            Uri url = Uri.parse(ISSUE_URL).buildUpon()
                    .appendQueryParameter("title", PREFIX + reportId)
                    .appendQueryParameter("body", body).build();
            if (url.toString().length() > 8000)
                throw new SecurityException("Issue draft URL too long");
            new AlertDialog.Builder(activity)
                    .setTitle("Review PUBLIC GitHub diagnostic")
                    .setMessage("Only these fixed boolean/unknown markers will be shared, "
                        + "not logs, raw paths, game data or credentials. GitHub issues "
                        + "are PUBLIC. The browser opens a PRE-FILLED DRAFT; you must "
                        + "sign in and press Submit yourself. This DOES NOT rerun Wine.\n\n"
                        + json)
                    .setNegativeButton("Cancel — keep private", null)
                    .setPositiveButton("Open GitHub issue draft", (dialog, which) -> {
                        try {
                            activity.startActivity(new Intent(Intent.ACTION_VIEW, url));
                        } catch (Exception ignored) {
                            new AlertDialog.Builder(activity)
                                    .setTitle("Browser not available")
                                    .setMessage("No report uploaded. Copy the short report instead.")
                                    .setPositiveButton("Close", null).show();
                        }
                    }).show();
        } catch (Exception ignored) {
            new AlertDialog.Builder(activity)
                    .setTitle("Report draft unavailable")
                    .setMessage("No data uploaded. Copy the complete short report instead.")
                    .setPositiveButton("Close", null).show();
        }
    }
}
