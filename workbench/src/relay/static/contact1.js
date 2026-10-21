// Local presentation controls only. No provider calls, telemetry or remote dependencies.
// Hosted demonstrations use the current service; local rehearsal keeps its explicit ports.
if (!['127.0.0.1', 'localhost', '[::1]'].includes(location.hostname)) {
  document.querySelectorAll('.demo-links a').forEach((link) => {
    const target = new URL(link.href);
    if (target.hostname === '127.0.0.1' && target.port === '8002') {
      link.href = location.origin + target.pathname;
    }
  });
}
const conceptsOnly = document.body.dataset.deckMode === 'concepts';
const slides = [...document.querySelectorAll('.slide')];
const outline = document.querySelector('#outline');
const outlineList = document.querySelector('#outline-list');
const notesButton = document.querySelector('#notes-button');
let current = 0;
let showNotes = new URLSearchParams(location.search).get('notes') === '1';
let elapsed = 0;
let startedAt = null;

function announce(message) {
  document.querySelector('#announcement').textContent = message;
}

function render(focus = false) {
  let requested = '';
  try {
    requested = decodeURIComponent(location.hash.slice(1));
  } catch {
    /* Invalid fragments return to the opening slide. */
  }
  const found = slides.findIndex((slide) => slide.id === requested);
  current = found >= 0 ? found : 0;
  slides.forEach((slide, index) => {
    slide.hidden = index !== current;
    const notes = slide.querySelector('.speaker-notes');
    if (notes) notes.hidden = !showNotes;
  });
  document.body.classList.toggle('showing-notes', showNotes);
  const slide = slides[current];
  document.querySelectorAll('#slide-dots button').forEach((button, index) => {
    button.tabIndex = index === current ? 0 : -1;
    if (index === current) button.setAttribute('aria-current', 'step');
    else button.removeAttribute('aria-current');
  });
  document.querySelector('#slide-counter').textContent = `${current + 1} / ${slides.length}`;
  document.querySelector('#phase-label').textContent = slide.dataset.phase;
  document.querySelector('#planned-time').textContent = slide.dataset.time;
  document.querySelector('#deck-progress').max = slides.length;
  document.querySelector('#deck-progress').value = current + 1;
  document.querySelector('#previous-slide').disabled = current === 0;
  document.querySelector('#next-slide').disabled = current === slides.length - 1;
  notesButton.setAttribute('aria-pressed', String(showNotes));
  outlineList.querySelectorAll('[data-slide]').forEach((button) => {
    if (button.dataset.slide === slide.id) button.setAttribute('aria-current', 'true');
    else button.removeAttribute('aria-current');
  });
  document.title = `${slide.dataset.title} — Contact 1${conceptsOnly ? ' concepts' : ''} · Relay`;
  announce(
    `Slide ${current + 1} of ${slides.length}. ${slide.dataset.phase}. ${slide.dataset.title}.`,
  );
  if (focus) {
    const heading = slide.querySelector('h1, h2');
    heading.tabIndex = -1;
    heading.focus({ preventScroll: true });
    window.scrollTo(0, 0);
  }
}

function goTo(index) {
  const target = slides[Math.max(0, Math.min(index, slides.length - 1))];
  if (target.id === location.hash.slice(1)) render(true);
  else {
    location.hash = target.id;
    render(true);
  }
}

function toggleNotes() {
  showNotes = !showNotes;
  const url = new URL(location.href);
  if (showNotes) url.searchParams.set('notes', '1');
  else url.searchParams.delete('notes');
  history.replaceState(null, '', url);
  render();
}

function showOutline() {
  if (!outline.open) outline.showModal();
  outlineList.querySelector('[aria-current="true"]')?.scrollIntoView({ block: 'center' });
}

async function fullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (document.documentElement.requestFullscreen)
      await document.documentElement.requestFullscreen();
    else
      announce('Fullscreen is unavailable in this browser. Use the browser presentation controls.');
  } catch {
    announce('Fullscreen is unavailable here. The presentation remains usable in this window.');
  }
}

const dots = document.querySelector('#slide-dots');
slides.forEach((slide, index) => {
  const button = document.createElement('button');
  button.type = 'button';
  button.setAttribute('aria-label', `Go to slide ${index + 1}`);
  button.title = slide.dataset.title;
  button.addEventListener('click', () => goTo(index));
  dots.append(button);
});

let lastPhase;
slides.forEach((slide, index) => {
  if (slide.dataset.phase !== lastPhase) {
    const heading = document.createElement('h3');
    heading.className = 'outline-group';
    heading.textContent = conceptsOnly
      ? 'Contact 1 / Concepts'
      : slide.dataset.phase === 'Concepts'
        ? 'Concepts / 00–15 min'
        : slide.dataset.phase === 'Demo'
          ? 'Guided demonstration / 15–60 min'
          : 'Appendix / reference outside the timed sequence';
    outlineList.append(heading);
    lastPhase = slide.dataset.phase;
  }
  const button = document.createElement('button');
  button.type = 'button';
  button.dataset.slide = slide.id;
  const number = document.createElement('span');
  number.textContent = String(index + 1).padStart(2, '0');
  const title = document.createElement('span');
  title.textContent = slide.dataset.title;
  const time = document.createElement('small');
  time.textContent = slide.dataset.time;
  button.append(number, title, time);
  button.addEventListener('click', () => {
    outline.close();
    goTo(index);
  });
  outlineList.append(button);
});

document.querySelector('#previous-slide').addEventListener('click', () => goTo(current - 1));
document.querySelector('#next-slide').addEventListener('click', () => goTo(current + 1));
document.querySelector('#outline-button').addEventListener('click', showOutline);
document.querySelector('#close-outline').addEventListener('click', () => outline.close());
notesButton.addEventListener('click', toggleNotes);
document.querySelector('#fullscreen-button').addEventListener('click', fullscreen);
document.querySelector('#print-button').addEventListener('click', () => window.print());
window.addEventListener('hashchange', () => render(true));
document.addEventListener('keydown', (event) => {
  if (
    event.altKey ||
    event.ctrlKey ||
    event.metaKey ||
    /INPUT|TEXTAREA|SELECT/.test(event.target.tagName) ||
    event.target.isContentEditable ||
    outline.open
  )
    return;
  const key = event.key.toLowerCase();
  if (['arrowright', 'pagedown'].includes(key)) {
    event.preventDefault();
    goTo(current + 1);
  } else if (['arrowleft', 'pageup'].includes(key)) {
    event.preventDefault();
    goTo(current - 1);
  } else if (key === 'home') {
    event.preventDefault();
    goTo(0);
  } else if (key === 'end') {
    event.preventDefault();
    goTo(slides.length - 1);
  } else if (key === 'n') {
    event.preventDefault();
    toggleNotes();
  } else if (key === 'g') {
    event.preventDefault();
    showOutline();
  } else if (key === 'f') {
    event.preventDefault();
    fullscreen();
  }
});

function updateTimer() {
  const milliseconds = elapsed + (startedAt === null ? 0 : performance.now() - startedAt);
  const total = Math.floor(milliseconds / 1000);
  document.querySelector('#timer').textContent =
    `${String(Math.floor(total / 60)).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`;
}

document.querySelector('#timer-button').addEventListener('click', () => {
  if (startedAt === null) {
    startedAt = performance.now();
    document.querySelector('#timer-button').textContent = 'Pause timer';
  } else {
    elapsed += performance.now() - startedAt;
    startedAt = null;
    document.querySelector('#timer-button').textContent = 'Resume timer';
  }
  updateTimer();
});
document.querySelector('#reset-timer').addEventListener('click', () => {
  elapsed = 0;
  startedAt = null;
  document.querySelector('#timer-button').textContent = 'Start timer';
  updateTimer();
});
setInterval(updateTimer, 1000);
render();

let copyStatusTimer;
document.querySelectorAll('[data-code-location]').forEach((button) => {
  button.addEventListener('click', async () => {
    const status = document.querySelector('#code-copy-status');
    clearTimeout(copyStatusTimer);
    try {
      await navigator.clipboard.writeText(button.dataset.codeLocation);
      status.textContent = `Copied ${button.dataset.codeLocation}. Paste into your editor’s file search.`;
    } catch {
      status.textContent = `Copy this location into your editor: ${button.dataset.codeLocation}`;
    }
    status.hidden = false;
    copyStatusTimer = setTimeout(() => {
      status.hidden = true;
    }, 5000);
  });
});
