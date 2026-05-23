# Personal Tracker

Two single-file web apps that share a cloud-synced state:

- **`Family_Quest.html`** — kids' daily quests, stars, prizes, reading list.
- **`Noman_Daily_Tracker.html`** — personal timeline, long-term projects, completed log, reading list, history heatmap.

Both files are vanilla HTML/CSS/JS. No build step. Open the file, you have an app.

State persists in three tiers (whichever is available wins, in order):

1. **Supabase** (recommended) — Postgres in the cloud, multi-device sync.
2. **`serve.py`** — local Python file-DB at `./db/*.json` (when you `python3 serve.py` and visit `http://127.0.0.1:8123`).
3. **`localStorage`** — works even if you just open the HTML directly. No sync, but no setup either.

The Cloud Sync panel inside each app (Family Quest → *Settings*, Noman → *Guide*) lets you paste your Supabase URL + anon key once. After that, opening the app on any device pulls the latest state.

---

## Quick start (5 steps)

### 1. Create a Supabase project
1. Sign up at [supabase.com](https://supabase.com) — free tier is plenty.
2. New project → name it whatever, pick the closest region, set a database password (you won't need it again).

### 2. Create the table
Supabase Dashboard → **SQL Editor** → New query → paste the contents of [`supabase/schema.sql`](supabase/schema.sql) → **Run**.

That's the entire backend. One table, two rows (`family_quest` and `noman_tracker`), each holding a JSON document.

### 3. Grab your two keys
Supabase Dashboard → **Settings** → **API**:
- *Project URL* (e.g. `https://abcd1234.supabase.co`)
- *anon* key (the **public** one — starts with `eyJ…`)

### 4. Put the app online via GitHub Pages
```bash
# in a fresh GitHub repo
git init && git add . && git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<you>/personal-tracker.git
git push -u origin main
```
Then on GitHub: **Settings → Pages → Source: "GitHub Actions"**. The workflow at [`.github/workflows/deploy.yml`](.github/workflows/deploy.yml) builds and ships on every push to `main`. After ~30 s your site is live at `https://<you>.github.io/<repo>/`.

### 5. Connect each app to your Supabase project
1. Open your deployed site.
2. **Family Quest** → log in → Settings tab → **Cloud Sync (Supabase)** → paste URL + key → *Save* → click ⬆️ **Push current data to cloud**.
3. **Daily Tracker** → Guide tab → same Cloud Sync panel → *Save*. (The two apps share the same Supabase project.)

Done. From now on any device, browser, or refresh starts from the same cloud state.

---

## Running locally

Two flavours of "local":

### A. Open the HTML directly
Just double-click `Family_Quest.html` or `Noman_Daily_Tracker.html`. Everything works; state lives in browser `localStorage`. No sync, no `serve.py` needed.

### B. Local file-DB via `serve.py`
```bash
python3 serve.py
# open http://127.0.0.1:8123/Family_Quest.html
```
This adds a local Python backend that snapshots all state to `./db/family_quest.json` and `./db/noman_tracker.json`, plus a per-day snapshot under `./db/snapshots/`. Useful for offline use or when you don't want to depend on Supabase.

### Both at once
If Supabase is configured AND `serve.py` is running, Supabase wins. `serve.py` keeps a local cache via `./db/*` that you can use as a backup.

---

## Login & session

Each app uses a local PIN (no email, no OAuth). After you successfully enter the PIN, the session sticks for **30 days** — refreshing the page won't re-prompt. The **Logout** button in the top-right clears the session immediately.

Default PINs (change them in Settings → Passwords after first login):
- Father: `1234`
- Mother: `1234`
- Kid 1: `0001`
- Kid 2: `0002`

The Noman tracker has no login at all — it's a single-user app.

---

## Backup safety

Two parallel safety nets:

- **Auto-backup**: each app downloads a JSON backup to your Downloads folder once per day, the first time it opens. Move your Downloads into iCloud / Google Drive and these auto-mirror everywhere.
- **`db/before-recovery/`**: when you change Supabase configs or move backends, the previous `db/*.json` is stashed under here. Nothing is destructively overwritten without leaving a copy.

You can also **Export Backup** manually at any time (Family Quest → Settings, Noman → Projects toolbar).

---

## File layout

```
.
├── Family_Quest.html             # kids' quest app
├── Noman_Daily_Tracker.html      # personal tracker app
├── serve.py                      # optional local file-DB backend
├── supabase/
│   └── schema.sql                # one-time DB setup
├── .github/workflows/deploy.yml  # publishes to GitHub Pages on push
├── ARCHITECTURE.md               # deep-dive for contributors
└── README.md                     # this file
```

---

## Outsourcing handoff

When you bring in another developer, point them at [`ARCHITECTURE.md`](ARCHITECTURE.md). It explains the storage adapter, the data shapes, and where to wire new features.
