package com.charoitegames.core;

import java.io.File;
import java.util.Locale;

/**
 * Game-specific metadata/policies, chosen by the current environment.
 * All other Core services consume these policies rather than hardcoding
 * Touhou executable detection in the Portal UI.
 */
public final class CharoiteGameProfiles {
    public interface Profile {
        boolean acceptsInstalledExecutable(String filename);
        String displayName(String filename);
    }

    private static final Profile GENERAL = new Profile() {
        public boolean acceptsInstalledExecutable(String filename) {
            String name = filename.toLowerCase(Locale.ROOT);
            return name.endsWith(".exe") && !CharoiteGameImport.isLikelyInstaller(name)
                    && !name.equals("unins000.exe") && !name.equals("uninstall.exe")
                    && !name.equals("winecfg.exe") && !name.equals("explorer.exe")
                    && !name.equals("regedit.exe");
        }
        public String displayName(String filename) {
            return new File(filename).getName().replaceFirst("(?i)\\.exe$", "");
        }
    };

    private static final Profile TOUHOU = new Profile() {
        public boolean acceptsInstalledExecutable(String filename) {
            String name = filename.toLowerCase(Locale.ROOT);
            return name.equals("gn_enbu.exe") || name.equals("enbu_ap.exe")
                    || CharoiteShardOfDreamsSupport.isExpansionGame(name)
                    || name.matches("th(0[6-9]|1[0-9]|20)\\.exe");
        }
        public String displayName(String filename) {
            String name = new File(filename).getName().toLowerCase(Locale.ROOT);
            if (CharoiteShardOfDreamsSupport.isExpansionGame(name))
                return "Touhou Puppet Dance Performance: Shard of Dreams";
            if (name.equals("gn_enbu.exe")) return "Touhou Puppet Dance Performance";
            return "Touhou game: " + new File(filename).getName();
        }
    };
    private CharoiteGameProfiles() {}

    public static Profile forEnvironment(String environmentId) {
        return CharoiteEnvironments.TOUHOU.equals(environmentId) ? TOUHOU : GENERAL;
    }
}
