/* Dashboard charts using vendored Chart.js, greyscale only, theme-aware, with zoom/pan modal. */
document.addEventListener('DOMContentLoaded', function() {
  if (!window.Chart) return;
  var charts = []; // Keep references to original charts for destroy/re-render
  var dashboardData = null; // Will hold parsed JSON
  var modalChart = null; // Current expanded chart instance
  var lastFocusedElement = null; // To return focus on close

  // Helpers ---------------------------------------------------------------

  function isMobile() {
    return window.matchMedia && window.matchMedia('(max-width: 768px)').matches;
  }

  function getColors() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (isDark) {
      return {
        text: '#E6E6E6',
        secondary: '#9B9B9B',
        grid: '#2F2F2F',
        bars: ['#E6E6E6', '#CFCFCF', '#B8B8B8', '#9B9B9B', '#7E7E7E', '#616161'],
        line: '#E6E6E6',
        point: '#E6E6E6',
      };
    } else {
      return {
        text: '#37352F',
        secondary: '#787774',
        grid: '#E9E9E7',
        bars: ['#37352F', '#5A5854', '#787774', '#9B9B9B', '#B8B8B8', '#CFCFCF'],
        line: '#37352F',
        point: '#37352F',
      };
    }
  }

  function formatCompactDate(iso) {
    // Expect "YYYY-MM-DD", return "12 Oct"
    try {
      var d = new Date(iso + 'T00:00:00');
      if (isNaN(d.getTime())) return iso;
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short' });
    } catch (e) {
      return iso;
    }
  }

  // Wrap long labels for horizontal bar charts into multiple lines
  function wrapLabel(label, maxLen) {
    maxLen = maxLen || 22;
    if (!label || label.length <= maxLen) return label;
    var words = label.split(' ');
    var lines = [];
    var cur = '';
    for (var i = 0; i < words.length; i++) {
      var w = words[i];
      if ((cur + ' ' + w).trim().length > maxLen) {
        if (cur) lines.push(cur);
        cur = w;
      } else {
        cur = cur ? cur + ' ' + w : w;
      }
    }
    if (cur) lines.push(cur);
    return lines.length > 1 ? lines : label;
  }

  // Base options that apply to all charts
  function baseOptions() {
    var c = getColors();
    return {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: {
            color: c.secondary,
            font: { size: 12, family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
            maxRotation: 45,
            minRotation: 0,
            autoSkip: true,
            maxTicksLimit: isMobile() ? 5 : 10,
          },
          grid: { color: c.grid, drawBorder: false, lineWidth: 1 },
          border: { display: false },
        },
        y: {
          ticks: {
            color: c.secondary,
            font: { size: 12, family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
            precision: 0,
          },
          grid: { color: c.grid, drawBorder: false, lineWidth: 1 },
          border: { display: false },
        },
      },
    };
  }

  // Set Chart global defaults for theme
  function setGlobalDefaults() {
    if (!window.Chart) return;
    var c = getColors();
    Chart.defaults.color = c.text;
    Chart.defaults.borderColor = c.grid;
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
  }
  setGlobalDefaults();

  // Dynamic height for horizontal bar charts: 44px per bar + 80px padding, min 340 (280 mobile)
  function setHorizontalHeight(canvasId, count) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var wrap = canvas.closest('.chart-wrap');
    if (!wrap) return;
    var min = isMobile() ? 280 : 340;
    var dynamic = count * 44 + 80;
    var h = Math.max(min, dynamic);
    wrap.style.height = h + 'px';
  }

  // Render bar chart (vertical or horizontal)
  function renderBar(canvasId, rawLabels, data, horizontal, opts) {
    opts = opts || {};
    var fontSize = opts.fontSize || 12;
    var isModal = !!opts.isModal;
    var canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    var ctx = canvas.getContext('2d');
    var c = getColors();
    var card = canvas.closest('.chart-card');

    var empty = !rawLabels.length || data.every(function(v){ return v === 0; });
    if (empty) {
      canvas.style.display = 'none';
      var existing = card ? card.querySelector('.empty-state') : null;
      if (!existing && card) {
        var p = document.createElement('p');
        p.className = 'empty-state';
        p.textContent = 'No mistakes logged in this period.';
        card.appendChild(p);
      }
      return null;
    }
    if (card) {
      var es = card.querySelector('.empty-state');
      if (es) es.remove();
    }
    canvas.style.display = '';

    // Wrap long labels for horizontal charts to avoid cutoff
    var labels = rawLabels.map(function(l){ return horizontal ? wrapLabel(l, 22) : l; });

    // If horizontal, set dynamic height for original charts (not modal, modal has fixed height)
    if (horizontal && !isModal) {
      setHorizontalHeight(canvasId, labels.length);
    }

    var bgColors = labels.map(function(_, i){ return c.bars[i % c.bars.length]; });

    var options = baseOptions();
    // Adjust font sizes
    options.scales.x.ticks.font.size = fontSize;
    options.scales.y.ticks.font.size = fontSize;
    if (horizontal) {
      options.indexAxis = 'y';
      // Give category axis enough width for long labels
      options.scales.y.ticks.padding = 8;
      // Ensure tooltips show full original label, not wrapped array
      options.plugins.tooltip = {
        enabled: true,
        callbacks: {
          title: function(items){
            var idx = items[0].dataIndex;
            // Return original unwrapped label
            return rawLabels[idx];
          }
        }
      };
      // Also draw value labels after bars
      options.plugins.tooltip.callbacks.label = function(ctx){
        return ctx.parsed.x + ' mistakes';
      };
    } else {
      options.plugins.tooltip = { enabled: true };
    }

    // For modal, add zoom/pan plugin options
    if (isModal) {
      options.plugins.zoom = {
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: horizontal ? 'y' : 'x',
        },
        pan: {
          enabled: true,
          mode: horizontal ? 'y' : 'x',
        },
      };
    }

    var chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: bgColors,
          borderWidth: 0,
          borderRadius: 2,
          barThickness: isModal ? 22 : (horizontal ? 18 : 24),
          maxBarThickness: 32,
        }]
      },
      options: options,
      plugins: [{
        id: 'valueLabels',
        afterDatasetsDraw: function(chart) {
          var ctx2 = chart.ctx;
          ctx2.save();
          ctx2.fillStyle = c.text;
          ctx2.font = fontSize + 'px -apple-system, sans-serif';
          chart.data.datasets.forEach(function(dataset, i) {
            var meta = chart.getDatasetMeta(i);
            meta.data.forEach(function(bar, idx) {
              var val = dataset.data[idx];
              if (horizontal) {
                ctx2.textAlign = 'left';
                // bar.x is right edge of bar for horizontal
                ctx2.fillText(val, bar.x + 6, bar.y + 4);
              } else {
                ctx2.textAlign = 'center';
                ctx2.fillText(val, bar.x, bar.y - 6);
              }
            });
          });
          ctx2.restore();
        }
      }]
    });
    if (!isModal) charts.push(chart);
    return chart;
  }

  function renderLine(canvasId, rawLabels, data, fullLabels, opts) {
    opts = opts || {};
    var fontSize = opts.fontSize || 12;
    var isModal = !!opts.isModal;
    var canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    var ctx = canvas.getContext('2d');
    var c = getColors();
    var card = canvas.closest('.chart-card');

    if (!rawLabels.length) {
      canvas.style.display = 'none';
      if (card && !card.querySelector('.empty-state')) {
        var p = document.createElement('p');
        p.className = 'empty-state';
        p.textContent = 'No mistakes logged in this period.';
        card.appendChild(p);
      }
      return null;
    }
    if (card) {
      var es = card.querySelector('.empty-state');
      if (es) es.remove();
    }
    canvas.style.display = '';

    var options = baseOptions();
    options.scales.x.ticks.font.size = fontSize;
    options.scales.y.ticks.font.size = fontSize;
    options.scales.x.ticks.maxRotation = 45;
    options.scales.x.ticks.minRotation = 0;
    options.scales.x.ticks.autoSkip = true;
    options.scales.x.ticks.maxTicksLimit = isMobile() ? 5 : 10;
    options.scales.y.beginAtZero = true;

    // Show point markers only when <=30 points, else hide and show on hover
    var pointRadius = data.length > 30 ? 0 : 3;
    var hoverRadius = 4;

    // Tooltip should show full label (date + test name)
    options.plugins.tooltip = {
      enabled: true,
      callbacks: {
        title: function(items){
          var idx = items[0].dataIndex;
          return fullLabels ? fullLabels[idx] : rawLabels[idx];
        }
      }
    };

    if (isModal) {
      options.plugins.zoom = {
        zoom: {
          wheel: { enabled: true },
          pinch: { enabled: true },
          mode: 'x',
        },
        pan: {
          enabled: true,
          mode: 'x',
        },
      };
    }

    var chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: rawLabels,
        datasets: [{
          label: 'Mistakes',
          data: data,
          borderColor: c.line,
          backgroundColor: 'transparent',
          pointBackgroundColor: c.point,
          pointBorderColor: c.point,
          pointRadius: pointRadius,
          pointHoverRadius: hoverRadius,
          tension: 0.3,
          borderWidth: 2,
          fill: false,
        }]
      },
      options: options,
    });
    if (!isModal) charts.push(chart);
    return chart;
  }

  // Store parsed dashboard data globally for modal reuse
  function initFromDOM() {
    var dataEl = document.getElementById('dashboard-data');
    if (!dataEl) return;
    try {
      var d = JSON.parse(dataEl.textContent);
      dashboardData = d;

      // By subject - vertical bar
      renderBar('chart-subject', d.by_subject.map(function(x){ return x.subject; }), d.by_subject.map(function(x){ return x.count; }), false);

      // By error type - horizontal
      renderBar('chart-error', d.by_error.map(function(x){ return x.error_type; }), d.by_error.map(function(x){ return x.count; }), true);

      // Top chapters - horizontal
      renderBar('chart-chapters', d.top_chapters.map(function(x){ return x.chapter; }), d.top_chapters.map(function(x){ return x.count; }), true);

      // Per test line - format dates compactly
      var compact = d.per_test.map(function(x){ return formatCompactDate(x.test_date); });
      var full = d.per_test.map(function(x){ return x.test_date + ' ' + x.test_name; });
      renderLine('chart-tests', compact, d.per_test.map(function(x){ return x.count; }), full);

    } catch(e) { console.error(e); }
  }

  initFromDOM();

  // Re-render on theme change for original charts
  window.addEventListener('themechange', function() {
    setGlobalDefaults();
    charts.forEach(function(c){ c.destroy(); });
    charts = [];
    // Clear empty states
    document.querySelectorAll('.chart-card .empty-state').forEach(function(el){ el.remove(); });
    // Reset heights so dynamic calculation can re-apply
    document.querySelectorAll('.chart-wrap').forEach(function(w){ w.style.height = ''; });
    initFromDOM();
    // If modal is open, also re-create modal chart with new colors
    if (modalChart && currentModalType) {
      recreateModalChart(currentModalType);
    }
  });

  // Modal handling -----------------------------------------------------

  var backdrop = document.getElementById('chart-modal-backdrop');
  var modalTitleEl = document.getElementById('chart-modal-title');
  var modalCanvas = document.getElementById('chart-modal-canvas');
  var closeBtn = document.getElementById('chart-modal-close');
  var resetBtn = document.getElementById('chart-modal-reset');
  var currentModalType = null; // e.g., 'subject', 'error', 'chapters', 'tests'

  function getFocusableElements() {
    if (!backdrop) return [];
    return backdrop.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  }

  function openModal(type, title) {
    if (!backdrop || !dashboardData) return;
    // Remember focus
    lastFocusedElement = document.activeElement;
    currentModalType = type;
    if (modalTitleEl) modalTitleEl.textContent = title;
    backdrop.classList.add('open');
    backdrop.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
    // Create expanded chart
    recreateModalChart(type);
    // Focus trap: focus close button
    if (closeBtn) closeBtn.focus();
    // Add listeners
    document.addEventListener('keydown', onModalKeydown);
  }

  function recreateModalChart(type) {
    if (!dashboardData) return;
    // Destroy previous
    if (modalChart) {
      try { modalChart.destroy(); } catch(e){}
      modalChart = null;
    }
    var c = getColors();
    setGlobalDefaults();
    var fontSize = 13; // 13-14px for modal
    if (type === 'subject') {
      modalChart = renderBar('chart-modal-canvas', dashboardData.by_subject.map(function(x){ return x.subject; }), dashboardData.by_subject.map(function(x){ return x.count; }), false, { fontSize: fontSize, isModal: true });
    } else if (type === 'error') {
      modalChart = renderBar('chart-modal-canvas', dashboardData.by_error.map(function(x){ return x.error_type; }), dashboardData.by_error.map(function(x){ return x.count; }), true, { fontSize: 14, isModal: true });
      // For modal horizontal, ensure height is handled via CSS flex, not dynamic
    } else if (type === 'chapters') {
      modalChart = renderBar('chart-modal-canvas', dashboardData.top_chapters.map(function(x){ return x.chapter; }), dashboardData.top_chapters.map(function(x){ return x.count; }), true, { fontSize: 14, isModal: true });
    } else if (type === 'tests') {
      var compact = dashboardData.per_test.map(function(x){ return formatCompactDate(x.test_date); });
      var full = dashboardData.per_test.map(function(x){ return x.test_date + ' ' + x.test_name; });
      modalChart = renderLine('chart-modal-canvas', compact, dashboardData.per_test.map(function(x){ return x.count; }), full, { fontSize: 13, isModal: true });
    }
    // Double-click to reset zoom
    if (modalCanvas) {
      modalCanvas.ondblclick = function() {
        if (modalChart && modalChart.resetZoom) modalChart.resetZoom();
      };
    }
  }

  function closeModal() {
    if (!backdrop) return;
    backdrop.classList.remove('open');
    backdrop.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (modalChart) {
      try { modalChart.destroy(); } catch(e){}
      modalChart = null;
    }
    currentModalType = null;
    document.removeEventListener('keydown', onModalKeydown);
    // Return focus
    if (lastFocusedElement && lastFocusedElement.focus) {
      lastFocusedElement.focus();
    }
  }

  function onModalKeydown(e) {
    if (!backdrop.classList.contains('open')) return;
    if (e.key === 'Escape') {
      e.preventDefault();
      closeModal();
      return;
    }
    if (e.key === 'Tab') {
      var focusable = getFocusableElements();
      if (!focusable.length) return;
      var first = focusable[0];
      var last = focusable[focusable.length -1];
      if (e.shiftKey) {
        if (document.activeElement === first) {
          e.preventDefault();
          last.focus();
        }
      } else {
        if (document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    }
  }

  // Attach open handlers to chart cards
  document.querySelectorAll('.chart-card[role="button"]').forEach(function(card){
    var type = card.getAttribute('data-chart');
    var title = card.getAttribute('data-title') || card.querySelector('h3')?.textContent || 'Chart';
    function handler(e) {
      openModal(type, title);
    }
    card.addEventListener('click', handler);
    card.addEventListener('keydown', function(e){
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        handler(e);
      }
    });
  });

  // Close handlers
  if (closeBtn) closeBtn.addEventListener('click', closeModal);
  if (resetBtn) resetBtn.addEventListener('click', function(){
    if (modalChart && modalChart.resetZoom) modalChart.resetZoom();
  });
  if (backdrop) {
    backdrop.addEventListener('click', function(e){
      if (e.target === backdrop) closeModal();
    });
  }

  // Ensure empty state cards are still focusable but show message in modal if needed
  // No extra handling needed

});
