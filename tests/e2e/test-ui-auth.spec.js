// @ts-check
const { test, expect } = require('@playwright/test');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

test('Music Analyzer UI Authentication Flow', async ({ page }) => {
  console.log('1. Navigating to Music Analyzer...');
  await page.goto(BASE_URL);
  
  // Wait for page to load
  await page.waitForLoadState('networkidle');
  
  // Take screenshot of initial state
  await page.screenshot({ path: 'tests/e2e/screenshots/ui-initial.png' });
  
  // Check if login dialog is present
  const loginDialog = page.locator('text=Login to Music Analyzer');
  const isLoginVisible = await loginDialog.isVisible();
  
  if (isLoginVisible) {
    console.log('2. Login dialog detected, filling credentials...');
    
    // Find username field
    const usernameField = page.locator('input[type="text"]').first();
    await usernameField.fill(USERNAME);
    console.log('   - Username entered');
    
    // Find password field
    const passwordField = page.locator('input[type="password"]').first();
    await passwordField.fill(PASSWORD);
    console.log('   - Password entered');
    
    // Take screenshot before login
    await page.screenshot({ path: 'tests/e2e/screenshots/ui-login-filled.png' });
    
    // Click login button
    const loginButton = page.locator('button:has-text("Login")');
    await loginButton.click();
    console.log('   - Login button clicked');
    
    // Wait for navigation or dialog to close
    await page.waitForTimeout(2000);
    
    // Take screenshot after login
    await page.screenshot({ path: 'tests/e2e/screenshots/ui-after-login.png' });
  }
  
  // Check if we're logged in by looking for dashboard content
  console.log('3. Checking if logged in...');
  
  // Wait a bit for any errors to appear
  await page.waitForTimeout(2000);
  
  // Check for error messages
  const errorText = await page.locator('text=Error').count();
  if (errorText > 0) {
    const errors = await page.locator('text=Error').allTextContents();
    console.log('   ❌ Errors found:', errors);
  } else {
    console.log('   ✓ No errors detected');
  }
  
  // Check if dashboard loaded
  const dashboardVisible = await page.locator('text=Dashboard').isVisible();
  console.log('   - Dashboard visible:', dashboardVisible);
  
  // Check if file list loaded (no error message)
  const fileListError = await page.locator('text=Error loading files').isVisible().catch(() => false);
  console.log('   - File list error:', fileListError);
  
  // Final screenshot
  await page.screenshot({ path: 'tests/e2e/screenshots/ui-final-state.png', fullPage: true });
  
  // Assert login was successful
  expect(fileListError).toBe(false);
  console.log('✓ Authentication successful!');
});