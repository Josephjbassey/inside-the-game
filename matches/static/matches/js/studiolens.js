/**
 * StudioLens Client
 *
 * Handles match clock formatting, narrative generation, and
 * HTMX after-swap re-initialization.
 */
(function () {
  'use strict';

  /* ---------- Match Clock ---------- */

  function formatClock(totalSeconds) {
    var mins = Math.floor(totalSeconds / 60);
    var secs = totalSeconds % 60;
    return mins + ':' + (secs < 10 ? '0' : '') + secs;
  }

  function updateClocks() {
    var clocks = document.querySelectorAll('[data-clock]');
    for (var i = 0; i < clocks.length; i++) {
      var el = clocks[i];
      var seconds = parseInt(el.getAttribute('data-clock'), 10);
      if (!isNaN(seconds)) {
        el.textContent = formatClock(seconds);
      }
    }
  }

  /* ---------- Narrative Generation ---------- */

  function setupNarrativeButtons() {
    var buttons = document.querySelectorAll('[data-narrative-btn]');
    for (var i = 0; i < buttons.length; i++) {
      buttons[i].addEventListener('click', handleNarrativeClick);
    }
  }

  function handleNarrativeClick() {
    var btn = this;
    var matchId = btn.getAttribute('data-match-id');
    var type = btn.getAttribute('data-narrative-type') || 'narrative';
    var lang = btn.getAttribute('data-lang') || 'en';
    var targetId = btn.getAttribute('data-target');
    var target = document.getElementById(targetId);

    if (!target || !matchId) return;

    /* Loading state */
    btn.classList.add('btn--loading');
    btn.disabled = true;
    target.innerHTML =
      '<div class="narrative__loading">' +
      '<div class="spinner"></div>' +
      '<span>Generating AI narrative\u2026</span>' +
      '</div>';

    var endpoint =
      type === 'recap'
        ? '/narratives/api/recap/' + matchId + '/?lang=' + lang
        : '/narratives/api/narrative/' + matchId + '/?lang=' + lang;

    fetch(endpoint)
      .then(function (res) {
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
      })
      .then(function (data) {
        var ts = new Date(data.generated_at).toLocaleTimeString();
        target.innerHTML =
          '<p class="narrative__text">' +
          escapeHtml(data.content) +
          '</p>' +
          '<time class="narrative__time">Generated at ' +
          ts +
          '</time>';
      })
      .catch(function () {
        target.innerHTML =
          '<p class="narrative__error">' +
          'Could not generate narrative. Ensure NVIDIA_API_BASE is configured.' +
          '</p>';
      })
      .finally(function () {
        btn.classList.remove('btn--loading');
        btn.disabled = false;
      });
  }

  function escapeHtml(str) {
    var div = document.createElement('div');
    div.appendChild(document.createTextNode(str));
    return div.innerHTML;
  }

  /* ---------- HTMX Integration ---------- */

  document.addEventListener('htmx:afterSwap', function () {
    updateClocks();
  });

  /* ---------- Init ---------- */

  document.addEventListener('DOMContentLoaded', function () {
    updateClocks();
    setupNarrativeButtons();
  });
})();
