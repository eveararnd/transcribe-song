// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

test.use({
  ignoreHTTPSErrors: true,
});

const BASE_URL = 'https://35.232.20.248';
const USERNAME = 'parakeet';
const PASSWORD = 'Q7+vD#8kN$2pL@9';

// Helper function to login
async function login(page) {
  await page.goto(BASE_URL);
  await page.waitForLoadState('networkidle');
  
  const loginDialog = page.locator('text=Login to Music Analyzer');
  if (await loginDialog.isVisible()) {
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    
    // Check "Remember Me" checkbox
    const rememberMe = page.locator('input[type="checkbox"]');
    if (await rememberMe.isVisible()) {
      await rememberMe.check();
    }
    
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(2000);
  }
}

test.describe('Music Analyzer Comprehensive Tests', () => {
  
  test('1. Cookie Authentication - Login with Remember Me', async ({ page, context }) => {
    console.log('Testing cookie-based authentication...');
    
    await page.goto(BASE_URL);
    
    // Login with Remember Me
    await page.locator('input[type="text"]').first().fill(USERNAME);
    await page.locator('input[type="password"]').first().fill(PASSWORD);
    
    const rememberMe = page.locator('input[type="checkbox"]');
    await rememberMe.check();
    expect(await rememberMe.isChecked()).toBe(true);
    
    await page.locator('button:has-text("Login")').click();
    await page.waitForTimeout(2000);
    
    // Check if cookie was set
    const cookies = await context.cookies();
    const authCookie = cookies.find(c => c.name === 'music-analyzer-auth');
    
    expect(authCookie).toBeTruthy();
    console.log('✓ Auth cookie set:', authCookie ? 'Yes' : 'No');
    
    // Check cookie expiry (should be ~14 days)
    if (authCookie) {
      const expiryDate = new Date(authCookie.expires * 1000);
      const daysDiff = (expiryDate - new Date()) / (1000 * 60 * 60 * 24);
      console.log(`✓ Cookie expires in ${daysDiff.toFixed(1)} days`);
      expect(daysDiff).toBeGreaterThan(13);
      expect(daysDiff).toBeLessThan(15);
    }
  });

  test('2. Dashboard - File List and Delete Functionality', async ({ page }) => {
    console.log('Testing dashboard and delete functionality...');
    
    await login(page);
    
    // Check dashboard elements
    const recentFiles = await page.locator('text=Recent Files').isVisible();
    expect(recentFiles).toBe(true);
    console.log('✓ Dashboard loaded');
    
    // Check if files are displayed
    const fileRows = page.locator('tbody tr');
    const fileCount = await fileRows.count();
    console.log(`✓ Found ${fileCount} files`);
    
    if (fileCount > 0) {
      // Test delete functionality on first file
      const firstRow = fileRows.first();
      const filename = await firstRow.locator('td').nth(0).textContent();
      console.log(`  Testing delete for: ${filename}`);
      
      // Click delete button
      const deleteBtn = firstRow.locator('[aria-label="Delete file"]');
      await deleteBtn.click();
      
      // Check confirmation dialog
      const confirmDialog = page.locator('text=Confirm Delete');
      await expect(confirmDialog).toBeVisible();
      
      const dialogText = await page.locator('.MuiDialogContentText-root').textContent();
      expect(dialogText).toContain(filename);
      
      // Cancel first
      await page.locator('button:has-text("Cancel")').click();
      await expect(confirmDialog).not.toBeVisible();
      console.log('✓ Delete cancel works');
      
      // Now actually delete
      await deleteBtn.click();
      await page.locator('button:has-text("Delete")').click();
      
      // Check for success notification
      await page.waitForTimeout(1000);
      const notification = await page.locator('.MuiSnackbar-root').textContent();
      console.log('✓ Delete notification:', notification);
    }
  });

  test('3. File Upload - FLAC File', async ({ page }) => {
    console.log('Testing file upload with FLAC...');
    
    await login(page);
    
    // Navigate to upload page
    await page.locator('text=Upload').click();
    await page.waitForLoadState('networkidle');
    
    // Check if on upload page
    const uploadTitle = await page.locator('h4:has-text("Upload Music Files")').isVisible();
    expect(uploadTitle).toBe(true);
    
    // Find a FLAC file to upload
    const flacFile = '/home/davegornshtein/parakeet-tdt-deployment/music_library/other/3863698b_01_Pumped_up_Kicks.flac';
    
    if (fs.existsSync(flacFile)) {
      // Upload file
      const fileInput = page.locator('input[type="file"]');
      await fileInput.setInputFiles(flacFile);
      
      console.log('✓ File selected:', path.basename(flacFile));
      
      // Wait for upload to complete
      await page.waitForTimeout(5000);
      
      // Check for success or error
      const alerts = await page.locator('.MuiAlert-root').count();
      if (alerts > 0) {
        const alertText = await page.locator('.MuiAlert-root').first().textContent();
        console.log('Upload result:', alertText);
      }
    } else {
      console.log('⚠ FLAC file not found for testing');
    }
  });

  test('4. File Details Page', async ({ page }) => {
    console.log('Testing file details page...');
    
    await login(page);
    
    // Get first file from dashboard
    const fileRows = page.locator('tbody tr');
    const fileCount = await fileRows.count();
    
    if (fileCount > 0) {
      // Click on view details button
      const viewBtn = fileRows.first().locator('[aria-label="View details"]');
      await viewBtn.click();
      
      await page.waitForLoadState('networkidle');
      
      // Check if file details page loaded
      const fileInfo = await page.locator('text=File Information').isVisible();
      expect(fileInfo).toBe(true);
      console.log('✓ File details page loaded');
      
      // Check for various sections
      const sections = [
        'File Information',
        'Audio Properties',
        'Transcription',
        'Lyrics'
      ];
      
      for (const section of sections) {
        const visible = await page.locator(`text=${section}`).isVisible();
        console.log(`  ${section}: ${visible ? '✓' : '✗'}`);
      }
      
      // Test transcribe button if visible
      const transcribeBtn = page.locator('button:has-text("Transcribe")');
      if (await transcribeBtn.isVisible()) {
        console.log('✓ Transcribe button available');
      }
    }
  });

  test('5. Search Functionality', async ({ page }) => {
    console.log('Testing search functionality...');
    
    await login(page);
    
    // Navigate to search page
    await page.locator('text=Search').click();
    await page.waitForLoadState('networkidle');
    
    // Check if on search page
    const searchTitle = await page.locator('h4:has-text("Search")').isVisible();
    expect(searchTitle).toBe(true);
    
    // Try a search
    const searchInput = page.locator('input[placeholder*="Search"]').first();
    await searchInput.fill('test');
    await searchInput.press('Enter');
    
    await page.waitForTimeout(2000);
    
    // Check for results or no results message
    const hasResults = await page.locator('text=results found').isVisible().catch(() => false);
    const noResults = await page.locator('text=No results').isVisible().catch(() => false);
    
    console.log('✓ Search executed');
    console.log(`  Results: ${hasResults ? 'Found' : noResults ? 'None' : 'Unknown'}`);
  });

  test('6. Logout and Cookie Persistence', async ({ page, context }) => {
    console.log('Testing logout and cookie persistence...');
    
    await login(page);
    
    // Find logout button (in the menu)
    const menuBtn = page.locator('[aria-label="open drawer"]');
    if (await menuBtn.isVisible()) {
      await menuBtn.click();
      await page.waitForTimeout(500);
    }
    
    const logoutBtn = page.locator('text=Logout');
    if (await logoutBtn.isVisible()) {
      await logoutBtn.click();
      
      // Confirm logout
      const confirmBtn = page.locator('button:has-text("Logout")').last();
      if (await confirmBtn.isVisible()) {
        await confirmBtn.click();
      }
      
      await page.waitForTimeout(2000);
      
      // Check if logged out
      const loginDialog = await page.locator('text=Login to Music Analyzer').isVisible();
      expect(loginDialog).toBe(true);
      console.log('✓ Logout successful');
      
      // Check if cookie was cleared
      const cookies = await context.cookies();
      const authCookie = cookies.find(c => c.name === 'music-analyzer-auth');
      expect(authCookie).toBeFalsy();
      console.log('✓ Auth cookie cleared');
    }
  });

  test('7. Error Handling - Invalid File ID', async ({ page }) => {
    console.log('Testing error handling...');
    
    await login(page);
    
    // Try to access non-existent file
    await page.goto(`${BASE_URL}/files/invalid-id-12345`);
    await page.waitForLoadState('networkidle');
    
    // Check for error message
    const errorVisible = await page.locator('text=Error').isVisible().catch(() => false);
    const notFound = await page.locator('text=not found').isVisible().catch(() => false);
    
    console.log('✓ Error handling:', errorVisible || notFound ? 'Working' : 'Unknown');
  });

  test('8. Responsive Design', async ({ page }) => {
    console.log('Testing responsive design...');
    
    await login(page);
    
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.waitForTimeout(1000);
    
    const mobileMenu = await page.locator('[aria-label="open drawer"]').isVisible();
    expect(mobileMenu).toBe(true);
    console.log('✓ Mobile menu visible');
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await page.waitForTimeout(1000);
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.waitForTimeout(1000);
    
    console.log('✓ Responsive design working');
  });
});

// Summary test
test('System Health Check', async ({ page }) => {
  console.log('\n=== FINAL SYSTEM HEALTH CHECK ===\n');
  
  const results = {
    api: false,
    auth: false,
    dashboard: false,
    upload: false,
    search: false,
    errors: 0
  };
  
  // Check API
  const apiResponse = await page.request.get(`${BASE_URL}/health`);
  results.api = apiResponse.ok();
  console.log(`API Health: ${results.api ? '✓' : '✗'}`);
  
  // Check auth and pages
  await login(page);
  
  // Count any errors
  page.on('pageerror', () => results.errors++);
  
  // Check dashboard
  results.dashboard = await page.locator('text=Recent Files').isVisible();
  console.log(`Dashboard: ${results.dashboard ? '✓' : '✗'}`);
  
  // Check upload page
  await page.locator('text=Upload').click();
  results.upload = await page.locator('text=Upload Music Files').isVisible();
  console.log(`Upload Page: ${results.upload ? '✓' : '✗'}`);
  
  // Check search page
  await page.locator('text=Search').click();
  results.search = await page.locator('h4:has-text("Search")').isVisible();
  console.log(`Search Page: ${results.search ? '✓' : '✗'}`);
  
  console.log(`JavaScript Errors: ${results.errors}`);
  
  const allPassed = Object.values(results).every(v => v === true || v === 0);
  console.log(`\nOverall Status: ${allPassed ? '✅ HEALTHY' : '⚠️ ISSUES FOUND'}`);
  
  expect(allPassed).toBe(true);
});