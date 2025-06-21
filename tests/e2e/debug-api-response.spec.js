// @ts-check
const { test, expect } = require('@playwright/test');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

test('Debug API responses', async ({ page }) => {
  // Intercept API responses
  const apiResponses = {};
  
  page.on('response', async response => {
    const url = response.url();
    if (url.includes('/api/')) {
      const path = new URL(url).pathname;
      try {
        const body = await response.json();
        apiResponses[path] = {
          status: response.status(),
          body: body
        };
        console.log(`API Response ${path}:`, JSON.stringify(body, null, 2));
      } catch (e) {
        // Not JSON
      }
    }
  });
  
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  // Login if needed
  const loginDialog = page.locator('text=Login to Music Analyzer');
  if (await loginDialog.isVisible()) {
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(3000);
  }
  
  // Log all collected responses
  console.log('\n=== All API Responses ===');
  for (const [path, data] of Object.entries(apiResponses)) {
    console.log(`\n${path} (${data.status}):`);
    console.log(JSON.stringify(data.body, null, 2));
  }
});