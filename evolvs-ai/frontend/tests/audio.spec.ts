import { test, expect } from '@playwright/test'
import path from 'path'
import { fileURLToPath } from 'url'

const testDir = path.dirname(fileURLToPath(import.meta.url))
const realAudioFiles = [
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call Recording 4 - Suraj - Lissabeth Babu.mp3',
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call Recording 5 - Suraj - Lissabeth Babu.mp3',
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call Recording 7 - Suraj - Lissabeth Babu.mp3',
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call recording 18004251444_260527_150102 - Deepak Yadav.mp3',
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call recording 18004255425_260527_141132 - Deepak Yadav.mp3',
]

async function openAudioPage(page: import('@playwright/test').Page) {
  await page.goto('http://127.0.0.1:3000/?e2e=1#', { waitUntil: 'load' })
  await expect(page.getByRole('heading', { name: 'Audio Transcription' })).toBeVisible({ timeout: 15000 })
}

test.describe('Audio transcription', () => {
  test('uploads an audio file and renders completed transcript', async ({ page }) => {
    await page.route('**/api/audio/upload', async (route) => {
      await route.fulfill({
        status: 202,
        contentType: 'application/json',
        body: JSON.stringify({ id: 'test-recording', status: 'pending' }),
      })
    })

    await page.route('**/api/audio/test-recording', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: 'test-recording',
          file_name: 'sample.mp3',
          duration: 2.4,
          status: 'done',
          error_msg: null,
          transcript: 'Hello from the audio smoke test.',
          vtt_content: 'WEBVTT\\n\\n00:00:00.000 --> 00:00:02.400\\nHello from the audio smoke test.\\n',
          created_at: '2026-06-19T00:00:00Z',
        }),
      })
    })

    await openAudioPage(page)

    const sampleAudio = path.resolve(testDir, 'fixtures', 'sample.mp3')
    await page.getByLabel('Select Audio File').setInputFiles(sampleAudio)

    await expect(page.getByText('sample.mp3')).toBeVisible()
    await page.getByRole('button', { name: 'Start Transcription' }).click()

    await expect(page.getByText('Text Transcript')).toBeVisible()
    await expect(page.getByRole('button', { name: 'VTT Subtitles WebVTT format with timings' })).toBeVisible()
    await page.getByRole('button', { name: 'Plain Text', exact: true }).click()
    await expect(page.getByText('Hello from the audio smoke test.')).toBeVisible()
  })

  test('shows a useful auth error when audio upload is unauthorized', async ({ page }) => {
    await page.route('**/api/audio/upload', async (route) => {
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Missing bearer token' }),
      })
    })

    await openAudioPage(page)

    const sampleAudio = path.resolve(testDir, 'fixtures', 'sample.mp3')
    await page.getByLabel('Select Audio File').setInputFiles(sampleAudio)
    await page.getByRole('button', { name: 'Start Transcription' }).click()

    await expect(page.getByText('Your session expired. Please sign in again.')).toBeVisible()
  })

  for (const audioFile of realAudioFiles) {
    const fileName = path.basename(audioFile)

    test(`accepts real MP3 fixture: ${fileName}`, async ({ page }) => {
      await page.route('**/api/audio/upload', async (route) => {
        await route.fulfill({
          status: 202,
          contentType: 'application/json',
          body: JSON.stringify({ id: 'real-file-recording', status: 'pending' }),
        })
      })

      await page.route('**/api/audio/real-file-recording', async (route) => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'real-file-recording',
            file_name: fileName,
            duration: 12.5,
            status: 'done',
            error_msg: null,
            transcript: `Mock transcript for ${fileName}`,
            vtt_content: `WEBVTT\\n\\n00:00:00.000 --> 00:00:12.500\\nMock transcript for ${fileName}\\n`,
            created_at: '2026-06-19T00:00:00Z',
          }),
        })
      })

      await openAudioPage(page)
      await page.getByLabel('Select Audio File').setInputFiles(audioFile)

      await expect(page.getByText(fileName)).toBeVisible()
      await page.getByRole('button', { name: 'Start Transcription' }).click()
      await expect(page.getByText(fileName)).toBeVisible()
      await page.getByRole('button', { name: 'Plain Text', exact: true }).click()
      await expect(page.getByText(`Mock transcript for ${fileName}`)).toBeVisible()
    })
  }
})
