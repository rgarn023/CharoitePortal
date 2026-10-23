# Charoite Portal environments (.cenv)

`.cenv` is the portable **Charoite Portal environment profile** file extension. Files are UTF-8 JSON with a strict versioned schema. A `.cenv` describes the realm name, theme and Windows compatibility preferences, **not** the Wine installation, Windows executable, game files, save data, wallpapers, accounts or personal storage paths.

## On your phone

- **System → Install Environment** opens the Android Files picker; select a previously downloaded `.cenv` profile. The app validates the file, shows its details, and creates a *new isolated Wine container* only after you confirm. It does **not** automatically choose the General Gaming preset.
- **System → Create Environment** asks for a name, then opens Android **Save As**. Choose a folder (such as Downloads or Documents) and save the suggested `<name>.cenv` filename. Only after the file is successfully written will the profile be added to Charoite Portal.
- **System → Export Environment (.CENV)** saves the *currently selected* environment's theme and settings as a reusable file to a folder you choose. It does not copy game installs, user data or save games.
- **System → Switch Environment** changes the active profile without moving any Wine data.

The `General-Gaming.cenv` file in this folder is an example you can download and then select with **Install Environment**. Repeat imports create a separate environment with a unique local name and container, never replace the original.

## Schema v1

```json
{
  "format": "com.charoitegames.portal.environment",
  "version": 1,
  "name": "General Gaming",
  "theme": "cosmic",
  "settings": {
    "compatibilityGraphics": false,
    "displayMode": 0,
    "capturePointer": false
  }
}
```

Valid themes are `cosmic` and `sakura`. `displayMode` indexes supported Charoite Core modes (0 = Automatic). Imported files are limited to 16 KiB and reject unknown keys, external paths, scripts and unsupported versions. The app itself still requires the included Wine/Box64 runtime. `.cenv` is *not* an APK, ZIP, Windows environment backup or executable package.

Japanese text support (Shift-JIS/CP932, licensed fonts) may be enabled per realm and exported as the optional boolean `settings.japaneseText` in schema v1; missing value defaults to off for imported custom realms. Touhou Realm continues to default on automatically.
