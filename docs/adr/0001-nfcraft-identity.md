# ADR 0001 — product identity and compatibility

Date: 2026-09-05. Status: accepted by owner.

The permanent app/repo name is **nfcraft**, lowercase without a separator. Rename the Python package and visible UI/distribution metadata, retain the existing implementation, and keep the local-first architecture. This is not a rewrite or an external trademark/domain clearance claim.

The canonical agent CLI is `nfcraftctl`; retain `nfcctl` and `nfcctl.py` as compatibility aliases. Keep the established `nfc_*` MCP names for now; the server is named `nfcraft`. Public URLs, SQLite/public-export schema 1 and stored identities do not change for branding.

The default local data root becomes `nfcraft`. A detected legacy journal prevents silent empty-state startup; offer explicit old-root selection or a reviewed non-destructive import. No automatic credential transfer, identity reallocation, cloud resource rename, or data deletion is authorized by the brand change.
