const select = document.querySelector('#document');
const status = document.querySelector('#status');
const checkbox = document.querySelector('#billable');
const importButton = document.querySelector('#ingest');
let previewed = null;
let busy = false;
function update() {
  importButton.disabled = busy || !checkbox.checked || previewed !== select.value;
}
select.addEventListener('change', () => {
  previewed = null;
  checkbox.checked = false;
  update();
});
checkbox.addEventListener('change', update);
async function run(execute) {
  busy = true;
  update();
  document.querySelector('#preview').disabled = true;
  status.textContent = execute
    ? 'Embedding and storing the approved policy…'
    : 'Checking metadata and approval; previewing chunks…';
  try {
    const current = await fetch('/api/v1/session').then((r) => r.json());
    const headers = { 'Content-Type': 'application/json' };
    if (current.csrf_token) headers['X-CSRF-Token'] = current.csrf_token;
    const sessionResponse = await fetch('/api/v1/demo/session', {
      method: 'POST',
      headers,
      body: JSON.stringify({ role: 'supervisor' }),
    });
    const session = await sessionResponse.json();
    if (!sessionResponse.ok)
      throw new Error(session.error?.message || 'Cannot start supervisor session.');
    const response = await fetch('/api/v1/teaching/policies', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRF-Token': session.csrf_token },
      body: JSON.stringify({
        document: select.value,
        execute,
        confirm_billable: execute && checkbox.checked,
      }),
    });
    const result = await response.json();
    document.querySelector('#output').hidden = false;
    document.querySelector('#result').textContent = JSON.stringify(result, null, 2);
    const summary = document.querySelector('#source-summary');
    const passages = document.querySelector('#passages');
    passages.replaceChildren();
    summary.textContent = '';
    document.querySelector('#output-title').textContent = response.ok
      ? execute
        ? 'Policy indexed'
        : 'Document and chunks'
      : 'Document could not be processed';
    if (!response.ok) throw new Error(result.error?.message || 'Request failed.');
    if (execute) {
      summary.textContent = `${result.source_id} · version ${result.source_version}. Import complete: ${result.embedding_calls} embedding requests. Ask your question in Relay and check its source.`;
    } else {
      const source = result.source;
      summary.textContent = `${source.title} · ${source.id} · version ${source.version} · ${source.visibility} access. ${result.chunks.length} chunks; no embedding requests yet.`;
      for (const [index, chunk] of result.chunks.entries()) {
        const card = document.createElement('article');
        card.className = 'passage';
        const heading = document.createElement('h3');
        heading.textContent = `Chunk ${index + 1}`;
        const text = document.createElement('p');
        text.textContent = chunk.excerpt;
        card.append(heading, text);
        passages.append(card);
      }
    }
    previewed = select.value;
    status.textContent = execute
      ? 'Imported. Open the resolution desk and check the cited answer.'
      : `Preview ready: ${result.chunks.length} chunks; no embedding calls.`;
  } catch (error) {
    previewed = null;
    status.textContent = error.message;
  } finally {
    busy = false;
    update();
    document.querySelector('#preview').disabled = false;
  }
}
document.querySelector('#preview').addEventListener('click', () => run(false));
importButton.addEventListener('click', () => run(true));

let copyFeedbackTimer;
document.querySelectorAll('[data-code-location]').forEach((button) => {
  button.addEventListener('click', async () => {
    const feedback = document.querySelector('#code-copy-status');
    clearTimeout(copyFeedbackTimer);
    feedback.hidden = false;
    try {
      await navigator.clipboard.writeText(button.dataset.codeLocation);
      feedback.textContent = `Copied ${button.dataset.codeLocation}`;
      copyFeedbackTimer = setTimeout(() => {
        feedback.hidden = true;
      }, 4000);
    } catch {
      feedback.textContent = `Copy this location: ${button.dataset.codeLocation}`;
    }
  });
});
