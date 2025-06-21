import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for AI Voice Agent E2E tests
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',

  use: {
    // Base URL for the API Gateway
    baseURL: process.env.API_GATEWAY_URL || 'http://localhost:8000',
    trace: 'on-first-retry',
    extraHTTPHeaders: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
    },
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },

    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },

    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },

    /* Test against mobile viewports. */
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
  ],

  /* Run your local dev server before starting the tests */
  // Note: webServer is disabled for this demo.
  // To enable, uncomment and ensure the API Gateway server dependencies are installed.
  // webServer: {
  //   command: 'cd services/api-gateway && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000',
  //   url: 'http://localhost:8000/health',
  //   reuseExistingServer: !process.env.CI,
  //   timeout: 120 * 1000,
  // },
});
