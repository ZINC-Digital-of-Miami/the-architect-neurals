# _backups

Point-in-time copies of generated-from sources, kept because this project is **not a git
repository** — there is no other way back.

| File | What it is |
|---|---|
| `master_report.pre-consolidation-2026-08-22.md` | `src/master_report.md` as it stood before the Consolidated Edition of 2026-08-22 (223,803 B; Third Edition spine, 14 h3 chapters fewer). Restore with `cp` into `src/` if the consolidation ever needs to be unwound. |

Nothing here is deployed: `build_site3.py` copies an explicit allowlist into `site/src/`,
and this directory is not on it.
