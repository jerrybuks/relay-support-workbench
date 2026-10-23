(() => {
  const $ = (id) => document.getElementById(id);
  let upload = null;
  let busy = false;
  let sessionRequest;
  const status = (text) => {
    $('pdf-status').textContent = text;
  };
  const update = () => {
    $('pdf-index').disabled =
      busy || !upload || !$('pdf-reviewed').checked || !$('pdf-billable').checked;
    $('pdf-upload').disabled = busy;
    $('pdf-ask').disabled = busy;
    $('pdf-refresh').disabled = busy;
    document.querySelectorAll('[data-remove-policy]').forEach((button) => {
      button.disabled = busy;
    });
    for (const id of ['pdf-file', 'pdf-title', 'pdf-access', 'pdf-reviewed', 'pdf-billable'])
      $(id).disabled = busy;
  };
  function session() {
    sessionRequest ??= startSession().finally(() => {
      sessionRequest = null;
    });
    return sessionRequest;
  }
  async function startSession() {
    let current = await fetch('/api/v1/session').then((r) => r.json());
    if (current.actor?.role === 'supervisor') return current.csrf_token;
    const response = await fetch('/api/v1/demo/session', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(current.csrf_token ? { 'X-CSRF-Token': current.csrf_token } : {}),
      },
      body: JSON.stringify({ role: 'supervisor' }),
    });
    current = await response.json();
    if (!response.ok)
      throw new Error(current.error?.message || 'Cannot start the workshop session.');
    return current.csrf_token;
  }
  async function request(url, csrf, body, contentType = 'application/json', method = 'POST') {
    const response = await fetch(url, {
      method,
      headers: { 'Content-Type': contentType, 'X-CSRF-Token': csrf },
      body: contentType === 'application/pdf' ? body : JSON.stringify(body),
    });
    const result = await response.json();
    if (!response.ok) throw new Error(result.error?.message || 'Request failed.');
    return result;
  }
  function retrievalScores(item, mode) {
    const text = Number.isFinite(item.vector_score)
      ? `Cosine similarity: ${item.vector_score.toFixed(3)}`
      : 'Cosine similarity: unavailable';
    const score = document.createElement('p');
    score.className = 'hint';
    score.textContent =
      mode === 'hybrid' && Number.isFinite(item.score)
        ? `${text} · Hybrid rank (RRF): ${item.score.toFixed(5)}`
        : text;
    return score;
  }
  function passages(container, items, mode = null) {
    container.replaceChildren();
    for (const [index, item] of items.entries()) {
      const card = document.createElement('article');
      card.className = 'passage';
      const heading = document.createElement('h3');
      heading.textContent = `Chunk ${index + 1}${item.title ? ' · ' + item.title : ''}`;
      const text = document.createElement('p');
      text.textContent = item.excerpt;
      card.append(heading);
      if (mode) card.append(retrievalScores(item, mode));
      card.append(text);
      container.append(card);
    }
  }
  function invalidate() {
    upload = null;
    $('pdf-reviewed').checked = false;
    $('pdf-billable').checked = false;
    $('pdf-pipeline').hidden = true;
    $('pdf-question-panel').hidden = true;
    $('pdf-answer').replaceChildren();
    $('pdf-hits').replaceChildren();
    $('pdf-retrieval').hidden = true;
    status('Choose Upload and inspect to process this policy.');
    update();
  }
  async function loadIndexed() {
    const list = $('pdf-indexed-list');
    try {
      await session();
      const response = await fetch('/api/v1/teaching/pdf');
      const result = await response.json();
      if (!response.ok) throw new Error(result.error?.message || 'Cannot load policies.');
      list.replaceChildren();
      if (result.policies.length) $('pdf-question-panel').hidden = false;
      if (!result.policies.length) list.textContent = 'No PDF policies indexed yet.';
      for (const policy of result.policies) {
        const row = document.createElement('article');
        row.className = 'indexed-policy';
        const title = document.createElement('p');
        title.textContent = `${policy.title} · v${policy.version} · ${policy.visibility} access`;
        const remove = document.createElement('button');
        remove.type = 'button';
        remove.className = 'remove-policy';
        remove.dataset.removePolicy = policy.id;
        remove.textContent = 'Remove policy';
        remove.setAttribute('aria-label', `Remove policy: ${policy.title}`);
        remove.addEventListener('click', async () => {
          if (
            busy ||
            !window.confirm(
              `Remove “${policy.title}” and its vectors from the shared teaching corpus?`,
            )
          )
            return;
          busy = true;
          update();
          status('Removing the policy and its vectors…');
          try {
            const csrf = await session();
            await request(
              '/api/v1/teaching/pdf/' + encodeURIComponent(policy.id),
              csrf,
              { confirm_remove: true },
              'application/json',
              'DELETE',
            );
            invalidate();
            $('pdf-file').value = '';
            await loadIndexed();
            status(
              'Policy removed from the teaching corpus and vector index. Upload it again to repeat the demo.',
            );
          } catch (error) {
            status(error.message);
          } finally {
            busy = false;
            update();
          }
        });
        row.append(title, remove);
        list.append(row);
      }
      update();
    } catch (error) {
      list.textContent = error.message;
    }
  }
  $('pdf-refresh').addEventListener('click', loadIndexed);
  loadIndexed();
  for (const id of ['pdf-file', 'pdf-title', 'pdf-access'])
    $(id).addEventListener('change', invalidate);
  for (const id of ['pdf-reviewed', 'pdf-billable']) $(id).addEventListener('change', update);
  $('pdf-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    if (busy) return;
    const file = $('pdf-file').files[0];
    if (!file || file.size > 2 * 1024 * 1024) {
      status('Choose a PDF up to 2 MiB.');
      return;
    }
    invalidate();
    busy = true;
    update();
    status('Reading your PDF and splitting the extracted text…');
    try {
      const csrf = await session();
      const params = new URLSearchParams({
        title: $('pdf-title').value,
        visibility: $('pdf-access').value,
      });
      upload = await request('/api/v1/teaching/pdf?' + params, csrf, file, 'application/pdf');
      $('pdf-pipeline').hidden = false;
      $('pdf-extract-state').textContent = `${upload.pages.length} page(s) · complete`;
      $('pdf-text').textContent = upload.source.text;
      $('pdf-chunk-state').textContent = `${upload.chunks.length} chunks · complete`;
      $('pdf-chunk-settings').textContent =
        `${upload.source.id} · version ${upload.source.version} · ${upload.source.visibility} access. ${upload.chunk_settings?.size_characters ?? '—'} characters per chunk; ${upload.chunk_settings?.overlap_characters ?? '—'} characters overlap (${upload.chunk_settings?.splitter ?? 'configured'} splitter).`;
      passages($('pdf-chunks'), upload.chunks);
      $('pdf-embed-state').textContent = 'Not started';
      $('pdf-store-state').textContent = 'Not started';
      $('pdf-vector').textContent = '';
      $('pdf-stored-record').textContent = '';
      $('pdf-embedding-info').textContent = 'Each chunk will be converted into a vector.';
      $('pdf-storage-info').textContent =
        'Vectors, passages and policy details will be stored together.';
      $('pdf-extraction').open = false;
      $('pdf-chunking').open = false;
      status(
        'PDF ready. Open the extracted text and chunks below, review them, then approve indexing.',
      );
    } catch (error) {
      upload = null;
      status(error.message);
    } finally {
      busy = false;
      update();
    }
  });
  $('pdf-index').addEventListener('click', async () => {
    if (busy || !upload) return;
    busy = true;
    update();
    status('Creating embeddings and writing the Qdrant index…');
    try {
      const csrf = await session();
      const base = '/api/v1/teaching/pdf/' + upload.upload_id;
      await request(base + '/review', csrf, { confirm_reviewed: true });
      const result = await request(base + '/index', csrf, { confirm_billable: true });
      $('pdf-embed-state').textContent = 'Complete';
      $('pdf-store-state').textContent = 'Complete';
      $('pdf-embedding-info').textContent =
        `${result.model} · ${result.records[0]?.dimensions || 0} dimensions · ${result.embedding_calls} new embedding request(s). Unchanged chunks reuse vectors.`;
      $('pdf-vector').textContent = JSON.stringify(
        {
          chunk_id: result.records[0]?.point_id,
          first_six_values: result.records[0]?.vector_preview,
        },
        null,
        2,
      );
      $('pdf-storage-info').textContent =
        `${result.stored_chunks} policy chunks stored in Qdrant collection ${result.collection}.`;
      $('pdf-stored-record').textContent = JSON.stringify(result.records[0], null, 2);
      $('pdf-embedding').open = false;
      $('pdf-storage').open = false;
      $('pdf-question-panel').hidden = false;
      status('Policy indexed. Ask a question below to see retrieval and the grounded answer.');
      await loadIndexed();
    } catch (error) {
      status(error.message);
    } finally {
      busy = false;
      update();
    }
  });
  $('pdf-ask').addEventListener('click', async () => {
    if (busy) return;
    const question = $('pdf-question').value.trim();
    if (question.length < 3) {
      status('Enter a question of at least three characters.');
      return;
    }
    busy = true;
    update();
    $('pdf-answer').replaceChildren();
    $('pdf-hits').replaceChildren();
    $('pdf-retrieval').hidden = true;
    status('Finding relevant passages and preparing the answer…');
    try {
      const csrf = await session();
      const data = await request('/api/v1/policies/query', csrf, { question });
      const retrievalMode = data.trace?.retrieval || 'unknown';
      passages($('pdf-hits'), data.retrieved_passages || [], retrievalMode);
      $('pdf-retrieval').hidden = false;
      $('pdf-retrieval').open = true;

      const answer = document.createElement('p');
      answer.textContent = data.answer;
      $('pdf-answer').append(answer);
      for (const citation of data.citations || []) {
        const details = document.createElement('details');
        const label = document.createElement('summary');
        label.textContent = `Source: ${citation.title} · v${citation.version}`;
        const quote = document.createElement('blockquote');
        quote.textContent = citation.excerpt;
        details.append(label, retrievalScores(citation, retrievalMode), quote);
        $('pdf-answer').append(details);
      }
      status(
        data.status === 'supported'
          ? 'Answer ready. Expand its source to check the supporting text.'
          : 'A supported answer was not available. Review the result and retrieved passages.',
      );
    } catch (error) {
      status(error.message);
    } finally {
      busy = false;
      update();
    }
  });
})();
