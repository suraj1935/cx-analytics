import { test, expect } from '@playwright/test'

test('unauthenticated users see the login screen', async ({ page }) => {
  await page.goto('http://localhost:3000', { waitUntil: 'load' })

  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible()
  await expect(page.getByLabel('Email address')).toBeVisible()
  await expect(page.getByLabel('Password')).toBeVisible()
})

test('protected analytics API rejects anonymous requests', async ({ request }) => {
  const response = await request.get('http://localhost:8000/api/analytics')

  expect(response.status()).toBe(401)
  await expect(response).not.toBeOK()
})

test('health API stays public', async ({ request }) => {
  const response = await request.get('http://localhost:8000/api/health')

  expect(response.ok()).toBeTruthy()
  const data = await response.json()
  expect(data).toHaveProperty('status')
})
