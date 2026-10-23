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
