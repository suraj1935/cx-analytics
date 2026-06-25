create extension if not exists "vector" with schema extensions;

alter table public.call_recordings alter column storage_path drop not null;
alter table public.call_recordings add column if not exists original_file_retained boolean not null default true;

create table if not exists public.user_ai_settings (
  user_id uuid primary key references auth.users(id) on delete cascade,
  retain_original_audio boolean not null default true,
  llm_model text not null default 'qwen3:4b',
  embedding_model text not null default 'nomic-embed-text',
  updated_at timestamptz not null default now()
);

create table if not exists public.knowledge_documents (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  title text not null,
  document_type text not null default 'policy',
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_chunks (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  document_id uuid not null references public.knowledge_documents(id) on delete cascade,
  chunk_index integer not null check (chunk_index >= 0),
  content text not null,
  embedding extensions.vector(768),
  created_at timestamptz not null default now(),
  unique (document_id, chunk_index)
);

create table if not exists public.knowledge_nodes (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  node_type text not null,
  name text not null,
  properties jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create table if not exists public.knowledge_edges (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  source_node_id uuid not null references public.knowledge_nodes(id) on delete cascade,
  target_node_id uuid not null references public.knowledge_nodes(id) on delete cascade,
  relationship_type text not null,
  confidence numeric check (confidence between 0 and 1),
  evidence_recording_id uuid references public.call_recordings(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.ai_analyses (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users(id) on delete cascade,
  recording_id uuid not null references public.call_recordings(id) on delete cascade,
  model text not null,
  result jsonb not null,
  created_at timestamptz not null default now()
);

create index if not exists knowledge_documents_user_idx on public.knowledge_documents (user_id, created_at desc);
create index if not exists knowledge_chunks_user_idx on public.knowledge_chunks (user_id);
create index if not exists knowledge_chunks_embedding_hnsw_idx on public.knowledge_chunks using hnsw (embedding extensions.vector_cosine_ops);
create index if not exists knowledge_nodes_user_idx on public.knowledge_nodes (user_id);
create index if not exists knowledge_edges_source_idx on public.knowledge_edges (user_id, source_node_id);
create index if not exists knowledge_edges_target_idx on public.knowledge_edges (user_id, target_node_id);
create index if not exists knowledge_edges_source_fk_idx on public.knowledge_edges (source_node_id);
create index if not exists knowledge_edges_target_fk_idx on public.knowledge_edges (target_node_id);
create index if not exists knowledge_edges_evidence_recording_idx on public.knowledge_edges (evidence_recording_id);
create index if not exists ai_analyses_user_recording_idx on public.ai_analyses (user_id, recording_id, created_at desc);
create index if not exists ai_analyses_recording_fk_idx on public.ai_analyses (recording_id);

alter table public.user_ai_settings enable row level security;
alter table public.knowledge_documents enable row level security;
alter table public.knowledge_chunks enable row level security;
alter table public.knowledge_nodes enable row level security;
alter table public.knowledge_edges enable row level security;
alter table public.ai_analyses enable row level security;

drop policy if exists "Users manage their AI settings" on public.user_ai_settings;
create policy "Users manage their AI settings" on public.user_ai_settings for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "Users manage their knowledge documents" on public.knowledge_documents;
create policy "Users manage their knowledge documents" on public.knowledge_documents for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "Users manage their knowledge chunks" on public.knowledge_chunks;
create policy "Users manage their knowledge chunks" on public.knowledge_chunks for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "Users manage their knowledge nodes" on public.knowledge_nodes;
create policy "Users manage their knowledge nodes" on public.knowledge_nodes for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "Users manage their knowledge edges" on public.knowledge_edges;
create policy "Users manage their knowledge edges" on public.knowledge_edges for all to authenticated
  using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);
drop policy if exists "Users read their AI analyses" on public.ai_analyses;
create policy "Users read their AI analyses" on public.ai_analyses for select to authenticated using ((select auth.uid()) = user_id);
drop policy if exists "Users insert their AI analyses" on public.ai_analyses;
create policy "Users insert their AI analyses" on public.ai_analyses for insert to authenticated with check ((select auth.uid()) = user_id);

create or replace function public.match_knowledge(query_embedding extensions.vector(768), match_user_id uuid, match_count integer default 5)
returns table (chunk_id uuid, document_id uuid, document_title text, document_type text, content text, similarity double precision)
language sql stable security invoker set search_path = '' as $$
  select kc.id, kd.id, kd.title, kd.document_type, kc.content,
    1 - (kc.embedding operator(extensions.<=>) query_embedding)
  from public.knowledge_chunks kc join public.knowledge_documents kd on kd.id = kc.document_id
  where kc.user_id = match_user_id and kc.embedding is not null
  order by kc.embedding operator(extensions.<=>) query_embedding
  limit least(greatest(match_count, 1), 10)
$$;

grant select, insert, update on public.user_ai_settings to authenticated, service_role;
grant select, insert, update, delete on public.knowledge_documents, public.knowledge_chunks, public.knowledge_nodes, public.knowledge_edges to authenticated, service_role;
grant select, insert on public.ai_analyses to authenticated, service_role;
revoke execute on function public.match_knowledge(extensions.vector, uuid, integer) from public, anon;
grant execute on function public.match_knowledge(extensions.vector, uuid, integer) to authenticated, service_role;
