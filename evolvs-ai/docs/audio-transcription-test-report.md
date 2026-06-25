# Audio Transcription Test Report

Date: 2026-06-19
Application URL: http://127.0.0.1:3000/#
Scope: Audio transcription only. QA analytics is intentionally excluded.

## Result

Audio upload is now testable against the live local app and live Supabase project.

The strengthened live Playwright test opened the Audio page directly with an admin Supabase session, selected a real MP3, clicked Start Transcription, waited for the real `POST /api/audio/upload` response, and verified the backend returned `202` with a pending recording id.

Supabase verification:

- Table: `public.call_recordings`
- Recording id: `e790cfff-cd6c-4f4d-b29e-79789882a68a`
- Filename alias: `Call Recording 7 - Alex - John.mp3`
- Final status: `done`
- Error: `null`
- File size: `2389915`

The row initially entered `processing`, then completed as `done` after the local CPU Whisper background task finished.

## Test Cases

| ID | Area | Scenario | Expected Result | Result |
| --- | --- | --- | --- | --- |
| AUD-001 | Auth | Admin Supabase session opens the app | Audio Transcription page is visible | Pass |
| AUD-002 | Upload UI | User selects an MP3 | Selected filename is displayed | Pass |
| AUD-003 | Live Upload | User starts transcription | Browser receives `POST /api/audio/upload` `202` response | Pass |
| AUD-004 | Live Persistence | Upload request completes | Supabase `call_recordings` row is created | Pass |
| AUD-005 | Live Completion | Background transcription finishes | Supabase `call_recordings.status` becomes `done` | Pass |
| AUD-006 | Mocked Transcript UI | Backend returns completed transcript | Transcript/export UI renders | Pass |
| AUD-007 | Auth Error UI | Backend returns `401` | UI shows clear sign-in error | Pass |
| AUD-008 | Backend Contract | Authenticated MP3 upload reaches backend | Backend returns `202` and pending id | Pass |
| AUD-009 | Backend Security | Anonymous MP3 upload reaches backend | Backend returns `401` | Pass |
| AUD-010 | Real Fixtures | Five provided fintech MP3s can be selected in UI tests | Filename displays and mocked transcript renders | Pass |

## Test Stories

### AUD-S01: Alex Uploads A Call Recording

As Alex, an admin QA user, I want to upload an MP3 call recording so that the platform can queue it for transcription.

Acceptance criteria:

- Alex can open the Audio Transcription page.
- Alex can select an MP3 file.
- The selected file name is visible in the UI.
- Clicking Start Transcription sends `POST /api/audio/upload`.
- The backend returns `202` with a recording id and `status = pending`.
- Supabase creates a `call_recordings` row.

Result: Pass

### AUD-S02: John Reviews Transcription Progress

As John, a QA reviewer, I want the uploaded call to move through processing so that I know the transcription job is running.

Acceptance criteria:

- The recording starts as `pending` or `processing`.
- The background transcription task runs locally.
- The recording completes with `status = done`.
- No `error_msg` is stored for the completed recording.

Result: Pass

### AUD-S03: Rocky Handles Missing Auth

As Rocky, a support user, I want clear auth feedback so that users know they must sign in before uploading audio.

Acceptance criteria:

- Anonymous upload returns `401`.
- The UI shows a readable sign-in message.
- The UI does not expose raw Axios/request error text.

Result: Pass

### AUD-S04: Alex Reviews Transcript Output

As Alex, I want completed transcripts to show text and VTT output so that QA teams can review call content.

Acceptance criteria:

- Completed transcript UI renders when the backend returns `done`.
- Text Transcript export option is visible.
- VTT Subtitles export option is visible.
- Plain text transcript can be reviewed in the UI.

Result: Pass

### AUD-S05: John Validates Real MP3 Fixtures

As John, I want the audio page to accept multiple fintech MP3 recordings so that QA can test realistic upload files.

Acceptance criteria:

- Five MP3 fixtures can be selected in browser tests.
- Each selected file appears in the upload card.
- Mocked transcript output renders for each fixture.

Result: Pass

## Sanitized MP3 Fixtures Covered

- `Call Recording 4 - Alex - John.mp3`
- `Call Recording 5 - Alex - John.mp3`
- `Call Recording 7 - Alex - John.mp3`
- `Call Recording 18004251444 - Rocky.mp3`
- `Call Recording 18004255425 - Rocky.mp3`

The live backend upload used the fixture represented in this report as `Call Recording 7 - Alex - John.mp3`.

## Commands Run

Backend audio tests:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai
& 'C:\Users\sg200\AppData\Local\Programs\Python\Python313\python.exe' -m pytest backend\tests\test_audio.py -q
```

Result: `2 passed`

Frontend type-check:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npm.cmd run type-check
```

Result: passed

Mocked frontend audio tests:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npx.cmd playwright test audio.spec.ts --reporter=line
```

Result: `7 passed`

Live headed audio upload test:

```powershell
cd C:\Users\sg200\Desktop\cx-analytics-react\evolvs-ai\frontend
npx.cmd playwright test audio-live.spec.ts --headed --reporter=line
```

Result: `1 passed`

## Jira-Ready Bug

Title: Login form does not reliably transition to authenticated app after valid admin sign-in

Type: Bug

Priority: High

Environment:

- Frontend: `http://127.0.0.1:3000/#`
- Supabase project: `imtqmruynirbejvxvqnj`
- User: `admin@example.com`

Evidence:

- Direct Supabase password grant with `admin@example.com` succeeds.
- Playwright login through the visible UI stayed on the login screen.
- An ambiguous role selector initially clicked the demo sign-in button and produced `Anonymous sign-ins are disabled`.
- Directly seeding a valid Supabase admin session allowed the audio page and live upload to pass.

Acceptance Criteria:

- Filling Email address and Password and clicking the submit button logs in the admin user.
- App transitions to the Audio Transcription page.
- Header shows `admin@example.com`.
- Demo login is either enabled in Supabase Auth or hidden/disabled with clear copy.
- Playwright live test can use the visible login flow instead of session seeding.

Suggested Test:

```ts
await page.goto('http://127.0.0.1:3000/#')
await page.getByLabel('Email address').fill('admin@example.com')
await page.getByLabel('Password').fill('StrongPassword123!')
await page.locator('form button[type="submit"]').click()
await expect(page.getByRole('heading', { name: 'Audio Transcription' })).toBeVisible()
await expect(page.getByText('admin@example.com')).toBeVisible()
```

## MCP Notes

Configured MCP servers are in `.mcp.json`:

- `supabase`: remote Supabase MCP endpoint
- `evolvs-test-runner`: local command `python backend/scripts/playwright_mcp_server.py`

No Jira MCP connector/tool is available in this Codex session, so I could not create or lock an actual Jira issue. This report contains the Jira-ready bug text.

## Model Notes

Audio transcription uses local `faster-whisper`, not an external LLM API key.

Current backend default:

- `WHISPER_MODEL = "base"` in `backend/app/config.py`
- CPU execution: `device="cpu"`
- Quantization: `compute_type="int8"`

No OpenAI/Anthropic/Groq key is used by the current audio transcription path.

## Remaining Risk

- Full transcript completion was not waited for in the live Playwright test because CPU Whisper can take minutes per call recording. The test verifies correct queueing and persistence.
- Supabase Auth leaked-password protection remains disabled in the project advisor.
- QA analytics remains out of scope until its tables and mapping are finalized.
