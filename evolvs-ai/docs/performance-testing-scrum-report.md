# EvolvS AI Performance Testing Report

Date: 2026-06-21
Scope: Web application performance testing for audio transcription, audit analytics, reporting, and future QA workflow modules.
Method: Agile Scrum test planning with repeatable Playwright smoke checks.

## Product Goal

EvolvS AI is a QA operations application where a user uploads audio, the system decodes speech to text, converts the transcript into structured audit records, and produces operational intelligence for QA teams.

Target modules:

- Audit Management: structured audit operations.
- RCA Management: root cause workflow support.
- DSAT, CSAT & NPS Scoring: customer scoring support.
- Benchmarking: performance comparison and tracking.
- Workflow Intelligence: mapping complex user and system journeys.
- Data Scrubbing: cleanup and validation before reporting.
- Compliance Support: critical checks and compliance review.
- Workflow Automation: routing, tagging, and summaries.
- Live Reporting: real-time audit and report access.
- Opportunity Arrest: top opportunity identification and targeting.

## Performance Test Strategy

Performance testing is split into three layers:

- Frontend smoke performance: app load, page usability, mocked API response rendering, tab switching, and visible state changes.
- API performance: upload, analytics, audit drilldown, audio queueing, transcript polling, and report generation latency.
- Data performance: large audio files, large transcript text, large Excel exports, large audit tables, and changed database schemas.

The current automated suite covers the frontend smoke layer. API and database load tests should be added after the altered database tables are finalized and seeded with realistic data volumes.

## Current Automated Coverage

Playwright file:

`frontend/tests/performance.spec.ts`

Current performance checks:

| Area | Scenario | Budget |
| --- | --- | --- |
| Audio Transcription | Audio page becomes usable | Under 3 seconds |
| Audio Transcription | Mock upload to completed transcript render | Under 6 seconds |
| Live Reporting | Dashboard renders generated audit reporting dataset | Under 4 seconds |
| Audit Management | Drilldown tab switches on larger audit dataset | Under 1 second |

The analytics test uses generated mock data:

- 2,500 total audits in summary.
- 250 audit rows rendered through dashboard/drilldown flow.
- 25 agent performance rows.
- 40 compliance parameter rows.

## Executed Results

Execution date: 2026-06-22

| Check | Measured Result | Budget | Status |
| --- | --- | --- | --- |
| Audio page usable | 511 ms | Under 3,000 ms | Pass |
| Mocked audio upload to transcript | 625 ms | Under 6,000 ms | Pass |
| Dashboard reporting load | 1,065 ms | Under 4,000 ms | Pass |
| Dashboard drilldown switch | 650 ms | Under 1,000 ms | Pass |

Additional application checks:

- Playwright performance suite: 4 passed.
- Playwright audio workflow suite: 7 passed.
- Playwright general e2e suite: 3 passed.
- Backend pytest suite: 2 passed, 1 dependency deprecation warning.
- Frontend TypeScript check: passed.
- Frontend production build: passed.

Production bundle:

- Main JavaScript: 844.24 kB minified, 237.35 kB gzip.
- Vite warning: main chunk exceeds the 500 kB warning threshold.
- Recommended backlog item: lazy-load dashboard charts and split Supabase, Recharts, and audio/reporting routes into separate chunks.

## Scrum Backlog

### Epic 1: Audio To Structured QA Dataset

User story:
As a QA user, I want to upload a call recording so that EvolvS AI can transcribe it and convert it into structured audit data.

Acceptance criteria:

- MP3, WAV, FLAC, OGG, and M4A files are accepted.
- Upload returns a queued recording id.
- Transcript completes with plain text and VTT output.
- Transcript can be transformed into audit-ready rows.
- Failed transcription stores a clear failure reason.

Performance criteria:

- Audio upload request should return within 2 seconds after file transfer completes.
- UI should show processing state within 500 ms after click.
- Transcript polling should not freeze the page.

### Epic 2: Audit And RCA Reporting

User story:
As a QA lead, I want uploaded transcripts and audit data to become dashboards, RCA views, and scoring reports so that I can manage performance issues.

Acceptance criteria:

- Dashboard shows audit volume, completion rate, and average score.
- Agent and parameter tables render from the latest uploaded dataset.
- Drilldown opens audit-level records without full page reload.
- RCA workflow can identify top failure reasons.

Performance criteria:

- Dashboard first usable state should stay under 4 seconds for normal datasets.
- Drilldown tab switch should stay under 1 second for 250 visible audit records.
- API should paginate or aggregate before returning very large audit datasets.

### Epic 3: Compliance, Scrubbing, And Automation

User story:
As a compliance user, I want the system to clean, validate, tag, and route QA records so that critical issues are acted on quickly.

Acceptance criteria:

- Missing and invalid fields are identified before reporting.
- Compliance failures are tagged separately from scoring failures.
- Opportunity Arrest identifies the highest-impact recurring issues.
- Live reports refresh from the latest valid dataset.

Performance criteria:

- Data validation should produce first results within 5 seconds for standard uploads.
- Long-running scrubbing jobs should run asynchronously.
- Live reporting endpoints should avoid returning unbounded row sets.

## Database Change Risks

Tables were altered, so these checks are required before load testing:

- Confirm current table names, primary keys, foreign keys, and RLS policies.
- Confirm `call_recordings`, `transcript_segments`, uploaded datasets, audit records, RCA records, scoring records, and compliance records still match backend queries.
- Add indexes for common filters: `org_id`, `uploaded_by`, `recording_id`, `created_at`, `audit_id`, `agent`, `status`, and score/report date fields.
- Confirm large text columns for transcript and VTT are not repeatedly fetched when only summary data is needed.
- Split summary endpoints from detail endpoints to avoid over-fetching.

## Definition Of Done

A performance story is done when:

- Automated Playwright performance smoke test passes.
- API timing is captured for at least one realistic dataset.
- Database query path is reviewed against the altered schema.
- Any endpoint over budget has an owner and fix plan.
- Results are written into the sprint test report.

## Commands

Frontend performance smoke suite:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npm run test:performance
```

Frontend type check:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npm run type-check
```

## Next Performance Work

- Add backend API timing tests for `/api/health`, `/api/audio/upload`, `/api/audio/{id}`, `/api/analytics`, and `/api/analytics/audit/{audit_id}`.
- Create seeded database fixtures that match the altered tables.
- Add an Excel-generation benchmark once transcript-to-audit export is implemented.
- Add load profiles for 10, 50, and 100 concurrent users after authentication is stable.
- Add route-level code splitting to reduce the 844.24 kB production JavaScript bundle.
