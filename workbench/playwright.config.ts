import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './browser',
  timeout: 45000,
  workers: 1,
  retries: 0,
  outputDir: '../test-results/relay',
  use: { baseURL: 'http://127.0.0.1:8100', trace: 'retain-on-failure' },
  projects: [
    { name: 'desktop', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['Pixel 7'] } },
  ],
  webServer: {
    command:
      'workbench/.venv/bin/python -m uvicorn relay.main:create_app --factory --host 127.0.0.1 --port 8100',
    cwd: '..',
    url: 'http://127.0.0.1:8100/api/health',
    reuseExistingServer: false,
    timeout: 30000,
    env: { RELAY_ENV: 'local', RELAY_DB: `workbench/.runtime/e2e-${process.pid}.sqlite` },
  },
});
