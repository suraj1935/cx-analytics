create extension if not exists "pgcrypto";
create extension if not exists "vector";

create table if not exists public.upload_datasets (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    file_name text not null,
    file_type text not null check (file_type in ('csv', 'xlsx', 'xls')),
    rows_processed integer not null default 0 check (rows_processed >= 0),
    sheets jsonb not null,
    created_at timestamptz not null default now()
);

create index if not exists upload_datasets_user_created_idx
    on public.upload_datasets (user_id, created_at desc);

alter table public.upload_datasets enable row level security;

drop policy if exists "Users can read their uploaded datasets" on public.upload_datasets;
create policy "Users can read their uploaded datasets"
    on public.upload_datasets
    for select
    to authenticated
    using ((select auth.uid()) = user_id);

drop policy if exists "Users can insert their uploaded datasets" on public.upload_datasets;
create policy "Users can insert their uploaded datasets"
    on public.upload_datasets
    for insert
    to authenticated
    with check ((select auth.uid()) = user_id);

drop policy if exists "Users can delete their uploaded datasets" on public.upload_datasets;
create policy "Users can delete their uploaded datasets"
    on public.upload_datasets
    for delete
    to authenticated
    using ((select auth.uid()) = user_id);

insert into storage.buckets (id, name, public)
values ('audio', 'audio', false)
on conflict (id) do nothing;

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
    embedding vector(384),
    created_at timestamptz not null default now()
);

create index if not exists transcript_segments_recording_idx
    on public.transcript_segments (recording_id, start_ms);

create index if not exists transcript_segments_embedding_hnsw_idx
    on public.transcript_segments
    using hnsw (embedding vector_cosine_ops);

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
