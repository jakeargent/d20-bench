// Theme behaviour shared with the personal site's Paper layout.
const root = document.documentElement;
const toggle = document.getElementById('theme-toggle');
function updateThemeLabel() {
  const next = root.dataset.theme === 'dark' ? 'light' : 'dark';
  toggle.textContent = next === 'light' ? 'Light' : 'Dark';
  toggle.setAttribute('aria-label', `Switch to ${next} theme`);
}
updateThemeLabel();
toggle.addEventListener('click', () => {
  root.dataset.theme = root.dataset.theme === 'dark' ? 'light' : 'dark';
  updateThemeLabel();
  try { localStorage.theme = root.dataset.theme; } catch {}
});
