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

  function getCurrentTheme() {
    return document.documentElement.getAttribute('data-theme') || getPreferredTheme();
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
    // Update aria-checked on all switches
    var isDark = theme === 'dark';
    document.querySelectorAll('.theme-switch[role="switch"]').forEach(function(btn) {
      btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
    });
    // Dispatch event for charts to re-render
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme: theme }}));
  }

  // Expose toggle for other scripts if needed
  window.toggleTheme = function() {
    var current = getCurrentTheme();
    var next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
  };

  // Ensure aria-checked reflects initial theme as soon as DOM is parsed
  // (CSS already drives knob position from [data-theme], but JS must set aria-checked)
  function syncSwitches() {
    var theme = getCurrentTheme();
    var isDark = theme === 'dark';
    document.querySelectorAll('.theme-switch[role="switch"]').forEach(function(btn) {
      btn.setAttribute('aria-checked', isDark ? 'true' : 'false');
    });
  }

  document.addEventListener('DOMContentLoaded', function() {
    syncSwitches();
    // Attach click handlers to both switches
    document.querySelectorAll('#theme-toggle, #theme-toggle-mobile').forEach(function(btn) {
      btn.addEventListener('click', window.toggleTheme);
    });
  });

  // Also sync immediately if DOM is already loaded (e.g., after inline script)
  if (document.readyState !== 'loading') {
    // Defer to next tick to ensure elements exist if script is in head
    setTimeout(syncSwitches, 0);
  } else {
    // Try early sync in case DOMContentLoaded hasn't fired but elements exist
    document.addEventListener('readystatechange', function() {
      if (document.readyState === 'interactive') syncSwitches();
    });
  }
})();
