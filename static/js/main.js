/**
 * main.js — Client-Side Utilities for BlockVote E-Voting System
 * Handles UI enhancements, animations, and helper functions.
 */

// ── Auto-dismiss flash messages after 5 seconds ──────────────────
document.addEventListener('DOMContentLoaded', () => {
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    setTimeout(() => {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 5000);
  });

  // Animate stat card numbers
  animateCounters();

  // Add scroll reveal to dash cards
  observeCards();
});


/**
 * Animate numeric values in .stat-val elements for a counting effect.
 */
function animateCounters() {
  document.querySelectorAll('.stat-val').forEach(el => {
    const target = parseInt(el.textContent, 10);
    if (isNaN(target) || target === 0) return;
    let start = 0;
    const duration = 800;
    const step = Math.ceil(target / (duration / 16));
    const timer = setInterval(() => {
      start = Math.min(start + step, target);
      el.textContent = start;
      if (start >= target) clearInterval(timer);
    }, 16);
  });
}


/**
 * Reveal cards as they scroll into view using IntersectionObserver.
 */
function observeCards() {
  const cards = document.querySelectorAll(
    '.stat-card, .dash-card, .step-card, .quick-action-card, .block-card'
  );
  if (!window.IntersectionObserver) return;
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        observer.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });

  cards.forEach(c => {
    c.style.opacity = '0';
    c.style.transform = 'translateY(16px)';
    c.style.transition = 'opacity .45s ease, transform .45s ease';
    observer.observe(c);
  });
}


/**
 * Global clipboard copy helper.
 * @param {string} text - Text to copy
 */
function copyToClipboard(text) {
  navigator.clipboard.writeText(text)
    .then(() => showToast('Copied to clipboard!', 'success'))
    .catch(() => showToast('Copy failed. Please copy manually.', 'danger'));
}


/**
 * Show a temporary Bootstrap-style toast notification.
 * @param {string} message
 * @param {string} type - Bootstrap color (success, danger, info, warning)
 */
function showToast(message, type = 'info') {
  const toastId = 'toast-' + Date.now();
  const html = `
    <div id="${toastId}" class="alert alert-${type} alert-dismissible fade show"
         style="position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;min-width:260px;border-radius:12px;">
      ${message}
      <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>`;
  document.body.insertAdjacentHTML('beforeend', html);
  setTimeout(() => {
    const el = document.getElementById(toastId);
    if (el) {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(el);
      bsAlert.close();
    }
  }, 4000);
}


/**
 * Confirm navigation with a custom message.
 * @param {string} message
 * @param {string} url
 */
function confirmNav(message, url) {
  if (confirm(message)) window.location.href = url;
}
