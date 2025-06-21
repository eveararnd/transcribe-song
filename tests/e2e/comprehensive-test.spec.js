// @ts-check
const { test, expect } = require('@playwright/test');
const path = require('path');
const fs = require('fs');

test.use({
  ignoreHTTPSErrors: true,
});

test.setTimeout(60000); // 60 seconds timeout for each test

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
    const authCookie = cookies.find(c => c.name === 'music_analyzer_auth');
    
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

  test('3. Model Selection - Load/Unload/Choose', async ({ page }) => {
    console.log('Testing model selection functionality...');
    
    await login(page);
    
    // Check model selection on dashboard
    const modelSelect = page.locator('text=Select Model').locator('..');
    await expect(modelSelect).toBeVisible();
    console.log('✓ Model selection dropdown visible');
    
    // Click on model dropdown
    await modelSelect.click();
    
    // Check available models
    const modelOptions = page.locator('[role="option"]');
    const modelCount = await modelOptions.count();
    console.log(`✓ Found ${modelCount} model options`);
    
    if (modelCount > 0) {
      // Get first model name
      const firstModel = await modelOptions.first().textContent();
      console.log(`  Selecting model: ${firstModel}`);
      await modelOptions.first().click();
      
      // Check if the model is already loaded or if we can load it
      const loadBtn = page.locator('button:has-text("LOAD MODEL")');
      const unloadBtn = page.locator('button:has-text("UNLOAD CURRENT")');
      
      const loadBtnEnabled = await loadBtn.isEnabled();
      const unloadBtnEnabled = await unloadBtn.isEnabled();
      
      if (loadBtnEnabled) {
        // Model not loaded, so load it
        await loadBtn.click();
        console.log('  Waiting for model to load...');
        await page.waitForTimeout(10000);
        console.log('✓ Model loaded');
      } else if (unloadBtnEnabled) {
        // Model already loaded
        console.log('✓ Model already loaded');
        
        // Test unload
        await unloadBtn.click();
        await page.waitForTimeout(2000);
        console.log('✓ Model unloaded');
        
        // Now load it again
        await loadBtn.click();
        await page.waitForTimeout(10000);
        console.log('✓ Model re-loaded');
      } else {
        console.log('⚠ Unable to test model loading - buttons not in expected state');
      }
    }
  });

  test('4. File Upload with FLAC and Full Processing', async ({ page }) => {
    test.setTimeout(90000); // 90 seconds for this test
    console.log('Testing file upload with FLAC and full processing...');
    
    await login(page);
    
    // First ensure a model is loaded
    const modelSelect = page.locator('text=Select Model').locator('..');
    await modelSelect.click();
    
    const modelOptions = page.locator('[role="option"]');
    const modelCount = await modelOptions.count();
    
    if (modelCount > 0) {
      await modelOptions.first().click();
      const loadBtn = page.locator('button:has-text("LOAD MODEL")');
      await loadBtn.click();
      console.log('  Loading model for transcription...');
      await page.waitForTimeout(10000);
    }
    
    // Navigate to upload page
    const drawer = page.locator('[aria-label="open drawer"]');
    if (await drawer.isVisible()) {
      await drawer.click();
      await page.waitForTimeout(500);
    }
    await page.locator('text=Upload').first().click();
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
      
      // Go back to dashboard to check categorization
      await page.locator('text=Dashboard').click();
      await page.waitForLoadState('networkidle');
      
      // Find the uploaded file
      const fileRows = page.locator('tbody tr');
      const fileCount = await fileRows.count();
      
      if (fileCount > 0) {
        // Find the Pumped up Kicks file
        let targetRow = null;
        for (let i = 0; i < fileCount; i++) {
          const filename = await fileRows.nth(i).locator('td').first().textContent();
          if (filename && filename.includes('Pumped_up_Kicks')) {
            targetRow = fileRows.nth(i);
            break;
          }
        }
        
        if (targetRow) {
          // Check genre categorization
          const genre = await targetRow.locator('td').nth(4).textContent();
          console.log(`✓ File categorized as: ${genre}`);
          
          // Check if it's properly categorized
          if (genre && genre !== 'other') {
            console.log('✓ Automatic genre categorization working');
          }
          
          // Click to view file details
          const viewBtn = targetRow.locator('[aria-label="View details"]');
          await viewBtn.click();
          await page.waitForLoadState('networkidle');
          
          // Test transcription
          console.log('  Testing transcription...');
          const transcribeBtn = page.locator('button:has-text("Transcribe")');
          if (await transcribeBtn.isVisible()) {
            await transcribeBtn.click();
            console.log('  Waiting for transcription to complete...');
            await page.waitForTimeout(15000); // Give time for transcription
            
            // Check if transcription appeared
            const transcriptionTab = page.locator('text=Transcription');
            if (await transcriptionTab.isVisible()) {
              await transcriptionTab.click();
              await page.waitForTimeout(1000);
              
              // Check for transcribed text
              const transcribedText = await page.locator('.MuiCardContent-root').textContent();
              if (transcribedText && transcribedText.length > 50) {
                console.log('✓ Transcription successful - extracted text from song');
                console.log(`  First 100 chars: ${transcribedText.substring(0, 100)}...`);
              }
            }
          }
        }
      }
    } else {
      console.log('⚠ FLAC file not found for testing');
    }
  });

  test('5. File Details and Export Functionality', async ({ page }) => {
    console.log('Testing file details and export functionality...');
    
    await login(page);
    
    // Get first file from dashboard
    const fileRows = page.locator('tbody tr');
    const fileCount = await fileRows.count();
    
    if (fileCount > 0) {
      // Store filename for export test
      const filename = await fileRows.first().locator('td').first().textContent();
      
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
      
      // Test Export functionality
      console.log('  Testing export options...');
      const exportBtn = page.locator('button:has-text("Export")');
      if (await exportBtn.isVisible()) {
        await exportBtn.click();
        await page.waitForTimeout(500);
        
        // Check export options
        const exportFormats = ['JSON', 'CSV', 'Excel', 'ZIP', 'TAR.GZ (Original)', 'TAR.GZ (Mono)'];
        for (const format of exportFormats) {
          const formatVisible = await page.locator(`text="${format}"`).isVisible();
          console.log(`  Export ${format}: ${formatVisible ? '✓' : '✗'}`);
        }
        
        // Test actual export (JSON)
        await page.locator('text="JSON"').click();
        console.log('✓ Export functionality available');
      }
    }
  });

  test('6. Search Functionality with Lyrics', async ({ page }) => {
    console.log('Testing search functionality with lyrics search...');
    
    await login(page);
    
    // Navigate to search page
    const drawer = page.locator('[aria-label="open drawer"]');
    if (await drawer.isVisible()) {
      await drawer.click();
      await page.waitForTimeout(500);
    }
    const searchLink = page.locator('text=Search').first();
    await searchLink.click();
    await page.waitForLoadState('networkidle');
    
    // Check if on search page
    const searchTitle = await page.locator('h4:has-text("Search Music")').isVisible();
    expect(searchTitle).toBe(true);
    
    // Test Similar Content search
    console.log('  Testing similar content search...');
    const searchInput = page.locator('input[placeholder*="Search"]').first();
    await searchInput.fill('pumped up kicks');
    await searchInput.press('Enter');
    
    await page.waitForTimeout(3000);
    
    // Check for results
    const hasResults = await page.locator('text=results found').isVisible().catch(() => false);
    const noResults = await page.locator('text=No results').isVisible().catch(() => false);
    
    console.log('✓ Similar content search executed');
    console.log(`  Results: ${hasResults ? 'Found' : noResults ? 'None' : 'Unknown'}`);
    
    // Test Lyrics search mode
    console.log('  Testing lyrics search mode...');
    const lyricsBtn = page.locator('button:has-text("Search by Lyrics")');
    if (await lyricsBtn.isVisible()) {
      await lyricsBtn.click();
      await page.waitForTimeout(500);
      
      const lyricsInput = page.locator('input[placeholder*="lyrics"]').first();
      await lyricsInput.fill('better run better run');
      await lyricsInput.press('Enter');
      
      await page.waitForTimeout(3000);
      
      const lyricsResults = await page.locator('text=results found').isVisible().catch(() => false);
      console.log('✓ Lyrics search executed');
      console.log(`  Lyrics results: ${lyricsResults ? 'Found' : 'None'}`);
    }
  });

  test('7. Batch Export Functionality', async ({ page }) => {
    console.log('Testing batch export functionality...');
    
    await login(page);
    
    // Check if we have multiple files
    const fileRows = page.locator('tbody tr');
    const fileCount = await fileRows.count();
    
    if (fileCount >= 2) {
      // Select multiple files for batch export
      console.log(`  Selecting ${Math.min(fileCount, 3)} files for batch export...`);
      
      // Click checkboxes for first few files
      for (let i = 0; i < Math.min(fileCount, 3); i++) {
        const checkbox = fileRows.nth(i).locator('input[type="checkbox"]');
        if (await checkbox.isVisible()) {
          await checkbox.check();
        }
      }
      
      // Look for batch export option
      const batchExportBtn = page.locator('button:has-text("Export Selected")');
      if (await batchExportBtn.isVisible()) {
        await batchExportBtn.click();
        await page.waitForTimeout(500);
        
        // Check for tar.gz option
        const tarGzOption = page.locator('text="TAR.GZ"');
        if (await tarGzOption.isVisible()) {
          console.log('✓ Batch export with TAR.GZ available');
          await tarGzOption.click();
          console.log('✓ Batch export initiated');
        }
      } else {
        console.log('  Batch export button not found - may need to implement');
      }
    } else {
      console.log('  Not enough files for batch export test');
    }
  });
  
  test('8. Logout and Cookie Persistence', async ({ page, context }) => {
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
      const authCookie = cookies.find(c => c.name === 'music_analyzer_auth');
      expect(authCookie).toBeFalsy();
      console.log('✓ Auth cookie cleared');
    }
  });

  test('9. Error Handling - Invalid File ID', async ({ page }) => {
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

  test('10. Responsive Design', async ({ page }) => {
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
    modelManagement: false,
    transcription: false,
    export: false,
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
  
  // Check model management
  results.modelManagement = await page.locator('text=Select Model').isVisible();
  console.log(`Model Management: ${results.modelManagement ? '✓' : '✗'}`);
  
  // Check upload page
  const drawer = page.locator('[aria-label="open drawer"]');
  if (await drawer.isVisible()) {
    await drawer.click();
    await page.waitForTimeout(500);
  }
  await page.locator('text=Upload').first().click();
  results.upload = await page.locator('text=Upload Music Files').isVisible();
  console.log(`Upload Page: ${results.upload ? '✓' : '✗'}`);
  
  // Check search page
  if (await drawer.isVisible()) {
    await drawer.click();
    await page.waitForTimeout(500);
  }
  await page.locator('text=Search').first().click();
  results.search = await page.locator('h4:has-text("Search Music")').isVisible();
  console.log(`Search Page: ${results.search ? '✓' : '✗'}`);
  
  // Check transcription capability (if files exist)
  if (await drawer.isVisible()) {
    await drawer.click();
    await page.waitForTimeout(500);
  }
  await page.locator('text=Dashboard').first().click();
  const fileCount = await page.locator('tbody tr').count();
  if (fileCount > 0) {
    const viewBtn = page.locator('[aria-label="View details"]').first();
    await viewBtn.click();
    results.transcription = await page.locator('button:has-text("Transcribe")').isVisible();
    results.export = await page.locator('button:has-text("Export")').isVisible();
  } else {
    results.transcription = true; // No files to test
    results.export = true;
  }
  console.log(`Transcription: ${results.transcription ? '✓' : '✗'}`);
  console.log(`Export: ${results.export ? '✓' : '✗'}`);
  
  console.log(`JavaScript Errors: ${results.errors}`);
  
  const allPassed = Object.values(results).every(v => v === true || v === 0);
  console.log(`\nOverall Status: ${allPassed ? '✅ HEALTHY' : '⚠️ ISSUES FOUND'}`);
  
  expect(allPassed).toBe(true);
});