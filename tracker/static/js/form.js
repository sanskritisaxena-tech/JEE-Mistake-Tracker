/* Form handling: dynamic chapter dropdown, client validation, autofocus. */
document.addEventListener('DOMContentLoaded', function() {
  var subjectEl = document.getElementById('subject');
  var chapterEl = document.getElementById('chapter');
  if (!subjectEl || !chapterEl) return;

  // Chapters data injected via data attribute
  var chaptersData = {};
  try {
    chaptersData = JSON.parse(document.getElementById('chapters-data').textContent);
  } catch (e) {}

  function updateChapters() {
    var subject = subjectEl.value;
    var current = chapterEl.getAttribute('data-current') || chapterEl.value;
    chapterEl.innerHTML = '<option value="">Select chapter</option>';
    if (subject && chaptersData[subject]) {
      chaptersData[subject].forEach(function(ch) {
        var opt = document.createElement('option');
        opt.value = ch;
        opt.textContent = ch;
        if (ch === current) opt.selected = true;
        chapterEl.appendChild(opt);
      });
    }
    // If there was a current value that matches new list, keep it
    if (current) {
      chapterEl.value = current;
    }
  }

  subjectEl.addEventListener('change', function() {
    // Clear data-current when user changes subject
    chapterEl.setAttribute('data-current', '');
    updateChapters();
  });

  // Initial population
  updateChapters();

  // Autofocus first empty required field
  var inputs = document.querySelectorAll('#mistake-form input[required], #mistake-form select[required]');
  for (var i = 0; i < inputs.length; i++) {
    if (!inputs[i].value) {
      inputs[i].focus();
      break;
    }
  }
  // If all filled, focus question_ref
  if (inputs.length && Array.from(inputs).every(function(el){return el.value;})) {
    var qref = document.getElementById('question_ref');
    if (qref) qref.focus();
  }

  // Client-side validation messages (use browser but also inline)
  var form = document.getElementById('mistake-form');
  if (form) {
    form.addEventListener('submit', function(e) {
      var valid = true;
      // Clear previous inline errors set by JS (server errors remain)
      // Check required fields
      var required = form.querySelectorAll('[required]');
      required.forEach(function(el) {
        if (!el.value.trim()) {
          valid = false;
        }
      });
      // Note length
      var note = document.getElementById('note');
      if (note && note.value.length > 300) {
        valid = false;
        // Show inline if not already
        var err = document.getElementById('error-note');
        if (err) err.textContent = 'Note must be 300 characters or fewer.';
      }
      // Let browser handle if invalid
    });
  }
});
