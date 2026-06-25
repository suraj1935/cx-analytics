import { test, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const testDir = path.dirname(fileURLToPath(import.meta.url))

const analyticsPayload = {
  summary: {
    total_audits: 2500,
    completion_rate: 92.4,
    average_final_score: 84.7,
  },
  audits: Array.from({ length: 250 }, (_, index) => ({
    audit_id: `AUD-${String(index + 1).padStart(5, '0')}`,
    project: index % 2 === 0 ? 'Voice QA' : 'Chat QA',
    status: index % 5 === 0 ? 'Open' : 'Closed',
    final_score: 70 + (index % 30),
    system_score: 72 + (index % 25),
    created_at: `2026-06-${String((index % 20) + 1).padStart(2, '0')}`,
  })),
  agents: Array.from({ length: 25 }, (_, index) => ({
    agent: `Agent ${index + 1}`,
    audits: 100 + index,
    average_final_score: 72 + (index % 24),
    completion_rate: 0.82 + (index % 10) / 100,
    sla_adherence: 88 + (index % 9),
    dispute_rate: 0.02 + (index % 5) / 100,
  })),
  parameters: Array.from({ length: 40 }, (_, index) => ({
    criterion_key: `P-${index + 1}`,
    label: `Compliance Parameter ${index + 1}`,
    category: index % 2 === 0 ? 'Process' : 'Customer Experience',
    pass_rate: 0.65 + (index % 30) / 100,
    failures: index * 2,
    average_score: 7 + (index % 3),
  })),
  reasons: [],
}

async function openAudioPage(page: import('@playwright/test').Page) {
  const start = Date.now()
  await page.goto('http://127.0.0.1:3000/?e2e=1#', { waitUntil: 'domcontentloaded' })
  await expect(page.getByRole('heading', { name: 'Audio Transcription' })).toBeVisible({ timeout: 15000 })
  return Date.now() - start
}

async function openDashboard(page: import('@playwright/test').Page) {
  await page.route('**/api/analytics', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 200))
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(analyticsPayload),
    })
  })

  const start = Date.now()
  await page.goto('http://127.0.0.1:3000/?e2e=1#', { waitUntil: 'domcontentloaded' })
  await page.getByRole('button', { name: 'Dashboard' }).click()
  await expect(page.getByRole('heading', { name: 'QA Analytics' })).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Agent Performance')).toBeVisible({ timeout: 15000 })
  return Date.now() - start
}

test.describe('Performance smoke checks', () => {
  test('audio page becomes usable within the target budget', async ({ page }) => {
    const loadMs = await openAudioPage(page)

    console.log(`[performance] audio_page_usable_ms=${loadMs}`)
    expect(loadMs, `Audio page interactive load was ${loadMs}ms`).toBeLessThan(3000)
  })

  test('audio upload flow renders completed transcript within mocked service budget', async ({ page }) => {
    await page.route('**/api/audio/upload', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 150))
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'perf-recording', status: 'pending' }),
      })
    })

    await page.route('**/api/audio/perf-recording', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 150))
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'perf-recording',
          file_name: 'sample.mp3',
          duration: 2.4,
          status: 'done',
          error_msg: null,
          transcript: 'Performance smoke transcript.',
          vtt_content: 'WEBVTT\n\n00:00:00.000 --> 00:00:02.400\nPerformance smoke transcript.\n',
          created_at: '2026-06-19T00:00:00Z',
        }),
      })
    })

    await openAudioPage(page)

    const start = Date.now()
    await page.getByLabel('Select Audio File').setInputFiles(path.resolve(testDir, 'fixtures', 'sample.mp3'))
    await page.getByRole('button', { name: 'Start Transcription' }).click()
    await expect(page.getByText('Performance smoke transcript.')).toBeVisible({ timeout: 10000 })
    const flowMs = Date.now() - start

    console.log(`[performance] mocked_audio_to_transcript_ms=${flowMs}`)
    expect(flowMs, `Mocked upload-to-transcript flow was ${flowMs}ms`).toBeLessThan(6000)
  })

  test('analytics dashboard renders audit reporting dataset within the target budget', async ({ page }) => {
    const loadMs = await openDashboard(page)

    await expect(page.getByText('2500')).toBeVisible()
    await expect(page.getByText('Compliance Parameter 1', { exact: true })).toBeVisible()
    console.log(`[performance] dashboard_reporting_load_ms=${loadMs}`)
    expect(loadMs, `Dashboard mocked analytics load was ${loadMs}ms`).toBeLessThan(4000)
  })

  test('dashboard drilldown switches without visible delay on a larger audit dataset', async ({ page }) => {
    await openDashboard(page)

    const start = Date.now()
    await page.getByRole('button', { name: 'Detailed Dataset Drilldown' }).click()
    await expect(page.getByText('AUD-00001')).toBeVisible({ timeout: 5000 })
    const switchMs = Date.now() - start

    console.log(`[performance] dashboard_drilldown_switch_ms=${switchMs}`)
    expect(switchMs, `Drilldown tab switch was ${switchMs}ms`).toBeLessThan(1000)
  })
})
