package org.winehq.wine;

import android.app.Activity;
import android.os.Bundle;
import android.content.Context;
import android.content.Intent;
import android.app.AlertDialog;
import android.util.AtomicFile;
import android.widget.LinearLayout;
import android.widget.Button;
import android.widget.TextView;

import java.io.File;
import java.io.IOException;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;
import java.io.InputStream;
import java.nio.file.Files;

public final class WineActivity extends Activity {
    // ntdll registers this exact method during JNI_OnLoad.
    private native String wine_init(String[] command, String[] environment);

    private static AtomicFile checkpoint(Context context) {
        return new AtomicFile(new File(context.getFilesDir(), "wine29-display-check.txt"));
    }

    private static void record(Context context, String message) throws IOException {
        AtomicFile file = checkpoint(context);
        FileOutputStream output = file.startWrite();
        try {
            output.write(message.getBytes(StandardCharsets.UTF_8));
            file.finishWrite(output);
        } catch (IOException failure) {
            file.failWrite(output);
            throw failure;
        }
    }

    public static void launchCheck(Activity portal) {
        try {
            record(portal, "Interrupted before the Wine29 display activity started.");
            portal.startActivity(new Intent(portal, WineActivity.class));
        } catch (IOException | RuntimeException failure) {
            checkpoint(portal).delete();
            new AlertDialog.Builder(portal).setTitle("Wine29 display check")
                    .setMessage("Could not start the check. " + failure.getClass().getSimpleName())
                    .setPositiveButton("OK", null).show();
        }
    }

    public static void showLastCheck(Activity portal) {
        AtomicFile file = checkpoint(portal);
        if (!file.getBaseFile().isFile()) return;
        try {
            String report = new String(file.readFully(), StandardCharsets.UTF_8);
            file.delete();
            new AlertDialog.Builder(portal).setTitle("Wine29 display check")
                    .setMessage(report).setPositiveButton("OK", null).show();
        } catch (IOException failure) {
            android.util.Log.w("Wine29Display", "Could not read display checkpoint", failure);
        }
    }

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        int inset = Math.round(20 * getResources().getDisplayMetrics().density);
        layout.setPadding(inset, inset, inset, inset);
        TextView result = new TextView(this);
        result.setText("Checking Wine29 display libraries…");
        layout.addView(result);
        Button done = new Button(this);
        done.setText("Return to Charoite Portal");
        done.setOnClickListener(view -> finish());
        layout.addView(done);
        setContentView(layout);

        new Thread(() -> {
            String checked = checkLibraries();
            try {
                record(this, checked);
            } catch (IOException failure) {
                android.util.Log.w("Wine29Display", "Could not save display result", failure);
            }
            String report = checked;
            runOnUiThread(() -> {
                if (!isDestroyed()) result.setText(report);
            });
        }, "Wine29DisplayLibraries").start();
    }

    private String checkLibraries() {
        String[] libraries = {"ntdll.so", "win32u.so", "wineandroid.so"};
        File directory = null;
        String current = "staging";
        try {
            record(this, "Interrupted while preparing the Wine29 display libraries.");
            directory = Files.createTempDirectory(getCacheDir().toPath(), "wine29-display-").toFile();
            for (String library : libraries) {
                current = library;
                File file = new File(directory, library);
                try (InputStream asset = getAssets().open("wine29-java-host/" + library)) {
                    Files.copy(asset, file.toPath());
                }
                record(this, "Interrupted while loading " + library + ".");
                System.load(file.getAbsolutePath());
            }
            return "PASS — Android loaded all three Wine29 display libraries.";
        } catch (IOException | LinkageError failure) {
            return "FAIL — " + current + " — " + failure.getMessage();
        } finally {
            if (directory != null) {
                for (String library : libraries) new File(directory, library).delete();
                directory.delete();
            }
        }
    }
}
