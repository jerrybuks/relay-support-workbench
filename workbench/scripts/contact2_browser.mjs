import { chromium } from '@playwright/test';
import { mkdir, writeFile } from 'node:fs/promises';
const args = process.argv.slice(2);
const base = new URL(args[args.indexOf('--base') + 1] || 'http://127.0.0.1:8002');
if (!['localhost', '127.0.0.1'].includes(base.hostname) || base.protocol !== 'http:')
  throw new Error('Use an explicit local teaching URL.');
const ask = args.includes('--ask');
const browser = await chromium.launch();
const report = {
  mode: ask ? 'live-provider' : 'local-browser-no-AI-call',
  url: base.origin,
  checks: [],
  errors: [],
};
try {
  for (const [name, viewport] of [
    ['desktop', { width: 1440, height: 1000 }],
    ['mobile', { width: 390, height: 844 }],
  ]) {
    const context = await browser.newContext({ viewport });
    const page = await context.newPage();
    page.on('pageerror', (error) => report.errors.push(error.message));
    await page.goto(base.origin + '/static/contact2-markdown.html');
    await page.getByText('Optional Codex exercise · Markdown parser', { exact: true }).click();
    await page.getByRole('button', { name: 'Preview document and chunks' }).click();
    await page
      .getByRole('status')
      .filter({ hasText: /Preview ready:/ })
      .waitFor();
    const output = await page.locator('#result').textContent();
    if (!output.includes('POL-COLLECTION-1') || !output.includes('seven calendar days'))
      throw new Error('Preview source missing');
    await page.getByRole('link', { name: 'Resolution desk', exact: false }).click();
    await page.getByRole('heading', { name: 'Resolution desk', exact: true }).waitFor();
    await page.getByLabel('Demo persona').selectOption('agent');
    await page.getByRole('button', { name: /Open case RY-1042/ }).click();
    if (ask && name === 'desktop') {
      await page
        .getByLabel('Ask about this case')
        .fill(
          'How long can a parcel stay at a collection point, when does that period start, and who reviews return to the sender?',
        );
      await page.getByRole('button', { name: 'Ask', exact: true }).click();
      await page.locator('.answer-sources summary').first().waitFor({ timeout: 90000 });
      const answer = await page.locator('.case-workspace').innerText();
      if (!/seven|7/i.test(answer)) throw new Error('Expected seven days in answer');
      await page.locator('.answer-sources summary').first().click();
      if (!(await page.locator('.answer-sources').innerText()).includes('collection'))
        throw new Error('Expected collection citation');
      report.answer = answer;
    }
    if (!(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)))
      throw new Error(name + ' horizontal overflow');
    await mkdir('workbench/.runtime/contact2/evidence', { recursive: true });
    await page.screenshot({
      path: `workbench/.runtime/contact2/evidence/${name}.png`,
      fullPage: true,
    });
    report.checks.push({
      viewport: name,
      preview: true,
      dashboard: true,
      horizontalOverflow: false,
    });
    await context.close();
  }
  if (report.errors.length) throw new Error('Browser console errors');
  report.status = 'passed';
} finally {
  await browser.close();
  await mkdir('workbench/.runtime/contact2/evidence', { recursive: true });
  await writeFile(
    'workbench/.runtime/contact2/evidence/browser.json',
    JSON.stringify(report, null, 2) + '\n',
  );
}
console.log(JSON.stringify({ status: report.status, mode: report.mode, checks: report.checks }));
