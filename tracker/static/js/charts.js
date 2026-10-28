/* Dashboard charts using vendored Chart.js, greyscale only, theme-aware. */
document.addEventListener('DOMContentLoaded', function() {
  if (!window.Chart) return;
  var charts = [];

  function getColors() {
    var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    // Greyscale differentiated by lightness
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
          ticks: { color: c.secondary, font: { size: 11 } },
          grid: { color: c.grid, drawBorder: false },
          border: { display: false },
        },
        y: {
          ticks: { color: c.secondary, font: { size: 11 }, precision: 0 },
          grid: { color: c.grid, drawBorder: false },
          border: { display: false },
        }
      }
    };
  }

  // Set global defaults
  if (window.Chart) {
    Chart.defaults.color = getColors().text;
    Chart.defaults.borderColor = getColors().grid;
    Chart.defaults.font.family = '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
  }

  // Helper to create bar chart
  function renderBar(canvasId, labels, data, horizontal) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var c = getColors();
    var empty = !labels.length || data.every(function(v){return v===0;});
    // If empty, show empty state text inside card and hide canvas
    var card = canvas.closest('.chart-card');
    if (empty) {
      canvas.style.display = 'none';
      var existing = card.querySelector('.empty-state');
      if (!existing) {
        var p = document.createElement('p');
        p.className = 'empty-state';
        p.textContent = 'No mistakes logged in this period.';
        card.appendChild(p);
      }
      return;
    }
    // Remove existing empty state if any
    var es = card.querySelector('.empty-state'); if (es) es.remove();
    canvas.style.display = '';

    var bgColors = labels.map(function(_, i){ return c.bars[i % c.bars.length]; });

    var options = baseOptions();
    if (horizontal) {
      options.indexAxis = 'y';
    }
    // Ensure x ticks appropriate
    options.plugins.tooltip = { enabled: true };
    options.plugins.datalabels = false;

    // Add data labels via plugin-like drawing? We'll use simple tooltip and rely on bar values visible via tooltip.
    // For value labels, we can use afterDraw but keep simple.

    var chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          data: data,
          backgroundColor: bgColors,
          borderWidth: 0,
          borderRadius: 2,
          barThickness: horizontal ? 18 : 24,
        }]
      },
      options: options,
      plugins: [{
        id: 'valueLabels',
        afterDatasetsDraw(chart) {
          var ctx = chart.ctx;
          ctx.save();
          ctx.fillStyle = c.text;
          ctx.font = '11px -apple-system, sans-serif';
          chart.data.datasets.forEach(function(dataset, i) {
            var meta = chart.getDatasetMeta(i);
            meta.data.forEach(function(bar, idx) {
              var val = dataset.data[idx];
              if (horizontal) {
                ctx.textAlign = 'left';
                ctx.fillText(val, bar.x + 6, bar.y + 4);
              } else {
                ctx.textAlign = 'center';
                ctx.fillText(val, bar.x, bar.y - 6);
              }
            });
          });
          ctx.restore();
        }
      }]
    });
    charts.push(chart);
  }

  function renderLine(canvasId, labels, data) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    var c = getColors();
    var card = canvas.closest('.chart-card');
    if (!labels.length) {
      canvas.style.display = 'none';
      var p = document.createElement('p');
      p.className = 'empty-state';
      p.textContent = 'No mistakes logged in this period.';
      card.appendChild(p);
      return;
    }
    canvas.style.display = '';
    var es = card.querySelector('.empty-state'); if (es) es.remove();

    var options = baseOptions();
    options.scales.y.beginAtZero = true;

    var chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [{
          label: 'Mistakes',
          data: data,
          borderColor: c.line,
          backgroundColor: 'transparent',
          pointBackgroundColor: c.point,
          pointRadius: 3,
          tension: 0.3,
          borderWidth: 1.5,
          fill: false,
        }]
      },
      options: options,
    });
    charts.push(chart);
  }

  // Read data from JSON embedded in page
  function initFromDOM() {
    var dataEl = document.getElementById('dashboard-data');
    if (!dataEl) return;
    try {
      var d = JSON.parse(dataEl.textContent);
      // By subject
      renderBar('chart-subject', d.by_subject.map(function(x){return x.subject;}), d.by_subject.map(function(x){return x.count;}), false);
      // By error type horizontal
      renderBar('chart-error', d.by_error.map(function(x){return x.error_type;}), d.by_error.map(function(x){return x.count;}), true);
      // Top chapters horizontal
      renderBar('chart-chapters', d.top_chapters.map(function(x){return x.chapter;}), d.top_chapters.map(function(x){return x.count;}), true);
      // Per test line
      renderLine('chart-tests', d.per_test.map(function(x){return x.test_date + ' ' + x.test_name;}), d.per_test.map(function(x){return x.count;}));
    } catch(e) { console.error(e); }
  }

  initFromDOM();

  // Re-render on theme change
  window.addEventListener('themechange', function() {
    // Destroy and re-init
    charts.forEach(function(c){ c.destroy(); });
    charts = [];
    // Need to clear canvases parent empty states
    document.querySelectorAll('.chart-card .empty-state').forEach(function(el){ el.remove(); });
    initFromDOM();
    // Also update global defaults
    if (window.Chart) {
      Chart.defaults.color = getColors().text;
    }
  });
});
