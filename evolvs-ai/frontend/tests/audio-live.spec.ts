import fs from 'node:fs'
import path from 'node:path'
import { fileURLToPath } from 'node:url'
import { test, expect, type Page } from '@playwright/test'

const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL || 'admin@example.com'
const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD || 'StrongPassword123!'

const LIVE_AUDIO_FILE =
  'C:\\Users\\sg200\\Downloads\\FintechRecordings\\FintechRecordings\\Call Recording 7 - Suraj - Lissabeth Babu.mp3'

function readFrontendEnv() {
  const dirname = path.dirname(fileURLToPath(import.meta.url))
  const envFile = fs.readFileSync(path.resolve(dirname, '..', '.env.local'), 'utf8')
  return Object.fromEntries(
    envFile
      .split(/\r?\n/)
      .map((line) => line.match(/^\s*([^#][^=]*)=(.*)$/))
      .filter((match): match is RegExpMatchArray => Boolean(match))
      .map((match) => [match[1].trim(), match[2].trim()])
  )
}

async function getSupabasePasswordSession() {
  const env = readFrontendEnv()
  const supabaseUrl = env.VITE_SUPABASE_URL
  const anonKey = env.VITE_SUPABASE_ANON_KEY

  const response = await fetch(`${supabaseUrl}/auth/v1/token?grant_type=password`, {
    method: 'POST',
    headers: {
      apikey: anonKey,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email: ADMIN_EMAIL,
      password: ADMIN_PASSWORD,
    }),
  })

  if (!response.ok) {
    throw new Error(`Supabase password auth failed: ${response.status} ${await response.text()}`)
  }

  return {
    projectRef: new URL(supabaseUrl).hostname.split('.')[0],
    session: await response.json(),
  }
}

async function seedSupabaseSession(page: Page) {
  const { projectRef, session } = await getSupabasePasswordSession()
  await page.goto('http://127.0.0.1:3000/#', { waitUntil: 'load' })
  await page.evaluate(
    ({ projectRef, session }) => {
      window.localStorage.setItem(`sb-${projectRef}-auth-token`, JSON.stringify(session))
    },
    { projectRef, session }
  )
  await page.reload({ waitUntil: 'load' })
}

test('live upload queues real MP3 for transcription', async ({ page }) => {
  await seedSupabaseSession(page)
  await expect(page.getByRole('heading', { name: 'Audio Transcription' })).toBeVisible({
    timeout: 15000,
  })

  await page.getByLabel('Select Audio File').setInputFiles(LIVE_AUDIO_FILE)
  await expect(page.getByText('Call Recording 7 - Suraj - Lissabeth Babu.mp3')).toBeVisible()

  const uploadResponsePromise = page.waitForResponse(
    (response) => response.url().includes('/api/audio/upload') && response.request().method() === 'POST',
    { timeout: 60000 }
  )
  await page.getByRole('button', { name: 'Start Transcription' }).click()

  await expect(page.getByText('Processing Audio File')).toBeVisible({ timeout: 15000 })
  await expect(page.getByText('Our AI engine is transcribing your file')).toBeVisible()

  const uploadResponse = await uploadResponsePromise
  expect(uploadResponse.status()).toBe(202)
  const uploadBody = await uploadResponse.json()
  expect(uploadBody).toEqual(expect.objectContaining({ id: expect.any(String), status: 'pending' }))
})
