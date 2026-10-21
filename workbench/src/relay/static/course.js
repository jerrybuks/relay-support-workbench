// Course context only: no provider calls, telemetry or remote dependencies.
const contextDialog = document.querySelector('#project-context');
const contextButton = document.querySelector('#open-project-context');
contextButton.addEventListener('click', () => {
  contextDialog.showModal();
  contextDialog.querySelector('.context-modal-body').scrollTop = 0;
  document.body.classList.add('context-open');
});
contextDialog.addEventListener('close', () => {
  document.body.classList.remove('context-open');
});
contextDialog.addEventListener('click', (event) => {
  if (event.target !== contextDialog) return;
  const rect = contextDialog.getBoundingClientRect();
  if (
    event.clientX < rect.left ||
    event.clientX > rect.right ||
    event.clientY < rect.top ||
    event.clientY > rect.bottom
  )
    contextDialog.close();
});
