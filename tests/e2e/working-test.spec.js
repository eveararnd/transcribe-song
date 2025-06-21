// @ts-check
const { test, expect } = require('@playwright/test');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

test('Music Analyzer - Working System Test', async ({ page }) => {
  console.log('=== MUSIC ANALYZER SYSTEM TEST ===\n');
  
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  // Login if needed
  const loginDialog = page.locator('text=Login to Music Analyzer');
  if (await loginDialog.isVisible()) {
    console.log('✓ Login dialog appeared');
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(3000);
    console.log('✓ Login completed');
  }
  
  // Check what's visible after login
  console.log('\nChecking page content...');
  
  const musicAnalyzerHeader = await page.locator('text=Music Analyzer').count();
  const recentFiles = await page.locator('text=Recent Files').count();
  const storageUsage = await page.locator('text=Storage Usage').count();
  const totalFiles = await page.locator('text=Total Files').count();
  
  console.log(`- "Music Analyzer" text found: ${musicAnalyzerHeader} times`);
  console.log(`- "Recent Files" section: ${recentFiles > 0 ? '✓' : '✗'}`);
  console.log(`- "Storage Usage" section: ${storageUsage > 0 ? '✓' : '✗'}`);
  console.log(`- "Total Files" text: ${totalFiles > 0 ? '✓' : '✗'}`);
  
  // Check for any errors
  const errors = await page.locator('text=Error').count();
  const unexpectedErrors = await page.locator('text=Unexpected Application Error').count();
  console.log(`\nError check:`);
  console.log(`- Regular errors: ${errors}`);
  console.log(`- Unexpected errors: ${unexpectedErrors}`);
  
  // Take screenshot
  await page.screenshot({ path: 'tests/e2e/screenshots/working-system.png', fullPage: true });
  
  // Success criteria
  const hasContent = musicAnalyzerHeader > 0 && recentFiles > 0;
  const noErrors = unexpectedErrors === 0;
  
  if (hasContent && noErrors) {
    console.log('\n✅ SYSTEM TEST PASSED!');
    console.log('Music Analyzer is working correctly.');
  } else {
    console.log('\n❌ Test failed - check screenshot');
  }
  
  expect(noErrors).toBe(true);
  expect(hasContent).toBe(true);
});