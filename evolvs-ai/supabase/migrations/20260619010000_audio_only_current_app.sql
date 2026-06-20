-- EvolvS AI - audio-only schema for the current FastAPI implementation.
-- Paste into Supabase SQL Editor if you want to enable live audio upload now.
--
-- This intentionally does NOT depend on organisations/profiles/audits.
-- The current backend uses auth.users.id as the tenant/user boundary:
--   call_recordings.org_id = current_user.id
--   call_recordings.uploaded_by = current_user.id
--   transcript_segments.org_id = current_user.id

create schema if not exists extensions;
create extension if not exists "pgcrypto";
create extension if not exists "vector" with schema extensions;

insert into storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
values (
    'audio',
    'audio',
    false,
    104857600,
    array[
        'audio/mpeg',
        'audio/wav',
        'audio/flac',
        'audio/ogg',
        'audio/mp4',
        'audio/x-m4a',
        'audio/webm'
    ]
)
on conflict (id) do update set
    public = false,
    file_size_limit = excluded.file_size_limit,
    allowed_mime_types = excluded.allowed_mime_types;

create table if not exists public.call_recordings (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references auth.users(id) on delete cascade,
    audit_id uuid,
    agent_id uuid,
    uploaded_by uuid not null references auth.users(id) on delete cascade,
    filename text not null,
    storage_path text not null,
    duration_s numeric,
    file_size bigint not null default 0 check (file_size >= 0),
    channel text,
    status text not null default 'pending' check (status in ('pending', 'processing', 'done', 'failed')),
    error_msg text,
    transcript text,
    vtt_content text,
    created_at timestamptz not null default now()
);

create index if not exists call_recordings_uploaded_created_idx
    on public.call_recordings (uploaded_by, created_at desc);

create index if not exists call_recordings_org_id_idx
    on public.call_recordings (org_id);

alter table public.call_recordings enable row level security;

drop policy if exists "Users can read their call recordings" on public.call_recordings;
create policy "Users can read their call recordings"
    on public.call_recordings
    for select
    to authenticated
    using ((select auth.uid()) = uploaded_by);

drop policy if exists "Users can insert their call recordings" on public.call_recordings;
create policy "Users can insert their call recordings"
    on public.call_recordings
    for insert
    to authenticated
    with check ((select auth.uid()) = uploaded_by);

drop policy if exists "Users can update their call recordings" on public.call_recordings;
create policy "Users can update their call recordings"
    on public.call_recordings
    for update
    to authenticated
    using ((select auth.uid()) = uploaded_by)
    with check ((select auth.uid()) = uploaded_by);

drop policy if exists "Users can delete their call recordings" on public.call_recordings;
create policy "Users can delete their call recordings"
    on public.call_recordings
    for delete
    to authenticated
    using ((select auth.uid()) = uploaded_by);

create table if not exists public.transcript_segments (
    id uuid primary key default gen_random_uuid(),
    org_id uuid not null references auth.users(id) on delete cascade,
    recording_id uuid not null references public.call_recordings(id) on delete cascade,
    speaker text not null default 'unknown',
    start_ms integer,
    end_ms integer,
    text text not null,
    confidence numeric,
    embedding extensions.vector(384),
    created_at timestamptz not null default now()
);

create index if not exists transcript_segments_recording_idx
    on public.transcript_segments (recording_id, start_ms);

create index if not exists transcript_segments_org_id_idx
    on public.transcript_segments (org_id);

create index if not exists transcript_segments_embedding_hnsw_idx
    on public.transcript_segments
    using hnsw (embedding extensions.vector_cosine_ops);

alter table public.transcript_segments enable row level security;

drop policy if exists "Users can read their transcript segments" on public.transcript_segments;
create policy "Users can read their transcript segments"
    on public.transcript_segments
    for select
    to authenticated
    using ((select auth.uid()) = org_id);

drop policy if exists "Users can insert their transcript segments" on public.transcript_segments;
create policy "Users can insert their transcript segments"
    on public.transcript_segments
    for insert
    to authenticated
    with check ((select auth.uid()) = org_id);

drop policy if exists "Users can update their transcript segments" on public.transcript_segments;
create policy "Users can update their transcript segments"
    on public.transcript_segments
    for update
    to authenticated
    using ((select auth.uid()) = org_id)
    with check ((select auth.uid()) = org_id);

select
    table_name,
    case when c.relrowsecurity then 'YES' else 'NO' end as rls_enabled
from information_schema.tables t
join pg_class c
    on c.relname = t.table_name
    and c.relnamespace = 'public'::regnamespace
where t.table_schema = 'public'
    and t.table_name in ('call_recordings', 'transcript_segments')
order by table_name;
