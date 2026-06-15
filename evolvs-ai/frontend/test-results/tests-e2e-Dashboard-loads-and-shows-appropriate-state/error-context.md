# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests\e2e.spec.ts >> Dashboard loads and shows appropriate state
- Location: tests\e2e.spec.ts:3:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: locator('text=Summary Metrics')
Expected: visible
Timeout: 5000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" with timeout 5000ms
  - waiting for locator('text=Summary Metrics')

```

```yaml
- img
- text: EvolvS AI
- heading "Welcome back" [level=2]
- paragraph: Enter your credentials to access the QA analytics suite
- text: Email address
- img
- textbox "Email address":
  - /placeholder: name@company.com
- text: Password
- img
- textbox "Password":
  - /placeholder: ••••••••
- checkbox "Remember me"
- text: Remember me
- link "Forgot password?":
  - /url: "#"
- button "Sign In":
  - text: Sign In
  - img
- text: Or quickly check out
- button "Access Demo Mode":
  - img
  - text: Access Demo Mode
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('Dashboard loads and shows appropriate state', async ({ page }) => {
  4  |   await page.goto('http://localhost:3000', { waitUntil: 'load' });
  5  |   await expect(page).toHaveTitle(/Dashboard|Analytics/);
  6  | 
  7  |   // Look for the empty‑state message
  8  |   const emptyMsg = page.locator('p:has-text("No data available")');
  9  | 
  10 |   if (await emptyMsg.count() > 0) {
  11 |     await expect(emptyMsg).toBeVisible();
  12 |   } else {
  13 |     // Fallback: ensure the summary metrics section is visible
  14 |     const summary = page.locator('text=Summary Metrics');
> 15 |     await expect(summary).toBeVisible();
     |                           ^ Error: expect(locator).toBeVisible() failed
  16 |   }
  17 | });
  18 | 
  19 | test('Analytics API returns JSON structure', async ({ request }) => {
  20 |   const response = await request.get('http://localhost:8000/api/analytics');
  21 |   expect(response.ok()).toBeTruthy();
  22 |   const data = await response.json();
  23 |   expect(data).toHaveProperty('summary');
  24 | });
  25 | 
```