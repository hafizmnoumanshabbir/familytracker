# Architecture

> One-page overview for a developer picking this up cold.

## What this is

Two independent single-file HTML apps that share a single JSON-document-per-app data store:

- **`Family_Quest.html`** — parent + kids interface. Daily quests, stars, prizes, reading list, history heatmap.
- **`Noman_Daily_Tracker.html`** — single-user productivity tracker. Time-blocked timeline, long-term projects, done log, history.

Vanilla HTML/CSS/JS. No bundler, no framework, no transpile step. Edit and reload.

## Storage adapter (the only thing you need to understand)

Each app has its own adapter, but both follow the same pattern:

```
write path:  app code → saveData() → localStorage (always)
                                  → debounced push to cloud
read path:   boot → loadData() → try Supabase (cloud)
                              → else try /db/<app> (local serve.py)
                              → else localStorage (offline)
                              → merge with on-disk defaults
```

The three backends sit behind one function. Adding a new one (e.g. Cloudflare D1) means swapping the implementation inside `_dbFetch` and `_dbPushSoon` (FQ) or `_ndtDbHydrate` and `_ndtDbPushSoon` (NDT) — nothing else changes.

### Why a JSON document and not a relational schema

Both apps already model their entire state as a single nested JSON object that the UI mutates in place. Putting it in a `jsonb` column gives us:

- Zero schema migrations as features evolve.
- One trivial upsert per save.
- Server-side JSONPath/jsonb operators if we ever need to query across kids/days/projects.

If you outgrow this (e.g. you want a leaderboard across many families), promote the columns one by one — Postgres lets the JSON live next to relational columns indefinitely.

### Conflict resolution

Last write wins. Both apps run a debounced upsert (250 ms FQ, 300 ms NDT) after every state change. To prevent a near-empty server snapshot from clobbering a fuller local copy, hydrate uses a **richness score**:

- **FQ** (`_fqScore`): weighted count of kids, blocks, activities, prizes, books, progress days.
- **NDT** (`_ndtScore`): per-key — parses the JSON value, scores by array length / object key count, falls back to string length.

If local wins on hydrate, the local copy is pushed up so the next device gets the good data.

### Where to wire a feature

| Doing | Touch |
|---|---|
| New activity field | `DEFAULT_ACTIVITIES` shape, `renderManage`, `saveActivity` |
| New tab | `tabsForRole`, `switchView`, add a `<div id="XView">` and a `renderX()` |
| New cloud backend | `_dbFetch` + `_dbPushSoon` in FQ, `_ndtDbHydrate` + `_ndtDbPushSoon` in NDT |
| New schema (Supabase) | Add to `supabase/schema.sql`, write a `data_migrations` block in the SDK call |

## Session / auth

There's no real auth — login is a per-role 4-digit PIN stored in `appData.passwords` and per-kid `appData.kids[i].password`. After a successful `submitLogin()`, `_saveSession(currentUser)` stores `{user, expiresAt = now + 30 days}` in `localStorage.fq_session`. Boot calls `tryAutoLogin()` before showing the login screen.

Noman tracker has no login flow.

To move to real auth (Supabase magic-link, OAuth, etc.) replace `submitLogin` / `_loadSession` with Supabase Auth — the rest of the app is auth-agnostic.

## Drag & drop

Both apps use pointer-events DnD with a ghost element. There are two implementations because the apps were built separately:

- **NDT** — original implementation in `dndStart` / `dndMove` / `dndEnd` (used for projects, plus extended for timeline blocks and tasks). Recognises drag kinds: `cat`, `item`, `sub`, `tl-block`, `tl-task`.
- **FQ** — `fqDndStart` / `fqDndMove` / `fqDndEnd`. Recognises kinds: `block`, `activity`, `prize`, `kid`. Activities are constrained to drop within their own block (via `data-fq-parent`).

If you need a unified DnD across both apps, extract NDT's implementation into a shared snippet — FQ's is structurally identical, just narrower.

## Deployment

- **Static frontend** → GitHub Pages via `.github/workflows/deploy.yml`. Builds a `_site/` directory containing only the published files (HTML + schema + docs), uploads to Pages.
- **Backend** → Supabase. The CDN-loaded JS SDK talks directly to Postgres via PostgREST. No serverless functions, no API gateway.
- **Local-only mode** → `python3 serve.py` runs `http.server` plus tiny `GET/POST /db/*` endpoints that read/write `./db/*.json`.

The Supabase URL and anon key are **client-side config** stored in `localStorage.tracker_supabase`. They are not in the repo. Each user pastes their own (or shares one across family devices). The anon key is intended to be public; access control is enforced by Postgres RLS policies in `supabase/schema.sql`.

## Files you can ignore

- `extract.py` — one-off helper, unused at runtime.
- `db/before-recovery/` — auto-stashed snapshots from `db/` when a destructive reset is about to happen.
- `db/snapshots/` — daily snapshots of the file-DB, written by `serve.py` on every POST.
