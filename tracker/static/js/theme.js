/* Theme handling: respects OS preference, persists in localStorage, applies before paint via inline head script. */
(function() {
  function getPreferredTheme() {
    var stored = localStorage.getItem('theme');
    if (stored === 'light' || stored === 'dark') return stored;
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
      return 'dark';
    }
    return 'light';
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
  }

  // Apply immediately if inline script not already did
  var current = document.documentElement.getAttribute('data-theme');
  if (!current) {
    applyTheme(getPreferredTheme());
  }

  // Expose toggle
  window.toggleTheme = function() {
    var current = document.documentElement.getAttribute('data-theme') || 'light';
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('theme', next);
    // Dispatch event for charts to re-render
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: next }}));
    updateLabel(next);
  };

  function updateLabel(theme) {
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
    }
  }

  document.addEventListener('DOMContentLoaded', function() {
    var theme = document.documentElement.getAttribute('data-theme') || getPreferredTheme();
    updateLabel(theme);
    var btn = document.getElementById('theme-toggle');
    if (btn) {
      btn.addEventListener('click', window.toggleTheme);
    }
    // Also mobile toggle
    var btnM = document.getElementById('theme-toggle-mobile');
    if (btnM) {
      btnM.textContent = theme === 'dark' ? 'Light mode' : 'Dark mode';
      btnM.addEventListener('click', function() {
        window.toggleTheme();
        // Sync both labels
        var t = document.documentElement.getAttribute('data-theme');
        if (btn) btn.textContent = t === 'dark' ? 'Light mode' : 'Dark mode';
        btnM.textContent = t === 'dark' ? 'Light mode' : 'Dark mode';
      });
    }
  });
})();
