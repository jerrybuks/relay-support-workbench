const $ = (selector) => document.querySelector(selector);
const esc = (value) =>
  String(value ?? '').replace(
    /[&<>"']/g,
    (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
  );
const money = (amount) => '₦' + Number(amount).toLocaleString('en-NG');
const icons = {
  queue: '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 10h18M8 15h4"/>',
  book: '<path d="M12 6c-3-3-7-3-9-2v15c3-1 6-1 9 1 3-2 6-2 9-1V4c-2-1-6-1-9 2ZM12 6v14"/>',
  activity: '<path d="M3 12h4l3-8 4 16 3-8h4"/>',
  check: '<path d="m5 12 4 4L19 6"/>',
  clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
  arrow: '<path d="M5 12h14m-5-5 5 5-5 5"/>',
};
const icon = (name) =>
  `<svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor">${icons[name] || icons.queue}</svg>`;
const state = {
  page: 'queue',
  cases: [],
  case: null,
  selected: 'RY-1042',
  filter: 'all',
  search: '',
  tab: 'conversation',
  actor: null,
  checkpoint: 'm0-baseline',
  csrf: '',
  provider: 'fixture',
  hosted: false,
  preview: null,
  questionDraft: '',
  busy: false,
  remember: true,
  inspectorTab: 'run',
  runOptions: { memory_mode: 'stateless', execution_mode: 'workflow', runtime: 'direct' },
  progress: '',
  abortController: null,
  mobileDetail: false,
  docs: [],
  activity: [],
};
let noticeTimer;

function notify(message) {
  $('#notice').textContent = message;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    $('#notice').textContent = '';
  }, 6000);
}

async function api(path, options = {}) {
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (state.csrf) headers['X-CSRF-Token'] = state.csrf;
  const response = await fetch('/api' + path, { ...options, headers });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error?.message || `Request failed (${response.status}).`);
  return data;
}

async function load() {
  state.preview = null;
  const [cases, docs, activity] = await Promise.all([
    api('/v1/cases'),
    api('/v1/knowledge'),
    api('/v1/activity'),
  ]);
  state.cases = cases.items;
  state.docs = docs.items;
  state.activity = activity.items;
  const selected = state.cases.find((c) => c.id === state.selected) || state.cases[0];
  state.selected = selected?.id;
  state.case = selected ? await api('/v1/cases/' + selected.id) : null;
  render();
}

async function boot() {
  try {
    let session;
    try {
      session = await api('/v1/session');
    } catch {
      session = await api('/v1/demo/session', {
        method: 'POST',
        body: JSON.stringify({ role: 'agent' }),
      });
    }
    state.actor = session.actor;
    state.csrf = session.csrf_token;
    state.provider = session.provider || 'fixture';
    state.hosted = session.mode === 'hosted-workshop';
    state.checkpoint = session.checkpoint || 'm0-baseline';
    await load();
  } catch (error) {
    $('#app').innerHTML =
      `<main class="boot" id="main"><span class="brand-symbol">r.</span><h1>Your desk couldn’t open</h1><p>${esc(error.message)}</p><button class="btn primary" data-action="retry">Try again</button></main>`;
    $('#app').setAttribute('aria-busy', 'false');
  }
}

const statusName = (status) =>
  ({ open: 'Open', awaiting_approval: 'Awaiting approval', resolved: 'Resolved' })[status] ||
  status;
const pill = (status) =>
  `<span class="pill ${status === 'awaiting_approval' ? 'waiting' : status === 'resolved' ? 'resolved' : ''}">${esc(statusName(status))}</span>`;

function render() {
  const waiting = state.cases.filter((c) => c.status === 'awaiting_approval').length;
  const open = state.cases.filter((c) => c.status === 'open').length;
  const resolved = state.cases.filter((c) => c.status === 'resolved').length;
  const live = ['openai', 'openrouter'].includes(state.provider);
  const pageName = {
    queue: 'Resolution desk',
    knowledge: 'Knowledge library',
    activity: 'Activity & decisions',
  }[state.page];
  $('#app').innerHTML = `<div class="shell ${live ? 'live-workbench' : ''}">
    <aside class="sidebar"><div class="brand"><span class="brand-symbol">r.</span><div class="brand-text"><div class="brand-name">relay</div><div class="brand-small">A clearer way forward</div></div></div>
      <p class="workspace-label eyebrow">Workspace</p><nav class="nav" aria-label="Workspace navigation">
      ${[
        ['queue', 'Resolution desk', state.cases.length],
        ['knowledge', 'Knowledge library', state.docs.length],
        ['activity', 'Activity', state.activity.length],
      ]
        .map(
          ([id, label, count]) =>
            `<button data-page="${id}" class="${state.page === id ? 'active' : ''}" ${state.page === id ? 'aria-current="page"' : ''} aria-label="${label}">${icon(id === 'knowledge' ? 'book' : id)}<span class="nav-label">${label}</span><span class="count">${count}</span></button>`,
        )
        .join('')}
      </nav><div class="sidebar-bottom"><span class="workspace-dot"></span>Local workspace<strong>Kora Dispatch</strong>Fictional company · workshop edition</div></aside>
    <div class="content"><header class="topbar"><div class="breadcrumb">Kora Dispatch <span aria-hidden="true"> / </span> <b>${pageName}</b></div>
      <div class="persona"><span class="avatar">${state.actor.role === 'supervisor' ? 'AN' : state.actor.role === 'observer' ? 'WO' : 'TA'}</span><div><label for="persona">Demo persona</label><select id="persona" ${state.busy ? 'disabled' : ''} aria-label="Demo persona"><option value="agent" ${state.actor.role === 'agent' ? 'selected' : ''}>Tolu · Support agent</option><option value="supervisor" ${state.actor.role === 'supervisor' ? 'selected' : ''}>Amara · Supervisor</option><option value="observer" ${state.actor.role === 'observer' ? 'selected' : ''}>Workshop observer</option></select></div></div></header>
    <main id="main" class="main-inner"><div class="page-head"><div><h1>${pageName}</h1><p>${state.page === 'queue' ? 'From customer concern to a resolution you can stand behind.' : state.page === 'knowledge' ? 'Published guidance, with the source always in view.' : 'A record of what happened, who reviewed it, and why.'}</p></div><span class="mode-badge ${['openai', 'openrouter'].includes(state.provider) ? 'live' : ''}"><span></span>${['openai', 'openrouter'].includes(state.provider) ? (state.provider === 'openrouter' ? 'OpenAI via OpenRouter' : 'Live OpenAI reference') : state.checkpoint.includes('lexical') ? 'Retrieval reference · fixture' : 'Starter · fixture answers'}</span></div>
    ${state.actor.role === 'observer' ? '<p class="notice-banner">Observer access: you can inspect cases and policies. Switch to a support agent to investigate or propose a resolution.</p>' : ''}
    ${
      state.page === 'queue'
        ? `<div class="metrics"><div class="metric"><div class="metric-icon">${icon('queue')}</div><div><strong>${open}</strong><span>Open cases</span></div><span class="metric-tag">Ready to investigate</span></div><div class="metric"><div class="metric-icon">${icon('clock')}</div><div><strong>${waiting}</strong><span>Awaiting approval</span></div><span class="metric-tag">A second pair of eyes</span></div><div class="metric"><div class="metric-icon">${icon('check')}</div><div><strong>${resolved}</strong><span>Resolved</span></div><span class="metric-tag">A clear way forward</span></div></div>
      <section class="desk ${state.mobileDetail ? 'detail-open' : ''}" aria-label="Case workspace"><aside class="queue"><div class="queue-head"><div class="queue-title">Your queue <span>${state.cases.length} cases</span></div><input type="search" class="search" id="case-search" aria-label="Search cases" placeholder="Search a case or customer…" value="${esc(state.search)}"/><div class="filters" aria-label="Filter cases">${[
        ['all', 'All'],
        ['open', 'Open'],
        ['awaiting_approval', 'Review'],
        ['resolved', 'Resolved'],
      ]
        .map(
          ([id, label]) =>
            `<button data-filter="${id}" class="${state.filter === id ? 'selected' : ''}" aria-pressed="${state.filter === id}">${label}</button>`,
        )
        .join(
          '',
        )}</div></div><div id="case-list">${caseList()}</div></aside><article class="case-workspace">${caseView()}</article></section>`
        : state.page === 'knowledge'
          ? knowledgeView()
          : activityView()
    }
    <footer class="footer"><span>${state.hosted ? 'Workshop demo · fictional data · history resets when the free service restarts' : 'Local demo · fictional data · no customer messages or payments are sent'}</span><a href="/course">Course overview ↗</a><a href="/docs" target="_blank" rel="noopener">API reference ↗</a></footer></main></div></div>`;
  $('#app').setAttribute('aria-busy', 'false');
  if ($('#ai-inspector').open) renderInspector();
}

function caseList() {
  const filtered = state.cases.filter(
    (c) =>
      (state.filter === 'all' || c.status === state.filter) &&
      `${c.subject} ${c.customer} ${c.id}`.toLowerCase().includes(state.search.toLowerCase()),
  );
  return filtered.length
    ? filtered
        .map(
          (c) =>
            `<button class="case-card ${c.id === state.selected ? 'selected' : ''}" data-case="${esc(c.id)}" aria-label="Open case ${esc(c.id)}: ${esc(c.subject)}" ${c.id === state.selected ? 'aria-current="true"' : ''}><div class="case-top"><span>${esc(c.id)}</span><span class="priority">${esc(c.priority)}</span></div><h3>${esc(c.subject)}</h3><div class="case-person"><span class="avatar">${esc(c.initials)}</span>${esc(c.customer)}<span>· ${esc(c.category)}</span></div></button>`,
        )
        .join('')
    : '<p class="queue-empty">No cases match this view.</p>';
}

function caseView() {
  if (!state.case) return '<div class="empty-state">No cases available.</div>';
  const { case: c, messages, proposals } = state.case;
  const exchange = state.preview || messages.at(-1);
  const latest = exchange?.answer;
  const live = ['openai', 'openrouter'].includes(state.provider);
  const questionForm = `<form id="ask-form" class="ask-form"><label for="question">Ask about this case</label><div class="ask-row"><input id="question" name="question" value="${esc(state.questionDraft)}" placeholder="What does our policy allow for this customer?" minlength="3" maxlength="1500" required ${disabled()}/><button class="btn primary" type="submit" ${disabled()}>Ask ${icon('arrow')}</button></div><label class="remember"><input type="checkbox" name="remember" checked ${disabled()}/> Save this exchange in the case</label></form>${promptView(c)}`;
  return `<div class="case-header"><button class="mobile-back" data-action="back">← Back to queue</button><div class="case-meta"><span class="case-id">${esc(c.id)}</span>${pill(c.status)}<span class="pill">${esc(c.category)}</span></div><h2>${esc(c.subject)}</h2><div class="customer-line">${esc(c.customer)} &nbsp; · &nbsp; ${esc(c.route)} &nbsp; · &nbsp; ${esc(c.shipment_id)}</div>${!live && !latest && c.status === 'open' ? `<div class="next-step"><div><span>Start here</span><p>Check the shipment against published policy.</p></div><button class="btn primary" data-action="investigate" ${disabled()}>Investigate case ${icon('arrow')}</button></div>` : ''}${live ? '' : workflowView(c, latest)}<div class="case-tabs" aria-label="Case views">${[
    ['conversation', 'Investigation'],
    ['shipment', 'Shipment details'],
    ['history', 'Saved exchanges'],
  ]
    .map(
      ([id, label]) =>
        `<button class="${state.tab === id ? 'selected' : ''}" data-tab="${id}" aria-pressed="${state.tab === id}">${label}${id === 'history' && messages.length ? ' · ' + messages.length : ''}</button>`,
    )
    .join('')}</div></div>
  <div class="case-body">${
    state.tab === 'shipment'
      ? shipmentView(c)
      : state.tab === 'history'
        ? historyView(messages)
        : `${factsView(c)}<section class="message-card" aria-label="Customer message"><div class="message-head"><span class="avatar">${esc(c.initials)}</span><div><b>${esc(c.customer)}</b><small>Customer message · fictional case</small></div></div><p>${esc(c.message)}</p></section>${live ? '' : proposalView(proposals, latest, c)}
  ${
    live
      ? liveAssistantView(c, exchange)
      : `<section class="assistant-card" aria-label="Resolution assistant"><div class="assistant-heading"><span class="spark" aria-hidden="true">✳</span><h3>Policy assistant</h3><small>${['openai', 'openrouter'].includes(state.provider) ? 'Live · read-only tools' : 'Fixture · no live model'}</small></div><div class="assistant-content">${live ? `<p class="assistant-intro">Ask a question in your own words. Get an answer grounded in our policies and this shipment.</p>${questionForm}` : ''}${state.busy ? `<p class="working" role="status">${esc(state.progress || 'Checking your case…')}</p>${state.abortController ? '<button class="btn" data-action="cancel-investigation">Cancel investigation</button>' : ''}` : ''}${exchange ? `<p class="asked-question">${esc(exchange.question)}${state.preview ? '<small>Not saved to history</small>' : ''}</p>` : ''}${latest ? answerView(latest) : live ? '' : `<h3>Check the shipment and policy.</h3><p>Investigate the case or ask a question below, then review the evidence.</p>`}
    ${live ? '' : questionForm}${referenceControls()}${live ? '<p class="demo-info">Review the cited policy before acting. Compensation requires supervisor approval.</p>' : `<p class="demo-info">${state.checkpoint === 'm0-baseline' || state.checkpoint === 'contact-1-before' ? 'The starter matches policy titles. Paraphrases may return no evidence; use the knowledge library to check the exact guidance.' : 'Reference retrieval searches published policy passages and tags. Answers are fixtures; no model is called.'}</p>`}</div></section>`
  }`
  }${live && state.tab === 'conversation' ? proposalView(proposals, latest, c) : ''}</div>`;
}

function liveAssistantView(c, exchange) {
  const answer = exchange?.answer;
  const status =
    answer?.status === 'unavailable'
      ? '<p class="assistant-error" role="status">The answer could not be completed. Please try again.</p>'
      : answer?.status === 'insufficient_evidence'
        ? '<p class="assistant-caution">More information is needed.</p>'
        : '';
  const sources = answer?.citations.length
    ? `<div class="answer-sources"><span>Sources</span>${answer.citations.map((source) => `<details><summary>${icon('book')}${esc(source.title)}</summary><p>${esc(source.excerpt)}</p><small>Version ${esc(source.version)}</small></details>`).join('')}</div>`
    : '';
  return `<section class="rag-assistant" aria-label="Policy assistant">
    <header class="rag-heading"><div><span class="rag-symbol" aria-hidden="true">✳</span><h3>Policy assistant</h3></div><button type="button" class="inspect-button" data-action="inspect-ai">${icon('activity')}Inspect AI</button></header>
    <div class="rag-conversation" aria-live="polite">${exchange ? `<div class="question-bubble"><span class="turn-label">You</span><p>${esc(exchange.question)}</p></div><div class="answer-bubble"><span class="turn-label">Relay</span>${status}<div class="answer-text">${esc(answer.answer)}</div>${sources}${state.preview ? '<small class="preview-note">Not saved to history</small>' : ''}</div>` : `<div class="rag-empty"><h4>What does the policy say?</h4></div>`}
      ${state.busy ? `<div class="rag-progress"><p class="working" role="status">${esc(state.progress || 'Looking up the policy…')}</p>${state.abortController ? '<button type="button" class="inspect-button" data-action="cancel-investigation">Cancel</button>' : ''}</div>` : ''}
    </div>
    <form id="ask-form" class="rag-composer"><label class="visually-hidden" for="question">Ask about this case</label><div><textarea id="question" name="question" rows="2" placeholder="Ask about this case…" minlength="3" maxlength="1500" required ${disabled()}>${esc(state.questionDraft)}</textarea><button class="btn primary" type="submit" ${disabled()}>Ask ${icon('arrow')}</button></div></form>${questionSuggestions(c)}
  </section>`;
}

function questionSuggestions(c) {
  const questions = {
    'Delivery delay': [
      ['Compensation?', 'Can this customer receive compensation for a late express delivery?'],
      ['Policy limit?', 'What is the maximum compensation allowed for this shipment?'],
      ['Approval needed?', 'Who needs to approve compensation for this case?'],
      [
        'Draft a reply',
        'Draft a short reply to this customer explaining the delay policy and next steps.',
      ],
    ],
    'Address change': [
      ['Change address?', 'Can we change this customer’s delivery address at this shipment stage?'],
      ['What to verify?', 'What details should we verify before requesting an address change?'],
      [
        'Who can help?',
        'Who should handle this address change now that the parcel is out for delivery?',
      ],
      [
        'Draft a reply',
        'Draft a short reply explaining the address-change options for this customer.',
      ],
    ],
    'Damage claim': [
      ['Photos needed?', 'What photos should we request for this damaged parcel?'],
      ['Claim details?', 'What information is required to report damage to this shipment?'],
      ['Next step?', 'Who should review this damage claim, and can we promise compensation yet?'],
      ['Draft a reply', 'Draft a short reply telling this customer how to report the damage.'],
    ],
  };
  const suggestions = questions[c.category] || [
    ['Relevant policy?', 'Which policy applies to this case?'],
    ['Next step?', 'What should the support agent do next?'],
    [
      'Draft a reply',
      'Draft a short customer reply based on the permitted policy and shipment facts.',
    ],
  ];
  return `<div class="question-suggestions" role="group" aria-label="Suggested questions">${suggestions.map(([label, question]) => `<button type="button" data-question="${esc(question)}" title="${esc(question)}" ${disabled()}>${esc(label)}</button>`).join('')}</div>`;
}

function renderInspector() {
  const answer = (state.preview || state.case?.messages.at(-1))?.answer;
  const content =
    state.inspectorTab === 'settings'
      ? `${referenceControls()}<section class="inspector-saving"><h3>Saved history</h3><label class="remember"><input id="remember-live" type="checkbox" ${state.remember ? 'checked' : ''} ${disabled()}/> Save this exchange in the case</label><p>Saved history and model context are separate. These settings apply to the next question.</p></section>`
      : !answer
        ? '<p class="inspector-empty">Ask a question first to inspect its run.</p>'
        : state.inspectorTab === 'raw'
          ? `<pre class="inspector-json" tabindex="0" aria-label="Raw execution record">${esc(JSON.stringify({ run: answer.id, provider: answer.provider, tools: answer.tools, trace: answer.trace }, null, 2))}</pre>`
          : `${runView(answer, true)}${answer.citations.length ? `<section class="inspector-sources"><h3>Source provenance</h3>${answer.citations.map((c) => `<p><strong>${esc(c.title)} · v${esc(c.version)}</strong><br/>${esc(c.id)}${c.chunk_id ? `<br/>Chunk ${esc(c.chunk_id)} · characters ${esc(c.start)}–${esc(c.end)} · retrieval score ${esc(c.score?.toFixed(4))}` : ''}</p>`).join('')}</section>` : ''}`;
  $('#ai-inspector').innerHTML =
    `<div class="inspector-header"><div><p>Case ${esc(state.selected)}</p><h2 id="inspector-title">Inspect AI</h2></div><button type="button" class="btn" data-action="close-inspector" aria-label="Close AI inspector">Close</button></div><nav class="inspector-tabs" aria-label="AI inspector views">${[
      ['run', 'Run details'],
      ['settings', 'Settings'],
      ['raw', 'Raw JSON'],
    ]
      .map(
        ([id, label]) =>
          `<button type="button" data-inspect-tab="${id}" aria-pressed="${state.inspectorTab === id}">${label}</button>`,
      )
      .join('')}</nav><div class="inspector-body">${content}</div>`;
}

function disabled() {
  return state.busy || state.actor.role === 'observer' ? 'disabled' : '';
}

function workflowView(c, latest) {
  const step =
    c.status === 'resolved'
      ? 3
      : c.status === 'awaiting_approval'
        ? 2
        : latest?.status === 'supported'
          ? 1
          : 0;
  return `<ol class="workflow" aria-label="Resolution progress">${['Investigate', 'Check evidence', 'Supervisor review', 'Resolved'].map((name, i) => `<li class="${i < step ? 'complete' : i === step ? 'current' : ''}" ${i === step ? 'aria-current="step"' : ''}><span>${i < step ? icon('check') : i + 1}</span>${name}</li>`).join('')}</ol>`;
}

function factsView(c) {
  return `<section class="case-facts" aria-label="Shipment at a glance"><div><span>Shipment status</span><strong>${esc(c.shipment.status)}</strong></div><div><span>Service & fee</span><strong>${esc(c.shipment.service)} · ${money(c.shipment.fee_naira)}</strong></div><div><span>Recorded delay</span><strong>${c.shipment.delay_hours ? esc(c.shipment.delay_hours) + ' hours' : 'No delay recorded'}</strong></div></section>`;
}

function promptView(c) {
  const paraphrases = {
    'Delivery delay': 'Can this customer receive compensation for a late express delivery?',
    'Address change': 'Can we change this customer’s delivery address?',
    'Damage claim': 'What evidence should we request for this damaged parcel?',
  };
  return `<div class="suggested-questions"><span>Try asking</span><button data-question="${esc(paraphrases[c.category] || 'What policy applies?')}" ${disabled()}>${esc(paraphrases[c.category] || 'What policy applies?')} ${icon('arrow')}</button></div>`;
}

function referenceControls() {
  if (!['openai', 'openrouter'].includes(state.provider)) return '';
  const options = state.runOptions;
  const select = (key, label, choices) =>
    `<div class="reference-option"><label for="run-${key}">${label}</label><select id="run-${key}" data-run-option="${key}" ${disabled()}>${choices.map(([value, title]) => `<option value="${value}" ${options[key] === value ? 'selected' : ''}>${title}</option>`).join('')}</select></div>`;
  return `<section class="reference-controls"><h3>Execution settings</h3><p>Compare execution choices on this same case. All tools remain read-only.</p><div class="reference-options">${select(
    'memory_mode',
    'Conversation context',
    [
      ['stateless', 'This question only'],
      ['case', 'Recent case exchanges'],
    ],
  )}${select('execution_mode', 'Execution', [
    ['workflow', 'Fixed workflow'],
    ['agent', 'Bounded agent loop'],
  ])}${select('runtime', 'Runtime', [
    ['direct', 'Direct Python'],
    ['langgraph', 'LangGraph'],
  ])}</div><p>Progress arrives during generation. The answer is shown after validation. Saving an exchange does not automatically include it in the next request.</p></section>`;
}

async function investigateQuestion(question, remember) {
  if (!['openai', 'openrouter'].includes(state.provider))
    return api('/v1/cases/' + state.selected + '/investigations', {
      method: 'POST',
      body: JSON.stringify({ question, remember }),
    });
  const controller = new AbortController();
  state.abortController = controller;
  render();
  try {
    const response = await fetch('/api/v1/cases/' + state.selected + '/runs/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': state.csrf },
      body: JSON.stringify({ question, remember, ...state.runOptions }),
      signal: controller.signal,
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error?.message || 'Investigation could not start.');
    }
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '',
      completed = null;
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
      let boundary;
      while ((boundary = buffer.indexOf('\n\n')) !== -1) {
        const frame = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        const name = frame
          .split('\n')
          .find((line) => line.startsWith('event: '))
          ?.slice(7);
        const payload = frame
          .split('\n')
          .filter((line) => line.startsWith('data: '))
          .map((line) => line.slice(6))
          .join('\n');
        if (!payload) continue;
        const data = JSON.parse(payload);
        if (name === 'failed') throw new Error(data.message);
        if (name === 'completed') completed = data;
        if (name === 'stage' || name === 'generation_progress') {
          state.progress =
            name === 'generation_progress'
              ? `Receiving answer… ${data.characters_received} characters; validation follows.`
              : `Working: ${{ 'relay.investigation': 'investigating the case', memory: 'loading chosen context', retrieval: 'finding permitted evidence', query_or_document_embedding: 'preparing policy search', vector_search: 'matching policy passages', tool_workflow: 'checking the shipment', agent_loop: 'investigating available evidence', tool_selection: 'selecting a read-only check', agent_planning: 'considering the next check', get_shipment: 'reading this shipment', read_policy_chunk: 'reading policy evidence', answer_generation: 'drafting the answer', output_validation: 'validating the answer' }[data.name] || 'checking the case'}…`;
          const status = $('.working');
          if (status) status.textContent = state.progress;
        }
      }
    }
    if (!completed)
      throw new Error(
        'Connection ended before a validated result arrived. Refresh the case before retrying.',
      );
    return completed;
  } catch (error) {
    if (error.name === 'AbortError')
      throw new Error('Investigation cancelled. Refresh the case before retrying.');
    throw error;
  } finally {
    state.abortController = null;
    state.progress = '';
  }
}

function runView(answer, expanded = false) {
  const trace = answer.trace;
  return `<details class="run-summary" ${expanded ? 'open' : ''}><summary>${icon('activity')}How this answer was prepared<span>${answer.provider === 'openrouter' ? 'OpenAI via OpenRouter' : answer.provider === 'openai' ? 'OpenAI' : 'Fixture'}</span></summary><div class="run-summary-body"><ol>${answer.tools.map((t) => `<li><span class="tool-check">${icon('check')}</span><div><strong>${t.name === 'get_shipment' ? 'Checked this shipment' : t.name === 'read_policy_chunk' ? 'Read a permitted policy passage' : 'Searched permitted policies'}</strong><small>${esc(t.status)}${t.result?.source_ids ? ' · ' + t.result.source_ids.length + ' sources' : ''}</small></div></li>`).join('')}</ol><dl>${trace.memory_mode ? `<div><dt>Context</dt><dd>${esc(trace.memory_mode)} · ${esc(trace.memory_exchanges)} exchanges</dd></div><div><dt>Execution / runtime</dt><dd>${esc(trace.execution_mode)} / ${esc(trace.runtime)}</dd></div>` : ''}<div><dt>Duration</dt><dd>${esc(trace.duration_ms)} ms</dd></div>${trace.embedding_calls != null ? `<div><dt>Retrieval</dt><dd>${esc(trace.retrieval || 'Unavailable')}</dd></div><div><dt>Embedding requests / tokens</dt><dd>${esc(trace.embedding_calls)} / ${trace.embedding_input_tokens == null ? 'Not measured' : esc(trace.embedding_input_tokens)}</dd></div>` : ''}<div><dt>Model requests</dt><dd>${esc(trace.model_calls ?? 0)}</dd></div><div><dt>Tokens in / out</dt><dd>${trace.input_tokens == null ? 'Not measured' : esc(trace.input_tokens) + ' / ' + esc(trace.output_tokens)}</dd></div></dl><p>${answer.provider === 'fixture' ? 'Deterministic fixture. No model call or API charge.' : answer.status === 'unavailable' ? 'The live result was not accepted. No resolution was proposed; review the policy or retry.' : trace.model_calls === 0 ? 'No answer-generation model was called because no permitted policy evidence matched. Query embedding usage is recorded separately.' : 'Schema and citation IDs validated. Review evidence to confirm the answer’s claims. API cost is not estimated.'}</p>${trace.stages?.length ? `<ol class="stage-timeline" aria-label="Execution stages">${trace.stages.map((stage) => `<li><span>${esc(stage.name.replaceAll('_', ' '))}</span><small>${esc(stage.status)} · ${esc(stage.duration_ms)} ms</small></li>`).join('')}</ol>` : ''}</div></details>`;
}

function answerView(answer) {
  return `<div class="case-meta"><span class="pill ${answer.status === 'insufficient_evidence' ? 'waiting' : answer.status === 'unavailable' ? 'failed' : ''}">${answer.status === 'supported' ? 'Policy evidence found' : answer.status === 'unavailable' ? 'Investigation unavailable' : 'More evidence needed'}</span></div><div class="answer-text">${esc(answer.answer)}</div>
  ${answer.citations.length ? `<div class="evidence" aria-label="Policy evidence">${answer.citations.map((c, i) => `<details><summary><span class="source-number">${i + 1}</span>${esc(c.title)} · v${esc(c.version)}</summary><p>${esc(c.excerpt)}</p>${c.chunk_id ? `<small>Source ${esc(c.id)} · characters ${esc(c.start)}–${esc(c.end)} · retrieval score ${esc(c.score?.toFixed(4))}</small>` : ''}</details>`).join('')}</div>` : ''}
  ${runView(answer)}<details class="run-details"><summary>Technical record · ${answer.tools.length} checks</summary><pre>${esc(JSON.stringify({ run: answer.id, provider: answer.provider, tools: answer.tools, trace: answer.trace }, null, 2))}</pre></details>`;
}

function proposalView(proposals, latest, c) {
  const proposal = proposals[0];
  if (proposal?.status === 'pending')
    return `<section class="resolution" aria-label="Pending resolution"><h3>A resolution is ready for review</h3><span class="amount">${money(proposal.amount)}</span><p>${esc(proposal.rationale)}</p><p>Service credit · awaiting supervisor approval. Nothing has been credited yet.</p><div class="actions">${state.actor.role === 'supervisor' ? `<button class="btn primary" data-action="review">Review proposal ${icon('arrow')}</button>` : '<span class="muted">Use the demo persona menu to continue as Amara, the supervisor.</span>'}</div></section>`;
  if (c.status === 'resolved')
    return `<section class="resolution done" aria-label="Resolved case"><h3>Resolution approved</h3><span class="amount">${money(proposal.amount)}</span><p>Recorded once in the local service-credit ledger. No money was transferred.</p><p>Supervisor decision: ${esc(proposal.decision_reason)}</p></section>`;
  let html =
    proposal?.status === 'rejected'
      ? `<section class="resolution"><h3>Proposal returned for revision</h3><p>${esc(proposal.decision_reason)}</p></section>`
      : '';
  if (latest?.suggested_credit_naira && c.status === 'open')
    html += `<section class="resolution"><h3>A possible next step</h3><p>Propose a service credit within the policy limit. A supervisor will review the exact amount and reason.</p><div class="actions"><button class="btn primary" data-action="propose" ${disabled()}>Propose a service credit ${icon('arrow')}</button></div></section>`;
  return html;
}

function shipmentView(c) {
  const s = c.shipment;
  return `<section class="shipment" aria-label="Shipment details"><dl class="shipment-grid">${[
    ['Shipment', s.id],
    ['Current status', s.status],
    ['Service', s.service],
    ['Delivery fee', money(s.fee_naira)],
    ['Delay', s.delay_hours + ' hours'],
    ['Route', c.route],
  ]
    .map(([k, v]) => `<div><dt>${k}</dt><dd>${esc(v)}</dd></div>`)
    .join(
      '',
    )}</dl><h3>Shipment timeline</h3><ol class="timeline">${s.events.map((e) => `<li>${esc(e)}</li>`).join('')}</ol><p class="muted">Fixture records · no carrier network request</p></section>`;
}

function historyView(messages) {
  if (!messages.length)
    return '<div class="empty-state">No saved exchanges yet. Investigate this case to begin.</div>';
  return `<div class="actions"><button class="btn danger" data-action="forget" ${disabled()}>Delete saved exchanges</button></div>${messages.map((m) => `<div class="history-item"><strong>${esc(m.question)}</strong><p>${esc(m.answer.answer)}</p></div>`).join('')}`;
}

function knowledgeView() {
  return `<section class="library" aria-label="Published policies">${state.docs.map((d) => `<article class="doc-card"><div class="doc-meta">${icon('book').replace('<svg ', '<svg width="15" height="15" ')} ${esc(d.id)} <span class="pill">Published · v${esc(d.version)}</span></div><h2>${esc(d.title)}</h2><p>${esc(d.text)}</p><div class="actions"><span class="pill">${d.visibility === 'supervisor' ? 'Supervisor access' : 'Team access'}</span><span class="muted">Original synthetic workshop policy</span></div></article>`).join('')}</section>`;
}

function activityView() {
  const labels = {
    'investigation.completed': 'Case investigated',
    'credit.proposed': 'Service credit proposed',
    'credit.approved': 'Service credit approved',
    'credit.rejected': 'Service credit returned',
    'memory.deleted': 'Saved exchanges deleted',
  };
  return `<section class="activity-list" aria-label="Decision activity">${state.activity.length ? state.activity.map((e) => `<article class="activity-row"><span class="metric-icon">${icon(e.event.includes('approved') ? 'check' : 'activity')}</span><div><h3>${esc(labels[e.event] || e.event)}</h3><p>${esc(e.actor)} · ${esc(e.metadata.case_id || 'Workspace')}</p><details><summary>View record</summary><pre>${esc(JSON.stringify(e.metadata, null, 2))}</pre></details></div><small>${new Date(e.created * 1000).toLocaleTimeString('en-NG', { hour: '2-digit', minute: '2-digit' })}</small></article>`).join('') : '<div class="empty-state">Your activity will appear here as you investigate and resolve cases.</div>'}</section>`;
}

async function busy(task) {
  if (state.busy) return;
  state.busy = true;
  render();
  try {
    await task();
  } catch (error) {
    notify(error.message);
  } finally {
    state.busy = false;
    render();
  }
}

function showProposal() {
  const max = (state.preview?.answer || state.case.messages.at(-1)?.answer).suggested_credit_naira;
  $('#action-dialog').innerHTML =
    `<form id="proposal-form" class="dialog-body"><h2 id="dialog-title">Propose a service credit</h2><p>The maximum for this shipment is ${money(max)}. A supervisor must approve your proposal before it is recorded.</p><label for="amount">Amount in naira</label><input id="amount" name="amount" type="number" min="100" max="${max}" value="${max}" required/><label for="rationale">Reason for the credit</label><textarea id="rationale" name="rationale" minlength="10" maxlength="1000" required>Express shipment delivered 48 hours late; service credit within the published policy limit.</textarea><div class="inline-error" role="alert"></div><div class="actions"><button class="btn" type="button" data-action="close">Cancel</button><button class="btn primary" type="submit">Submit for approval</button></div></form>`;
  $('#action-dialog').showModal();
}

function showReview() {
  const p = state.case.proposals[0];
  $('#action-dialog').innerHTML =
    `<form id="review-form" class="dialog-body"><h2 id="dialog-title">Review this resolution</h2><p>${esc(state.case.case.id)} · ${esc(state.case.case.customer)}</p><div class="review-amount">${money(p.amount)}<small>Service credit · local ledger only</small></div><p>${esc(p.rationale)}</p><label for="decision-reason">Your decision note</label><textarea id="decision-reason" name="reason" minlength="5" maxlength="500" required>Reviewed shipment and policy. Amount is within the approved limit.</textarea><div class="inline-error" role="alert"></div><div class="actions"><button class="btn" type="button" data-action="close">Cancel</button><button class="btn danger" name="decision" value="reject" type="submit">Return for revision</button><button class="btn primary" name="decision" value="approve" type="submit">Approve ${money(p.amount)}</button></div></form>`;
  $('#action-dialog').showModal();
}

document.addEventListener('click', async (event) => {
  const button = event.target.closest('button');
  if (!button || button.disabled) return;
  if (button.dataset.action === 'cancel-investigation') {
    state.abortController?.abort();
    return;
  }
  if (button.dataset.action === 'inspect-ai') {
    state.inspectorTab = 'run';
    renderInspector();
    $('#ai-inspector').showModal();
    return;
  }
  if (button.dataset.action === 'close-inspector') {
    $('#ai-inspector').close();
    return;
  }
  if (button.dataset.inspectTab) {
    state.inspectorTab = button.dataset.inspectTab;
    renderInspector();
    $(`[data-inspect-tab="${state.inspectorTab}"]`).focus();
    return;
  }
  if (button.dataset.question) {
    state.questionDraft = button.dataset.question;
    $('#question').value = state.questionDraft;
    $('#question').focus();
    return;
  }
  if (button.dataset.page) {
    state.page = button.dataset.page;
    render();
    return;
  }
  if (button.dataset.filter) {
    state.filter = button.dataset.filter;
    render();
    return;
  }
  if (button.dataset.tab) {
    state.tab = button.dataset.tab;
    render();
    return;
  }
  if (button.dataset.case) {
    await busy(async () => {
      state.preview = null;
      state.questionDraft = '';
      state.selected = button.dataset.case;
      state.mobileDetail = true;
      state.tab = 'conversation';
      state.case = await api('/v1/cases/' + state.selected);
    });
    return;
  }
  const action = button.dataset.action;
  if (action === 'retry') {
    await boot();
    return;
  }
  if (action === 'back') {
    state.mobileDetail = false;
    render();
    return;
  }
  if (action === 'close') {
    $('#action-dialog').close();
    return;
  }
  if (action === 'propose') {
    showProposal();
    return;
  }
  if (action === 'review') {
    showReview();
    return;
  }
  if (action === 'forget') {
    await busy(async () => {
      await api('/v1/cases/' + state.selected + '/memory', { method: 'DELETE' });
      await load();
      notify('Saved exchanges deleted. Decision audit records are retained.');
    });
    return;
  }
  if (action === 'investigate')
    await busy(async () => {
      const questions = {
        'Delivery delay': ['openai', 'openrouter'].includes(state.provider)
          ? 'Can this customer receive compensation for a late express delivery?'
          : 'delivery service credit policy',
        'Address change': 'delivery address changes',
        'Damage claim': 'damage evidence claims',
      };
      await investigateQuestion(questions[state.case.case.category], true);
      await load();
      notify('Shipment and policy checked. Review the evidence below.');
    });
});

document.addEventListener('input', (event) => {
  if (event.target.id === 'question') state.questionDraft = event.target.value;
  if (event.target.id === 'case-search') {
    state.search = event.target.value;
    $('#case-list').innerHTML = caseList();
  }
});

document.addEventListener('change', async (event) => {
  if (event.target.id === 'remember-live') state.remember = event.target.checked;
  if (event.target.dataset.runOption)
    state.runOptions[event.target.dataset.runOption] = event.target.value;
  if (event.target.id === 'persona') {
    const role = event.target.value;
    await busy(async () => {
      const session = await api('/v1/demo/session', {
        method: 'POST',
        body: JSON.stringify({ role }),
      });
      state.actor = session.actor;
      state.runOptions.memory_mode = 'stateless';
      state.preview = null;
      state.questionDraft = '';
      state.csrf = session.csrf_token;
      state.case = null;
      state.cases = [];
      state.docs = [];
      state.activity = [];
      await load();
      notify('Demo persona changed. Your workspace is preserved.');
    });
  }
});

document.addEventListener('submit', async (event) => {
  const form = event.target;
  if (!['ask-form', 'proposal-form', 'review-form'].includes(form.id)) return;
  event.preventDefault();
  const data = new FormData(form);
  if (form.id === 'ask-form') {
    const question = data.get('question'),
      remember = ['openai', 'openrouter'].includes(state.provider)
        ? state.remember
        : data.has('remember');
    await busy(async () => {
      const answer = await investigateQuestion(question, remember);
      await load();
      if (!remember) {
        state.preview = { question, answer };
      }
      state.questionDraft = '';
      if (!['openai', 'openrouter'].includes(state.provider))
        notify(
          remember
            ? 'Exchange saved to this case.'
            : 'Exchange shown only for this view; it was not saved.',
        );
    });
    return;
  }
  if (form.dataset.submitting) return;
  form.dataset.submitting = 'true';
  const key = crypto.randomUUID();
  form.querySelectorAll('button[type="submit"]').forEach((b) => (b.disabled = true));
  try {
    if (form.id === 'proposal-form')
      await api('/v1/cases/' + state.selected + '/proposals', {
        method: 'POST',
        headers: { 'Idempotency-Key': key },
        body: JSON.stringify({
          amount_naira: Number(data.get('amount')),
          rationale: data.get('rationale'),
          case_version: state.case.case.version,
        }),
      });
    else
      await api('/v1/proposals/' + state.case.proposals[0].id + '/decision', {
        method: 'POST',
        headers: { 'Idempotency-Key': key },
        body: JSON.stringify({ decision: event.submitter.value, reason: data.get('reason') }),
      });
    $('#action-dialog').close();
    await load();
    notify(
      form.id === 'proposal-form'
        ? 'Proposal submitted. A supervisor can now review it.'
        : 'Decision recorded in the local ledger.',
    );
  } catch (error) {
    form.querySelector('.inline-error').textContent = error.message;
  } finally {
    delete form.dataset.submitting;
    form.querySelectorAll('button[type="submit"]').forEach((b) => (b.disabled = false));
  }
});

boot();

$('#ai-inspector').addEventListener('close', () => {
  $('#ai-inspector').replaceChildren();
});
$('#ai-inspector').addEventListener('click', (event) => {
  const dialog = event.currentTarget;
  const bounds = dialog.getBoundingClientRect();
  if (
    event.target === dialog &&
    (event.clientX < bounds.left ||
      event.clientX > bounds.right ||
      event.clientY < bounds.top ||
      event.clientY > bounds.bottom)
  )
    dialog.close();
});
