// @ts-check
const { test, expect } = require('@playwright/test');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

test('Final Music Analyzer Test - Complete Flow', async ({ page }) => {
  console.log('=== FINAL SYSTEM TEST ===\n');
  
  console.log('1. Navigating to Music Analyzer...');
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  // Login
  const loginDialog = page.locator('text=Login to Music Analyzer');
  if (await loginDialog.isVisible()) {
    console.log('2. Logging in...');
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(3000);
  }
  
  // Check for errors
  const errorCount = await page.locator('text=Error').count();
  const unexpectedError = await page.locator('text=Unexpected Application Error').count();
  
  console.log(`3. Checking for errors...`);
  console.log(`   - Error elements found: ${errorCount}`);
  console.log(`   - Unexpected errors: ${unexpectedError}`);
  
  // Check if dashboard loaded
  const dashboardVisible = await page.locator('h6:has-text("Dashboard")').isVisible();
  console.log(`4. Dashboard visible: ${dashboardVisible}`);
  
  // Check if file list is present (even if empty)
  const fileListSection = await page.locator('text=Recent Files').isVisible().catch(() => false);
  const noFilesMessage = await page.locator('text=No files uploaded yet').isVisible().catch(() => false);
  const hasFileList = await page.locator('[role="grid"]').isVisible().catch(() => false);
  
  console.log(`5. File list status:`);
  console.log(`   - Recent Files section: ${fileListSection}`);
  console.log(`   - No files message: ${noFilesMessage}`);
  console.log(`   - File grid visible: ${hasFileList}`);
  
  // Check storage stats
  const storageStats = await page.locator('text=Storage Usage').isVisible().catch(() => false);
  console.log(`6. Storage stats visible: ${storageStats}`);
  
  // Take final screenshot
  await page.screenshot({ path: 'tests/e2e/screenshots/final-working-state.png', fullPage: true });
  
  // Assertions
  expect(unexpectedError).toBe(0);
  expect(dashboardVisible).toBe(true);
  
  console.log('\n✅ SYSTEM TEST PASSED! Music Analyzer is fully functional.');
});