// @ts-check
const { test, expect } = require('@playwright/test');

// Configure to ignore SSL certificate errors
test.use({
  ignoreHTTPSErrors: true,
  // Slow down actions to see what's happening
  // slowMo: 500,
});

const BASE_URL = 'https://35.232.20.248';
const API_USERNAME = 'parakeet';
const API_PASSWORD = 'Q7+vD#8kN$2pL@9';

test.describe('Music Analyzer End-to-End Tests', () => {
  
  test('1. Homepage loads without authentication', async ({ page }) => {
    console.log('Testing homepage access...');
    await page.goto(BASE_URL);
    
    // Check if the page loaded
    await expect(page).toHaveTitle(/Music Analyzer/);
    
    // Check for main UI elements
    const heading = page.locator('h1').first();
    await expect(heading).toBeVisible();
    
    // Take screenshot
    await page.screenshot({ path: 'tests/e2e/screenshots/homepage.png' });
    console.log('✓ Homepage loaded successfully');
  });

  test('2. API health endpoint works', async ({ request }) => {
    console.log('Testing API health endpoint...');
    const response = await request.get(`${BASE_URL}/health`);
    expect(response.ok()).toBeTruthy();
    
    const data = await response.json();
    expect(data.status).toBe('healthy');
    console.log('✓ API health check passed:', data);
  });

  test('3. Protected API endpoint requires authentication', async ({ request }) => {
    console.log('Testing protected API endpoint without auth...');
    
    // Test without auth - should fail
    const responseNoAuth = await request.get(`${BASE_URL}/api/v2/catalog`);
    expect(responseNoAuth.status()).toBe(401);
    console.log('✓ Protected endpoint correctly returns 401 without auth');
    
    // Test with auth - should work
    const responseWithAuth = await request.get(`${BASE_URL}/api/v2/catalog`, {
      headers: {
        'Authorization': 'Basic ' + Buffer.from(`${API_USERNAME}:${API_PASSWORD}`).toString('base64')
      }
    });
    expect(responseWithAuth.ok()).toBeTruthy();
    console.log('✓ Protected endpoint works with correct auth');
  });

  test('4. Frontend authentication flow', async ({ page, context }) => {
    console.log('Testing frontend authentication flow...');
    
    // Set up request interception to log API calls
    page.on('request', request => {
      if (request.url().includes('/api/')) {
        console.log('>> API Request:', request.method(), request.url());
      }
    });
    
    page.on('response', response => {
      if (response.url().includes('/api/')) {
        console.log('<< API Response:', response.status(), response.url());
      }
    });
    
    // Go to homepage
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Take screenshot of initial state
    await page.screenshot({ path: 'tests/e2e/screenshots/initial-state.png' });
    
    // Look for authentication form or error message
    const authError = page.locator('text=Error loading files');
    const isAuthError = await authError.isVisible().catch(() => false);
    
    if (isAuthError) {
      console.log('! Found authentication error on page load');
      await page.screenshot({ path: 'tests/e2e/screenshots/auth-error.png' });
      
      // Look for login form
      const usernameInput = page.locator('input[type="text"], input[name="username"], input[placeholder*="username" i]').first();
      const passwordInput = page.locator('input[type="password"], input[name="password"], input[placeholder*="password" i]').first();
      
      if (await usernameInput.isVisible() && await passwordInput.isVisible()) {
        console.log('Found login form, attempting to login...');
        
        await usernameInput.fill(API_USERNAME);
        await passwordInput.fill(API_PASSWORD);
        
        // Look for submit button
        const submitButton = page.locator('button[type="submit"], button:has-text("Login"), button:has-text("Sign in")').first();
        if (await submitButton.isVisible()) {
          await submitButton.click();
          await page.waitForLoadState('networkidle');
          await page.screenshot({ path: 'tests/e2e/screenshots/after-login.png' });
        }
      }
    }
    
    // Check final state
    const finalError = await page.locator('text=Error').isVisible().catch(() => false);
    if (finalError) {
      console.log('! Still seeing error after authentication attempt');
      const errorText = await page.locator('text=Error').textContent();
      console.log('Error text:', errorText);
    }
  });

  test('5. Check console errors and network failures', async ({ page }) => {
    console.log('Checking for console errors and network issues...');
    
    const consoleMessages = [];
    const networkErrors = [];
    
    // Collect console messages
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleMessages.push({
          type: msg.type(),
          text: msg.text(),
          location: msg.location()
        });
      }
    });
    
    // Collect failed requests
    page.on('requestfailed', request => {
      networkErrors.push({
        url: request.url(),
        failure: request.failure()
      });
    });
    
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    // Wait a bit to collect any async errors
    await page.waitForTimeout(3000);
    
    console.log('Console errors:', consoleMessages);
    console.log('Network errors:', networkErrors);
    
    // Check what API calls are being made
    const apiCalls = await page.evaluate(() => {
      const performanceEntries = performance.getEntriesByType('resource');
      return performanceEntries
        .filter(entry => entry.name.includes('/api/'))
        .map(entry => ({
          url: entry.name,
          duration: entry.duration,
          status: entry.responseStatus || 'unknown'
        }));
    });
    
    console.log('API calls made:', apiCalls);
  });

  test('6. Test monitoring dashboard access', async ({ page, context }) => {
    console.log('Testing monitoring dashboard...');
    
    // Create context with HTTP credentials
    const authContext = await context.browser().newContext({
      httpCredentials: {
        username: 'monitor',
        password: 'Monitor2025!'
      },
      ignoreHTTPSErrors: true
    });
    
    const authPage = await authContext.newPage();
    await authPage.goto(`${BASE_URL}/monitor/dashboard.html`);
    
    // Check if dashboard loaded
    await expect(authPage).toHaveTitle(/Service Dashboard/);
    await authPage.screenshot({ path: 'tests/e2e/screenshots/monitoring-dashboard.png' });
    console.log('✓ Monitoring dashboard accessible with auth');
    
    await authContext.close();
  });

  test('7. Debug frontend authentication issue', async ({ page }) => {
    console.log('Debugging authentication issue in detail...');
    
    // Enable verbose logging
    await page.route('**/*', route => {
      const request = route.request();
      if (request.url().includes('/api/')) {
        console.log(`API Call: ${request.method()} ${request.url()}`);
        console.log('Headers:', request.headers());
      }
      route.continue();
    });
    
    await page.goto(BASE_URL);
    
    // Check localStorage and sessionStorage
    const storage = await page.evaluate(() => {
      return {
        localStorage: { ...localStorage },
        sessionStorage: { ...sessionStorage }
      };
    });
    console.log('Browser storage:', storage);
    
    // Check for any authentication-related elements
    const authElements = await page.evaluate(() => {
      const elements = [];
      
      // Check for auth-related inputs
      document.querySelectorAll('input').forEach(input => {
        if (input.type === 'password' || 
            input.name?.toLowerCase().includes('user') || 
            input.name?.toLowerCase().includes('pass') ||
            input.placeholder?.toLowerCase().includes('user') ||
            input.placeholder?.toLowerCase().includes('pass')) {
          elements.push({
            tag: 'input',
            type: input.type,
            name: input.name,
            placeholder: input.placeholder,
            id: input.id
          });
        }
      });
      
      // Check for error messages
      document.querySelectorAll('*').forEach(el => {
        if (el.textContent?.includes('Error') || 
            el.textContent?.includes('authentication') ||
            el.textContent?.includes('401') ||
            el.textContent?.includes('unauthorized')) {
          elements.push({
            tag: el.tagName,
            text: el.textContent.substring(0, 100)
          });
        }
      });
      
      return elements;
    });
    
    console.log('Auth-related elements found:', authElements);
    
    // Get the actual HTML to see what's being rendered
    const bodyHTML = await page.evaluate(() => document.body.innerHTML);
    await require('fs').promises.writeFile('tests/e2e/page-source.html', bodyHTML);
    console.log('Page source saved to tests/e2e/page-source.html');
  });
});

// Run the tests
if (require.main === module) {
  const { execSync } = require('child_process');
  console.log('Running Playwright tests...\n');
  try {
    execSync('npx playwright test tests/e2e/music-analyzer.spec.js --reporter=list', { stdio: 'inherit' });
  } catch (error) {
    console.error('Tests failed');
    process.exit(1);
  }
}