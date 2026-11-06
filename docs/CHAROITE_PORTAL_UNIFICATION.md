# Charoite Portal: one flagship product, Next as the development track

**Decision (November 6, 2026):** Charoite Next is the temporary experimental
development track for the *next generation of Charoite Portal*. The intended
shipping product is **Charoite Portal**, not two permanently competing apps.
**Charoite Core** names the compatibility/runtime engine inside Portal.

## Keep two identities until a verified migration

- **Stable Portal** remains `com.charoite`, with its current signer, games,
  Wine prefixes, saves and environments unchanged.
- **Experimental Next** remains `com.charoitx` and retains the Next signer and
  its private scratch areas. It is not yet a working Wine29 Windows launcher.
- Do **not** change the Next application ID to `com.charoite` to make the label
  appear unified. Android treats package IDs as distinct app/data identities;
  a renamed APK does not become an in-place upgrade with preserved data.
- Do not automatically migrate, uninstall, wipe, overwrite, or share either
  app's private data or reset old Wine scratch generations.

## Path toward the future Portal

1. Fix the isolated ARM64 Wine29 native/PE loader and prove an initial
   Wineboot/prefix on a **new, separately authorized** test area.
2. Validate ordinary Windows app launches, graphics, sound, input and
   rotation; then selected games and store clients. Never promise
   unsupported anti-cheat compatibility or attempt to bypass protection.
3. Bring modern UI/runtime features to parity with stable Portal and
   demonstrate retention of games, saves, environments, wallpapers and
   boot experience in migration rehearsals.
4. Plan an explicit, reversible migration to the **stable `com.charoite`**
   identity using its established signing key. If transfer from experimental
   Next is needed, make it user-initiated and verified (export/import or
   another supported consent-based mechanism), not silent app-data access.
5. Only then promote the Next codebase into the shipping **Charoite Portal**.
   "Next" can remain an optional testing channel but should not be the
   advertised final product.

**Release gate:** a successful APK build, module staging or a PE header pass
does not satisfy the runtime-compatibility or safe-data-migration gates.

See [CURRENT_HANDOFF.md](CURRENT_HANDOFF.md) for the live state and
[WINE29_KERNEL32_LOADER_AUDIT.md](WINE29_KERNEL32_LOADER_AUDIT.md) for the
current technical blocker.
