// @ts-check
const { test, expect } = require('@playwright/test');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

test('Check Current System State', async ({ page }) => {
  console.log('=== CHECKING CURRENT STATE ===\n');
  
  // 1. Check login
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  const loginDialog = page.locator('text=Login to Music Analyzer');
  if (await loginDialog.isVisible()) {
    console.log('✓ Login dialog visible');
    
    // Check for Remember Me checkbox
    const rememberMe = page.locator('input[type="checkbox"]');
    const hasRememberMe = await rememberMe.isVisible();
    console.log(`Remember Me checkbox: ${hasRememberMe ? '✓' : '✗'}`);
    
    // Login
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    if (hasRememberMe) {
      await rememberMe.check();
    }
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(3000);
  }
  
  // 2. Check for errors
  const errors = await page.locator('text=Error').count();
  const unexpectedErrors = await page.locator('text=Unexpected Application Error').count();
  console.log(`\nErrors found: ${errors}`);
  console.log(`Unexpected errors: ${unexpectedErrors}`);
  
  // 3. Check dashboard
  const dashboardElements = {
    'Recent Files': await page.locator('text=Recent Files').isVisible(),
    'File table': await page.locator('table').isVisible(),
    'Delete buttons': await page.locator('[aria-label="Delete file"]').count(),
    'View buttons': await page.locator('[aria-label="View details"]').count(),
  };
  
  console.log('\nDashboard elements:');
  for (const [element, value] of Object.entries(dashboardElements)) {
    console.log(`  ${element}: ${value}`);
  }
  
  // 4. Check file data
  const fileRows = page.locator('tbody tr');
  const fileCount = await fileRows.count();
  console.log(`\nFiles in table: ${fileCount}`);
  
  if (fileCount > 0) {
    // Get first file info
    const firstRow = fileRows.first();
    const cells = await firstRow.locator('td').allTextContents();
    console.log('First file data:', cells);
  }
  
  // 5. Take screenshot
  await page.screenshot({ path: 'tests/e2e/screenshots/current-state.png', fullPage: true });
  console.log('\nScreenshot saved to: tests/e2e/screenshots/current-state.png');
});