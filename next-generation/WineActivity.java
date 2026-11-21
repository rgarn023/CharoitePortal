package org.winehq.wine;

import android.app.Activity;
import android.os.Bundle;
import android.widget.LinearLayout;
import android.widget.Button;
import android.widget.TextView;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;

public final class WineActivity extends Activity {
    // ntdll registers this exact method during JNI_OnLoad.
    private native String wine_init(String[] command, String[] environment);

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
            String report = checkLibraries();
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
            directory = Files.createTempDirectory(getCacheDir().toPath(), "wine29-display-").toFile();
            for (String library : libraries) {
                current = library;
                File file = new File(directory, library);
                try (InputStream asset = getAssets().open("wine29-java-host/" + library)) {
                    Files.copy(asset, file.toPath());
                }
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
