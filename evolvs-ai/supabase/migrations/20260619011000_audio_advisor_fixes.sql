create schema if not exists extensions;
alter extension vector set schema extensions;

create index if not exists call_recordings_org_id_idx
    on public.call_recordings (org_id);

create index if not exists transcript_segments_org_id_idx
    on public.transcript_segments (org_id);
