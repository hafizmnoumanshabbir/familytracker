-- ============================================================================
-- Personal Tracker — Supabase schema
-- Paste this whole file into:
--   Supabase Dashboard → SQL Editor → "+ New query" → Run
-- It's idempotent: safe to run again.
-- ============================================================================

-- One row per app. data is a JSON document — same shape the apps already use
-- in localStorage, so migration is a single upsert per app.
create table if not exists app_state (
    app_name    text primary key,
    data        jsonb not null default '{}'::jsonb,
    updated_at  timestamptz not null default now()
);

-- Seed the two expected rows (no-op if they exist)
insert into app_state (app_name, data) values ('family_quest',  '{}'::jsonb)
    on conflict (app_name) do nothing;
insert into app_state (app_name, data) values ('noman_tracker', '{}'::jsonb)
    on conflict (app_name) do nothing;

-- Bump updated_at on every write so the apps can detect remote changes
create or replace function set_app_state_updated_at()
returns trigger language plpgsql as $$
begin
    new.updated_at := now();
    return new;
end;
$$;

drop trigger if exists trg_app_state_updated_at on app_state;
create trigger trg_app_state_updated_at
    before update on app_state
    for each row execute function set_app_state_updated_at();

-- ============================================================================
-- Row-Level Security
-- We're using the *anon* key from the frontend, so we have to explicitly
-- allow it. This config is single-tenant (only you / your family use it).
-- Tighten this later if you ever expose the project publicly.
-- ============================================================================
alter table app_state enable row level security;

drop policy if exists "anon read"   on app_state;
drop policy if exists "anon insert" on app_state;
drop policy if exists "anon update" on app_state;

create policy "anon read"   on app_state for select using (true);
create policy "anon insert" on app_state for insert with check (true);
create policy "anon update" on app_state for update using (true) with check (true);

-- ============================================================================
-- Done. After running:
--   1. Settings → API → copy "Project URL" and "anon public" key.
--   2. Open each tracker app, go to its Cloud Sync settings panel,
--      paste both, click "Push current data to cloud" once.
--   3. From any device, opening the app fetches the latest state on boot.
-- ============================================================================
