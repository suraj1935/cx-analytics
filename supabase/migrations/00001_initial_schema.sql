-- Enable UUID extension
create extension if not exists "uuid-ossp";

-- Organisations (multi-tenant root)
create table organisations (
  id uuid primary key default uuid_generate_v4(),
  name text not null,
  created_at timestamptz default now()
);

-- Profiles (extends Supabase auth.users)
create table profiles (
  id uuid primary key references auth.users(id) on delete cascade,
  org_id uuid references organisations(id),
  full_name text,
  role text default 'agent', -- 'admin' | 'auditor' | 'agent'
  team_id uuid,
  created_at timestamptz default now()
);

-- Survey responses (CSAT / NPS)
create table survey_responses (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organisations(id),
  agent_id uuid references profiles(id),
  csat_score int check (csat_score between 1 and 5),
  nps_score int check (nps_score between 0 and 10),
  verbatim text,
  sentiment text, -- 'positive' | 'neutral' | 'negative'
  channel text,
  received_at timestamptz default now()
);

-- Audits
create table audits (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organisations(id),
  agent_id uuid references profiles(id),
  auditor_id uuid references profiles(id),
  form_id uuid,
  score numeric(5,2),
  status text default 'draft',
  created_at timestamptz default now()
);

-- RCAs
create table rcas (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organisations(id),
  audit_id uuid references audits(id),
  root_cause text,
  capa_action text,
  owner_id uuid references profiles(id),
  due_date date,
  status text default 'open',
  keywords jsonb,
  created_at timestamptz default now()
);

-- Uploaded CSVs metadata
create table uploads (
  id uuid primary key default uuid_generate_v4(),
  org_id uuid references organisations(id),
  uploaded_by uuid references profiles(id),
  filename text,
  row_count int,
  storage_path text,
  created_at timestamptz default now()
);

-- Row Level Security: every table only returns org's own data
alter table survey_responses enable row level security;
alter table audits enable row level security;
alter table rcas enable row level security;
alter table uploads enable row level security;

create policy "org isolation" on survey_responses
  using (org_id = (select org_id from profiles where id = auth.uid()));

create policy "org isolation" on audits
  using (org_id = (select org_id from profiles where id = auth.uid()));

create policy "org isolation" on rcas
  using (org_id = (select org_id from profiles where id = auth.uid()));

create policy "org isolation" on uploads
  using (org_id = (select org_id from profiles where id = auth.uid()));
