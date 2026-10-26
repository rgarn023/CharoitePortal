# Pop-up keyboard and Shard of Dreams compatibility

## System keyboard

TPDP's Charoite Core handheld overlay now includes a visible **KEYBOARD**
button between More and Hide Keys. Tapping opens the Android system
keyboard using the existing XServer runtime's input-method implementation.
The keyboard works alongside the original Game Boy-style controls; holding
a gamepad button is released before opening it. It does not change any
Wine keymaps, input profiles or game data.

The on-screen Android IME must still be tested on the physical phone for
both showing and successfully typing into a game text entry field. The
runtime's existing menu used the same method previously.

## Shard of Dreams `enbu_ap.exe`

The expansion is a distinct install and needs the base TPDP game.
A documented Wine path compatibility issue can make Shard of Dreams
expect a `notkey` link to the original game inside the expansion folder.
See https://gist.github.com/RobertTheSable/6c4d705623b4de8d8cb3c954eac4814f .

Core now handles this automatically at **launch** of `enbu_ap.exe`:

1. Verify the expansion executable is under a Charoite-managed
   `.wine/drive_c` directory.
2. Look for the original `gn_enbu.exe` installation in the same Wine C:
   drive, preferring a sibling installation, with a bounded read-only
   fallback scan.
3. If the expansion has no existing `notkey` entry and the base directory
   is verified, create a single symbolic-link reference to it.
4. Never overwrite, delete, move, rename, or copy existing installation
   files; never delete saves. Leave all existing `notkey` entries unchanged.
5. Record a readable result under **SHARD OF DREAMS COMPATIBILITY**
   in View Last Launch Diagnostics.

This can fix missing-base-file launches in older Wine, but it is not a
proven resolution of every possible expansion issue: successful startup
of Shard of Dreams still requires physical-device testing. Base TPDP
continues using verified DXVK 1.10.3 + Turnip.

The Library's installed-executable discovery already supports
`enbu_ap.exe`; Setup -> Find Installed Games can rescan if the tile
isn't visible after the installer closes. If no game executable exists,
the installer itself may not have finished or may be missing companion
media, and no link should be invented.
