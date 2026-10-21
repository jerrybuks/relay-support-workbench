import { expect, test } from '@playwright/test';

test('course overview explains the four contacts and supports topic exploration', async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/course');
  await expect(page.getByRole('heading', { level: 1 })).toContainText('AI engineering');
  await expect(page.getByText('4 contacts × 60 minutes', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-course.png` });
  const contextButton = page.getByRole('button', {
    name: 'Read the Kora Dispatch project context',
  });
  await contextButton.click();
  const context = page.getByRole('dialog', { name: 'The Kora Dispatch context' });
  await expect(context).toBeVisible();
  await expect(context).toContainText('Their support team is overwhelmed with customer questions');
  await expect(context).toContainText('I paid ₦8,000 for express delivery');
  await expect(context.locator('.context-modal-body p')).toHaveCount(4);
  await expect(context).not.toContainText('Your assignment is');
  expect(await context.evaluate((el) => el.scrollWidth <= el.clientWidth)).toBe(true);
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-course-context.png` });
  await page.getByRole('button', { name: 'Close project context', exact: true }).click();
  await expect(context).not.toBeVisible();
  await expect(contextButton).toBeFocused();
  await contextButton.press('Enter');
  await expect(context).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(context).not.toBeVisible();
  await expect(contextButton).toBeFocused();
  await page.getByRole('link', { name: 'The four contacts', exact: true }).click();
  await expect(page).toHaveURL(/#contacts$/);
  await expect(
    page.getByRole('heading', { name: 'From a model response to a trustworthy application' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Take a real engineering task from issue to review' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Give automation useful capabilities and clear boundaries' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Decide what is ready to put in front of a customer' }),
  ).toBeVisible();
  const topic = page
    .locator('.topic-groups details')
    .filter({ hasText: 'Retrieval and context engineering' });
  await topic.locator('summary').click();
  await expect(topic.locator('p')).toBeVisible();
  await expect(topic).toContainText('hybrid retrieval');
  await page.getByRole('link', { name: 'Guided practice', exact: true }).click();
  await expect(page).toHaveURL(/#practice$/);
  await expect(
    page.getByText('A Codex issue-to-PR change with tests and browser evidence.'),
  ).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole('link', { name: 'Open workbench', exact: false }).click();
  await expect(page.getByRole('heading', { name: 'Resolution desk', exact: true })).toBeVisible();
  await page.getByRole('link', { name: 'Course overview', exact: false }).click();
  await expect(page).toHaveURL(/\/course$/);
  expect(errors).toEqual([]);
});

test('concepts-only deck explains the existing topics without demonstration instructions', async ({
  page,
}, info) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/course');
  await page
    .getByRole('link', { name: 'Open the optional concepts-only slides', exact: false })
    .click();
  await expect(page).toHaveURL(/contact1-concepts\.html$/);
  await expect(page.locator('#slide-counter')).toHaveText('1 / 15');
  await expect(page.locator('.slide')).toHaveCount(15);
  await expect(page.locator('.slide[data-phase="Demo"], .slide.appendix')).toHaveCount(0);
  await expect(page.locator('a[href^="http://127.0.0.1:800"]')).toHaveCount(0);
  await expect(page.locator('#why')).toContainText('Concepts explained');
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-concepts.png` });
  await page.keyboard.press('g');
  await expect(page.locator('#outline-list')).toContainText('Contact 1 / Concepts');
  await expect(page.locator('#outline-list')).not.toContainText('00–15');
  await expect(page.locator('#outline-list button')).toHaveCount(15);
  await page.getByRole('button', { name: /OpenAI Responses API: request/ }).click();
  await page.keyboard.press('n');
  await expect(page.locator('#responses .speaker-notes')).toBeVisible();
  await expect(page.locator('#responses .speaker-notes')).toContainText(
    'We don’t pass the result of create into parse',
  );
  await page.keyboard.press('n');
  const ids = await page.locator('.slide').evaluateAll((slides) => slides.map((slide) => slide.id));
  for (const id of ids) {
    await page.goto(`/static/contact1-concepts.html#${id}`);
    await expect(page.locator(`#${id}`)).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), id).toBe(
      true,
    );
    if (info.project.name === 'desktop') {
      const footer = await page.locator('.deck-footer').boundingBox();
      expect(footer!.y + footer!.height, `${id} fits a projector`).toBeLessThanOrEqual(720);
    }
  }
  await page.keyboard.press('End');
  await expect(page).toHaveURL(/#choices$/);
  await expect(page.getByRole('button', { name: 'Next slide', exact: true })).toBeDisabled();
  expect(errors).toEqual([]);
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.slide:visible')).toHaveCount(15);
  await expect(page.locator('.speaker-notes:visible')).toHaveCount(0);
  const clipped = await page
    .locator('.slide')
    .evaluateAll((slides) =>
      slides
        .filter(
          (slide) =>
            slide.scrollHeight > slide.clientHeight + 2 ||
            slide.scrollWidth > slide.clientWidth + 2,
        )
        .map((slide) => slide.id),
    );
  expect(clipped).toEqual([]);
  if (info.project.name === 'desktop') {
    await page.pdf({
      path: 'workbench/evidence/contact1-concepts.pdf',
      preferCSSPageSize: true,
      printBackground: true,
    });
  }
});

test('investigate, inspect, propose, review and persist a resolution', async ({ page }, info) => {
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Resolution desk', exact: true })).toBeVisible();
  await page.getByRole('button', { name: /Open case RY-1042/ }).click();
  await expect(page.getByRole('list', { name: 'Resolution progress' })).toContainText(
    'Investigate',
  );
  await expect(page.getByRole('button', { name: 'Investigate case', exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Investigate case', exact: true }).click();
  await expect(page.getByText('Policy evidence found', { exact: true })).toBeVisible();
  await page.getByText('How this answer was prepared', { exact: false }).click();
  await expect(page.locator('.run-summary-body')).toContainText('No model call or API charge');
  await page.locator('.evidence summary').click();
  await expect(page.locator('.evidence')).toContainText('25%');
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(page.locator('#notice')).toBeEmpty({ timeout: 7000 });
  await page.screenshot({
    path: `workbench/evidence/${info.project.name}-investigation.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Propose a service credit', exact: true }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(page.getByLabel('Amount in naira')).toHaveValue('2000');
  await page.getByRole('button', { name: 'Submit for approval', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Pending resolution' })).toBeVisible();
  await page.getByLabel('Demo persona').selectOption('supervisor');
  await page.getByRole('button', { name: 'Review proposal', exact: true }).click();
  await page.getByRole('button', { name: 'Approve ₦2,000', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Resolution approved' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: /Open case RY-1042/ }).click();
  await expect(page.getByRole('region', { name: 'Resolved case' })).toContainText('₦2,000');
  await page.evaluate(() => window.scrollTo(0, 0));
  await expect(page.locator('#notice')).toBeEmpty({ timeout: 7000 });
  await page.screenshot({
    path: `workbench/evidence/${info.project.name}-resolved.png`,
    fullPage: true,
  });
  await page.getByRole('button', { name: 'Activity', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Service credit approved', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Knowledge library', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Supervisor reserve', exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
});

test('starter paraphrase gap and unsaved preview are explicit', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Open case RY-1042/ }).click();
  await page.getByRole('button', { name: /Can this customer receive compensation/ }).click();
  await expect(page.getByLabel('Ask about this case')).toHaveValue(
    'Can this customer receive compensation for a late express delivery?',
  );
  await page.getByLabel('Save this exchange in the case').uncheck();
  await page.getByRole('button', { name: 'Ask', exact: true }).click();
  await expect(page.getByText('More evidence needed', { exact: true })).toBeVisible();
  await expect(page.getByText('Not saved to history', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Saved exchanges', exact: true }).click();
  await expect(page.getByText('No saved exchanges yet.', { exact: false })).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(
    true,
  );
});

test('failed live result is visible and offers no resolution action', async ({ page }) => {
  // Browser presentation contract only; actual SDK failure paths are tested in Python.
  await page.route('**/api/v1/cases/*/investigations', async (route) => {
    await route.fulfill({
      json: {
        id: 'browser-failure-fixture',
        provider: 'openai',
        model: 'mock-model',
        status: 'unavailable',
        answer: 'The live investigation could not be validated.',
        citations: [],
        tools: [],
        suggested_credit_naira: null,
        trace: { duration_ms: 20, model_calls: 1, input_tokens: null, output_tokens: null },
      },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: /Open case RY-1042/ }).click();
  await page.getByLabel('Ask about this case').fill('delivery service credit policy');
  await page.getByLabel('Save this exchange in the case').uncheck();
  await page.getByRole('button', { name: 'Ask', exact: true }).click();
  await expect(page.getByText('Investigation unavailable', { exact: true })).toBeVisible();
  await page.getByText('How this answer was prepared', { exact: false }).click();
  await expect(page.locator('.run-summary-body')).toContainText('No resolution was proposed');
  await expect(
    page.getByRole('button', { name: 'Propose a service credit', exact: true }),
  ).toHaveCount(0);
});

test('clear next action, search, memory and observer restrictions', async ({ page }) => {
  await page.goto('/');
  await page.getByLabel('Search cases').fill('damaged');
  await expect(page.getByRole('button', { name: /Open case RY-1044/ })).toBeVisible();
  await expect(page.getByRole('button', { name: /Open case RY-1042/ })).toHaveCount(0);
  await page.getByRole('button', { name: /Open case RY-1044/ }).click();
  await page.getByRole('button', { name: 'Investigate case', exact: true }).click();
  await expect(page.locator('.answer-text')).toContainText('photos');
  await expect(
    page.getByRole('button', { name: 'Propose a service credit', exact: true }),
  ).toHaveCount(0);
  await page.getByRole('button', { name: /Saved exchanges/ }).click();
  await expect(page.locator('.history-item')).toHaveCount(1);
  await page.getByRole('button', { name: 'Delete saved exchanges', exact: true }).click();
  await expect(page.getByText('No saved exchanges yet.', { exact: false })).toBeVisible();
  await page.getByLabel('Demo persona').selectOption('observer');
  await page.getByRole('button', { name: 'Investigation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Investigate case', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Knowledge library', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Supervisor reserve', exact: true })).toHaveCount(
    0,
  );
});

test('self-hosted Swagger supports sessions, protected reads and CSRF mutations', async ({
  page,
  baseURL,
}, info) => {
  const external: string[] = [];
  const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).origin !== new URL(baseURL!).origin) {
      external.push(route.request().url());
      return route.abort();
    }
    return route.continue();
  });
  await page.addInitScript(() => {
    (window as any).cspViolations = [];
    document.addEventListener('securitypolicyviolation', (event) => {
      (window as any).cspViolations.push(event.violatedDirective);
    });
  });
  await page.goto('/docs');
  await expect(page.getByRole('heading', { name: /Relay Resolution API/ })).toBeVisible();

  const operation = (method: string, path: string) =>
    page.locator(`.opblock-${method}`).filter({
      has: page
        .locator('.opblock-summary-path')
        .filter({ hasText: new RegExp('^' + path.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') + '$') }),
    });
  const prepare = async (method: string, path: string) => {
    const block = operation(method, path);
    await block.locator('.opblock-summary-control').click();
    await block.getByRole('button', { name: 'Try it out', exact: true }).click();
    return block;
  };
  const execute = async (block: ReturnType<typeof operation>, path: string, method = 'POST') => {
    const result = page.waitForResponse(
      (r) => new URL(r.url()).pathname === path && r.request().method() === method,
    );
    await block.getByRole('button', { name: 'Execute', exact: true }).click();
    return await result;
  };
  const health = await prepare('get', '/api/health');
  expect((await execute(health, '/api/health', 'GET')).status()).toBe(200);

  const session = await prepare('post', '/api/v1/demo/session');
  await session.locator('textarea').fill('{"role":"agent"}');
  expect((await execute(session, '/api/v1/demo/session')).status()).toBe(200);

  const cases = await prepare('get', '/api/v1/cases');
  expect((await execute(cases, '/api/v1/cases', 'GET')).status()).toBe(200);

  const investigation = await prepare('post', '/api/v1/cases/{case_id}/investigations');
  await investigation.getByPlaceholder('case_id').fill('RY-1042');
  await investigation
    .locator('textarea')
    .fill('{"question":"delivery service credit policy","remember":false}');
  const investigated = await execute(investigation, '/api/v1/cases/RY-1042/investigations');
  expect(investigated.status()).toBe(200);
  expect((await investigated.json()).status).toBe('supported');
  const proposal = await prepare('post', '/api/v1/cases/{case_id}/proposals');
  await proposal.getByPlaceholder('case_id').fill('RY-1042');
  await proposal.locator('textarea').fill(
    JSON.stringify({
      amount_naira: 2000,
      rationale: 'Express shipment delayed beyond the published policy threshold.',
      case_version: 1,
    }),
  );
  const proposed = await execute(proposal, '/api/v1/cases/RY-1042/proposals');
  expect(proposed.status()).toBe(200);
  const key = proposed.request().headers()['idempotency-key'];
  expect(key).toMatch(/^[0-9a-f-]{36}$/);
  await proposal.getByPlaceholder(/idempotency.key/i).fill(key);
  const replayed = await execute(proposal, '/api/v1/cases/RY-1042/proposals');
  expect(replayed.status()).toBe(200);
  expect((await replayed.json()).id).toBe((await proposed.json()).id);

  await session.locator('textarea').fill('{"role":"supervisor"}');
  expect((await execute(session, '/api/v1/demo/session')).status()).toBe(200);
  expect((await execute(investigation, '/api/v1/cases/RY-1042/investigations')).status()).toBe(200);
  expect(external).toEqual([]);
  expect(errors).toEqual([]);
  expect(await page.evaluate(() => (window as any).cspViolations)).toEqual([]);
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-swagger.png` });
});

test('RAG presentation distinguishes embedding usage and exact chunk provenance', async ({
  page,
}) => {
  // Presentation fixture only. Python exercises actual SDK + Qdrant pipeline contracts.
  await page.route('**/api/v1/cases/*/investigations', async (route) => {
    await route.fulfill({
      json: {
        id: 'browser-vector-fixture',
        provider: 'openai',
        model: 'mock-model',
        status: 'supported',
        answer: 'A supervisor must review the service credit.',
        citations: [
          {
            id: 'POL-DELIVERY-3',
            title: 'Delivery service credit policy',
            version: '3.0',
            excerpt: 'Exact permitted policy chunk.',
            chunk_id: 'mock-chunk',
            start: 0,
            end: 29,
            score: 0.9,
          },
        ],
        tools: [
          {
            name: 'search_policies',
            status: 'completed',
            result: { source_ids: ['POL-DELIVERY-3'] },
          },
        ],
        suggested_credit_naira: null,
        trace: {
          duration_ms: 50,
          retrieval: 'vector',
          embedding_calls: 1,
          embedding_input_tokens: 12,
          model_calls: 2,
          input_tokens: 200,
          output_tokens: 50,
        },
      },
    });
  });
  await page.goto('/');
  await page.getByRole('button', { name: /Open case RY-1042/ }).click();
  await page.getByLabel('Ask about this case').fill('What remedy applies?');
  await page.getByLabel('Save this exchange in the case').uncheck();
  await page.getByRole('button', { name: 'Ask', exact: true }).click();
  await page.locator('.evidence summary').click();
  await expect(page.locator('.evidence')).toContainText('characters 0–29');
  await expect(page.locator('.evidence')).toContainText('retrieval score 0.9000');
  await page.getByText('How this answer was prepared', { exact: false }).click();
  await expect(page.locator('.run-summary-body')).toContainText('Embedding requests / tokens');
  await expect(page.locator('.run-summary-body')).toContainText('1 / 12');
  await expect(page.locator('.run-summary-body')).toContainText('vector');
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

for (const provider of ['openai', 'openrouter']) {
  test(`${provider} teaching controls send context/runtime options and render a streamed result`, async ({
    page,
  }, info) => {
    // Browser presentation fixture; Python independently executes SDK streaming and graph/tool paths.
    await page.route('**/api/v1/demo/session', async (route) => {
      const response = await route.fetch();
      await route.fulfill({
        response,
        json: {
          ...(await response.json()),
          provider,
          checkpoint: 'contact-1-live-reference',
        },
      });
    });
    let submitted: Record<string, unknown> = {};
    await page.route('**/api/v1/cases/*/runs/stream', async (route) => {
      submitted = route.request().postDataJSON();
      const result = {
        id: 'browser-runtime-fixture',
        provider,
        model: 'mock-model',
        status: 'supported',
        answer:
          'For this late express shipment, you may propose compensation of up to ₦2,000. A supervisor must approve the amount before it is recorded.',
        citations: [
          {
            id: 'POL-DELIVERY-3',
            title: 'Delivery service credit policy',
            version: '3.0',
            excerpt:
              'For an express shipment delivered more than 24 hours late, an agent may propose a service credit of up to 25% of the delivery fee, capped at ₦5,000. A supervisor must approve the exact amount.',
            chunk_id: 'browser-policy-chunk',
            start: 0,
            end: 200,
            score: 0.0328,
          },
        ],
        tools: [],
        suggested_credit_naira: null,
        trace: {
          duration_ms: 40,
          model_calls: 4,
          input_tokens: 200,
          output_tokens: 50,
          memory_mode: 'case',
          memory_exchanges: 1,
          execution_mode: 'agent',
          runtime: 'langgraph',
          stages: [{ name: 'answer_generation', status: 'completed', duration_ms: 12 }],
        },
      };
      const frames = [
        ['started', {}],
        ['stage', { name: 'retrieval', status: 'started' }],
        ['generation_progress', { characters_received: 80, validated: false }],
        ['completed', result],
      ];
      await route.fulfill({
        contentType: 'text/event-stream',
        body: frames
          .map(([name, data]) => `event: ${name}\ndata: ${JSON.stringify(data)}\n\n`)
          .join(''),
      });
    });
    await page.goto('/');
    await expect(page.locator('.mode-badge')).toContainText(
      provider === 'openrouter' ? 'OpenAI via OpenRouter' : 'Live OpenAI reference',
    );
    await page.getByRole('button', { name: /Open case RY-1042/ }).click();
    await expect(page.getByRole('button', { name: 'Investigate case', exact: true })).toHaveCount(
      0,
    );
    await expect(page.getByRole('list', { name: 'Resolution progress' })).toHaveCount(0);
    await expect(page.getByLabel('Ask about this case')).toBeVisible();
    const suggestions = page.getByRole('group', { name: 'Suggested questions' });
    await expect(suggestions.getByRole('button')).toHaveCount(4);
    await suggestions.getByRole('button', { name: 'Compensation?', exact: true }).click();
    await expect(page.getByLabel('Ask about this case')).toHaveValue(
      'Can this customer receive compensation for a late express delivery?',
    );
    await expect(page.getByLabel('Ask about this case')).toBeFocused();
    expect(submitted).toEqual({});
    await expect(page.getByLabel('Runtime', { exact: true })).not.toBeVisible();
    await page.getByRole('button', { name: 'Inspect AI', exact: true }).click();
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByLabel('Conversation context', { exact: true }).selectOption('case');
    await page.getByLabel('Execution', { exact: true }).selectOption('agent');
    await page.getByLabel('Runtime', { exact: true }).selectOption('langgraph');
    await page.getByLabel('Save this exchange in the case').uncheck();
    await page.getByRole('button', { name: 'Close AI inspector', exact: true }).click();
    await expect(page.getByRole('button', { name: 'Inspect AI', exact: true })).toBeFocused();
    await page.getByLabel('Ask about this case').fill('What should happen next?');
    await page.getByRole('button', { name: 'Ask', exact: true }).click();
    await expect(page.locator('.answer-text')).toContainText('A supervisor must approve');
    expect(submitted).toMatchObject({
      memory_mode: 'case',
      execution_mode: 'agent',
      runtime: 'langgraph',
      remember: false,
    });
    await page.locator('.answer-sources summary').click();
    await expect(page.locator('.answer-sources')).toContainText('25%');
    await expect(page.locator('.rag-assistant')).not.toContainText('retrieval score');
    await page.screenshot({
      path: `workbench/evidence/${info.project.name}-${provider}-clean-rag.png`,
      fullPage: true,
    });
    await expect(page.locator('.rag-assistant')).not.toContainText('How this answer was prepared');
    await expect(page.locator('.rag-assistant')).not.toContainText('Technical record');
    await expect(page.locator('.rag-assistant')).not.toContainText('Save this exchange');
    await expect(suggestions.getByRole('button')).toHaveCount(4);
    await page.getByRole('button', { name: 'Inspect AI', exact: true }).click();
    await expect(page.locator('.inspector-sources')).toContainText('retrieval score 0.0328');
    await expect(page.locator('.run-summary-body')).toContainText('case · 1 exchanges');
    await expect(page.getByRole('list', { name: 'Execution stages' })).toContainText(
      'answer generation',
    );
    await page.getByRole('button', { name: 'Raw JSON', exact: true }).click();
    await expect(page.getByLabel('Raw execution record')).toContainText('browser-runtime-fixture');
    await expect(page.locator('#ai-inspector')).not.toContainText('Execution settings');
    await page.screenshot({
      path: `workbench/evidence/${info.project.name}-${provider}-ai-inspector.png`,
    });
    await page.keyboard.press('Escape');
    await expect(page.locator('#ai-inspector')).not.toBeVisible();
    await expect(page.getByRole('button', { name: 'Inspect AI', exact: true })).toBeFocused();
    await expect(page.locator('#question')).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
  });
}

test('Contact 1 presentation supports deep links, keyboard navigation, notes and rehearsal timing', async ({
  page,
}, info) => {
  const errors: string[] = [];
  const violations: string[] = [];
  const external: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('request', (request) => {
    if (!request.url().startsWith('http://127.0.0.1:8100/')) external.push(request.url());
  });
  await page.exposeFunction('recordSlideCsp', (directive: string) => violations.push(directive));
  await page.addInitScript(() =>
    document.addEventListener('securitypolicyviolation', (event) => {
      (window as any).recordSlideCsp(event.violatedDirective);
    }),
  );
  await page.clock.install();
  await page.goto('/course');
  await page.getByRole('link', { name: 'Open Contact 1 slides', exact: false }).click();
  await expect(page).toHaveURL(/\/course\/contact-1$/);
  await expect(page.getByRole('heading', { level: 1 })).toContainText('Build an answer');
  await expect(page.locator('.slide:visible')).toHaveCount(1);
  await expect(page.locator('#slide-counter')).toHaveText('1 / 30');
  await expect(page.locator('#why')).toContainText(
    'My parcel arrived late. Can I get compensation?',
  );
  await expect(page.getByRole('button', { name: 'Previous slide' })).toBeDisabled();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-cover.png` });
  await expect(page.locator('#slide-dots button')).toHaveCount(30);
  const ragShortcut = page.getByRole('button', { name: 'Go to slide 7', exact: true });
  await ragShortcut.click();
  await expect(page).toHaveURL(/#rag$/);
  await expect(ragShortcut).toHaveAttribute('aria-current', 'step');
  await expect(ragShortcut).toHaveAttribute('tabindex', '0');
  await page.keyboard.press('Home');
  await expect(page.getByRole('button', { name: 'Go to slide 1', exact: true })).toHaveAttribute(
    'aria-current',
    'step',
  );
  await expect(ragShortcut).not.toHaveAttribute('aria-current');
  await page.getByRole('button', { name: 'Next slide' }).click();
  await expect(page).toHaveURL(/#outcomes$/);
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(/#harness$/);
  await expect(page.getByRole('img', { name: 'A horse wearing a harness' })).toBeVisible();
  await expect(page.locator('#harness')).toContainText('Evaluation harness = the test runner.');
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-harness.png` });
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(/#governance$/);
  await expect(page.locator('#governance')).toContainText('People remain accountable.');
  await expect(page.locator('#governance .speaker-notes')).toBeHidden();
  await page.screenshot({
    path: `workbench/evidence/${info.project.name}-contact1-governance.png`,
  });
  await page.keyboard.press('ArrowRight');
  await expect(page).toHaveURL(/#request-path$/);
  await page.keyboard.press('n');
  await expect(page.locator('#notes-button')).toHaveAttribute('aria-pressed', 'true');
  await expect(page.locator('#request-path .speaker-notes')).toBeVisible();
  await page.keyboard.press('g');
  await expect(page.getByRole('dialog', { name: 'Presentation contents' })).toBeVisible();
  await expect(page.locator('#outline-list button')).toHaveCount(30);
  await page.getByRole('button', { name: /RAG has an indexing path and a query path/ }).click();
  await expect(page).toHaveURL(/#rag$/);
  await expect(page.getByRole('heading', { name: 'RAG has two paths.' })).toBeVisible();
  await page.getByRole('button', { name: /Speaker notes/ }).click();
  await expect(page.locator('#rag .speaker-notes')).toBeHidden();
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-rag.png` });
  for (const [id, heading] of [
    ['responses', 'OpenAI Responses API: the model boundary.'],
    ['memory', 'Conversation state: who keeps the context?'],
    ['streaming', 'Streaming: events before the final answer.'],
  ]) {
    await page.goto(`/course/contact-1#${id}`);
    await expect(page.getByRole('heading', { name: heading, exact: true })).toBeVisible();
    await expect(page.locator(`#${id} .speaker-notes`)).toBeHidden();
    await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-${id}.png` });
  }
  await page.screenshot({ path: `workbench/evidence/${info.project.name}-contact1-streaming.png` });
  await page.getByRole('button', { name: 'Start timer', exact: true }).click();
  await page.clock.fastForward(61000);
  await expect(page.locator('#timer')).toHaveText('01:01');
  await page.getByRole('button', { name: 'Pause timer', exact: true }).click();
  await page.clock.fastForward(10000);
  await expect(page.locator('#timer')).toHaveText('01:01');
  await page.getByRole('button', { name: 'Reset rehearsal timer' }).click();
  await expect(page.locator('#timer')).toHaveText('00:00');
  await page.goto('/course/contact-1#responses');
  await page.context().grantPermissions(['clipboard-read', 'clipboard-write']);
  const codeLocation = page.locator('#responses [data-code-location]').first();
  const expectedLocation = await codeLocation.getAttribute('data-code-location');
  await codeLocation.click();
  await expect(page.locator('#code-copy-status')).toContainText(`Copied ${expectedLocation}`);
  expect(await page.evaluate(() => navigator.clipboard.readText())).toBe(expectedLocation);
  await page.clock.fastForward(5100);
  await expect(page.locator('#code-copy-status')).toBeHidden();
  await page.goto('/course/contact-1#demo-baseline');
  await expect(page.locator('#phase-label')).toHaveText('Demo');
  await expect(page.locator('#planned-time')).toHaveText('15–23 min');
  await expect(page.getByRole('link', { name: 'Open Relay', exact: false })).toHaveAttribute(
    'href',
    'http://127.0.0.1:8002',
  );
  await expect(
    page.locator('.slide.demo a[href*="8004"], .slide.demo a[href*="8001"]'),
  ).toHaveCount(0);
  await page.keyboard.press('End');
  await expect(page).toHaveURL(/#references$/);
  await expect(page.getByRole('button', { name: 'Next slide' })).toBeDisabled();
  await page.keyboard.press('Home');
  await expect(page).toHaveURL(/#why$/);
  await page.goto('/course/contact-1#%');
  await expect(page.locator('#slide-counter')).toHaveText('1 / 30');
  const slideIds = await page.locator('.slide').evaluateAll((slides) => slides.map((s) => s.id));
  const projectorOverflow: string[] = [];
  for (const id of slideIds) {
    await page.goto(`/course/contact-1#${id}`);
    await expect(page.locator(`#${id}`)).toBeVisible();
    expect(
      await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth),
      `${id} should fit the screen width`,
    ).toBe(true);
    if (
      info.project.name === 'desktop' &&
      !(await page.locator(`#${id}`).evaluate((s) => s.classList.contains('appendix')))
    ) {
      const footer = await page.locator('.deck-footer').boundingBox();
      if (footer!.y + footer!.height > 720) projectorOverflow.push(id);
    }
  }
  expect(projectorOverflow, 'Audience slides and navigation should fit a 720p projector').toEqual(
    [],
  );
  expect(violations).toEqual([]);
  expect(errors).toEqual([]);
  expect(external).toEqual([]);
});

test('Contact 1 print view contains the complete deck without notes or clipped slides', async ({
  page,
}, info) => {
  await page.goto('/course/contact-1?notes=1#evaluation');
  await expect(page.locator('#evaluation .speaker-notes')).toBeVisible();
  await page.emulateMedia({ media: 'print' });
  await expect(page.locator('.slide:visible')).toHaveCount(30);
  await expect(page.locator('.speaker-notes:visible')).toHaveCount(0);
  const clipped = await page.locator('.slide').evaluateAll((slides) =>
    slides
      .filter(
        (slide) =>
          slide.scrollHeight > slide.clientHeight + 2 || slide.scrollWidth > slide.clientWidth + 2,
      )
      .map((slide) => ({
        id: slide.id,
        height: slide.scrollHeight,
        available: slide.clientHeight,
      })),
  );
  expect(clipped).toEqual([]);
  if (info.project.name === 'desktop') {
    await page.pdf({
      path: 'workbench/evidence/contact1-presentation.pdf',
      preferCSSPageSize: true,
      printBackground: true,
    });
  }
});
