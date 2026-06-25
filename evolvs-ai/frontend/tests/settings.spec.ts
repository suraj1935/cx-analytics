import { expect, test } from '@playwright/test'

test('updates original audio retention setting', async ({ page }) => {
  let retained = true
  await page.route('**/api/settings', async (route) => {
    if (route.request().method() === 'PUT') {
      retained = (await route.request().postDataJSON()).retain_original_audio
    }
    await route.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({
      retain_original_audio: retained, llm_model: 'qwen3:4b', embedding_model: 'nomic-embed-text',
    })})
  })
  await page.goto('http://127.0.0.1:3000/?e2e=1', {waitUntil: 'load'})
  await page.getByRole('button', {name: 'Settings'}).click()
  const toggle = page.getByRole('switch', {name: 'Retain original audio'})
  await expect(toggle).toBeChecked()
  await toggle.click()
  await expect(toggle).not.toBeChecked()
  await page.getByRole('button', {name: 'Save settings'}).click()
  await expect(page.getByText('Settings saved')).toBeVisible()
  expect(retained).toBe(false)
})

test('shows retained original audio download after transcription', async ({ page }) => {
  await page.route('**/api/audio/upload', (route) => route.fulfill({status: 202, contentType: 'application/json', body: JSON.stringify({id: 'retained', status: 'pending'})}))
  await page.route('**/api/audio/retained/file', (route) => route.fulfill({status: 200, contentType: 'audio/mpeg', body: 'audio'}))
  await page.route('**/api/audio/retained', (route) => route.fulfill({status: 200, contentType: 'application/json', body: JSON.stringify({
    id: 'retained', file_name: 'sample.mp3', duration: 2, status: 'done', transcript: 'Test transcript',
    vtt_content: 'WEBVTT\\n\\n00:00:00.000 --> 00:00:02.000\\nTest transcript\\n', created_at: '2026-06-24T00:00:00Z', original_file_retained: true,
  })}))
  await page.goto('http://127.0.0.1:3000/?e2e=1', {waitUntil: 'load'})
  await page.getByLabel('Select Audio File').setInputFiles('tests/fixtures/sample.mp3')
  await page.getByRole('button', {name: 'Start Transcription'}).click()
  await expect(page.getByText('Original Audio')).toBeVisible()
})
