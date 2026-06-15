import { test, expect } from '@playwright/test';

test('Dashboard loads and shows appropriate state', async ({ page }) => {
  await page.goto('http://localhost:3000', { waitUntil: 'load' });
  await expect(page).toHaveTitle(/Dashboard|Analytics/);

  // Look for the empty‑state message
  const emptyMsg = page.locator('p:has-text("No data available")');

  if (await emptyMsg.count() > 0) {
    await expect(emptyMsg).toBeVisible();
  } else {
    // Fallback: look for a metric label that always exists
    const metricLabel = page.locator('text=Total Audits');
    await expect(metricLabel).toBeVisible();
  }
});

test('Analytics API returns JSON structure', async ({ request }) => {
  const response = await request.get('http://localhost:8000/api/analytics');
  expect(response.ok()).toBeTruthy();
  const data = await response.json();
  expect(data).toHaveProperty('summary');
});
