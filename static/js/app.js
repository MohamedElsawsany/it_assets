/* ============================================================
   IT Asset Management — Shared JS utilities
   ============================================================ */

/* ── CSRF token ─────────────────────────────────────────────── */
function getCsrfToken() {
  const name  = 'csrftoken';
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  const el = document.querySelector('[name=csrfmiddlewaretoken]');
  return el ? el.value : '';
}

/* ── AJAX helpers ───────────────────────────────────────────── */
function ajaxGet(url) {
  return fetch(url, {
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json',
    },
    credentials: 'same-origin',
  }).then(handleResponse);
}

function ajaxPost(url, formData) {
  if (formData instanceof FormData) {
    if (!formData.has('csrfmiddlewaretoken')) {
      formData.set('csrfmiddlewaretoken', getCsrfToken());
    }
  }
  return fetch(url, {
    method: 'POST',
    headers: {
      'X-Requested-With': 'XMLHttpRequest',
      'Accept': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'same-origin',
    body: formData,
  }).then(handleResponse);
}

function handleResponse(res) {
  if (!res.ok && res.status !== 400 && res.status !== 403) {
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}

/* ── Toast notifications ────────────────────────────────────── */
function showToast(message, type) {
  type = type || 'success';
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const id   = 'toast-' + Date.now();
  const icon = type === 'success' ? 'check-circle-fill'
             : type === 'danger'  ? 'x-circle-fill'
             : type === 'warning' ? 'exclamation-triangle-fill'
             : 'info-circle-fill';

  const html = `
    <div id="${id}" class="toast align-items-center text-white bg-${type} border-0"
         role="alert" aria-live="assertive">
      <div class="d-flex">
        <div class="toast-body d-flex align-items-center gap-2">
          <i class="bi bi-${icon}"></i>${escHtml(message)}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto"
                data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    </div>`;

  container.insertAdjacentHTML('beforeend', html);
  const toastEl = document.getElementById(id);
  const toast   = new bootstrap.Toast(toastEl, { delay: 4000 });
  toast.show();
  toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}

/* ── Form error helpers ─────────────────────────────────────── */
function showFormErrors(form, errors) {
  Object.entries(errors).forEach(([field, messages]) => {
    if (field === '__all__') {
      showToast(messages.join(' '), 'danger');
      return;
    }
    const input = form.querySelector(`[name="${field}"]`);
    if (input) {
      input.classList.add('is-invalid');
      const feedback = input.closest('.col-md-6, .mb-3, .input-group')
                             ?.querySelector('.invalid-feedback, .d-block.invalid-feedback');
      if (feedback) feedback.textContent = messages.join(' ');

      const wrapper = input.closest('.input-group');
      if (wrapper) {
        const next = wrapper.nextElementSibling;
        if (next && next.classList.contains('invalid-feedback')) {
          next.textContent = messages.join(' ');
        }
        const namedEl = document.getElementById(`create${capitalize(field)}Error`)
                      || document.getElementById(`edit${capitalize(field)}Error`)
                      || document.getElementById(`reset${capitalize(camelize(field))}Error`);
        if (namedEl) namedEl.textContent = messages.join(' ');
      }
    } else {
      showToast(`${field}: ${messages.join(' ')}`, 'danger');
    }
  });
}

function clearFormErrors(form) {
  form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
  form.querySelectorAll('.invalid-feedback').forEach(el => {
    if (!el.dataset.keep) el.textContent = '';
  });
  if (window.jQuery) {
    $(form).find('.select2-container--bootstrap-5').removeClass('is-invalid');
  }
}

/* ── Button loading state ───────────────────────────────────── */
function setButtonLoading(btn, loading) {
  const textEl    = btn.querySelector('.btn-text');
  const loadingEl = btn.querySelector('.btn-loading');
  btn.disabled = loading;
  if (textEl)    textEl.classList.toggle('d-none', loading);
  if (loadingEl) loadingEl.classList.toggle('d-none', !loading);
}

/* ── Password visibility toggle ────────────────────────────── */
function togglePasswordField(btn) {
  const input = btn.closest('.input-group').querySelector('input');
  const icon  = btn.querySelector('i');
  if (input.type === 'password') {
    input.type  = 'text';
    icon.className = 'bi bi-eye-slash';
  } else {
    input.type  = 'password';
    icon.className = 'bi bi-eye';
  }
}

/* ── Sidebar toggle ─────────────────────────────────────────── */
function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const isOpen  = sidebar.classList.contains('sidebar-open');
  sidebar.classList.toggle('sidebar-open', !isOpen);
  overlay.classList.toggle('show', !isOpen);
}

function closeSidebar() {
  document.getElementById('sidebar').classList.remove('sidebar-open');
  document.getElementById('sidebarOverlay').classList.remove('show');
}

document.addEventListener('DOMContentLoaded', () => {
  const overlay = document.getElementById('sidebarOverlay');
  if (overlay) overlay.addEventListener('click', closeSidebar);
});

window.addEventListener('resize', () => {
  if (window.innerWidth >= 992) closeSidebar();
});

/* ── HTML escape ────────────────────────────────────────────── */
function escHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/* ── String helpers ─────────────────────────────────────────── */
function capitalize(str) {
  return str ? str.charAt(0).toUpperCase() + str.slice(1) : '';
}

function camelize(str) {
  return str.replace(/_([a-z])/g, (_, c) => c.toUpperCase());
}

/* ── Select2 AJAX helpers ────────────────────────────────────── */

/**
 * Initialise Select2 with AJAX on a jQuery element.
 *
 * Guards:
 *  - Skips silently if jQuery is missing
 *  - Skips silently if Select2 plugin is not loaded
 *  - Skips silently if $el is empty (element not in DOM)
 *
 * @param {jQuery} $el          - the <select> wrapped in jQuery
 * @param {string} entity       - entity slug for /select2/<entity>/
 * @param {function|object}     extraParams - extra query params (or null)
 * @param {string} placeholder
 */
function initSelect2($el, entity, extraParams, placeholder) {
  /* ── Safety guards ── */
  if (!window.jQuery) return;                  // jQuery not loaded
  if (typeof $.fn.select2 === 'undefined') {   // Select2 plugin not loaded
    console.warn('Select2 is not loaded – skipping initSelect2 for', entity);
    return;
  }
  if (!$el || !$el.length) return;             // element not in DOM

  /* ── Already initialised? Destroy first to avoid duplicate init ── */
  if ($el.data('select2')) {
    $el.select2('destroy');
  }

  const $modal = $el.closest('.modal');

  /* ── Build options object (avoid passing undefined values) ── */
  const opts = {
    theme: 'bootstrap-5',
    dir: window.APP_DIR || 'ltr',
    dropdownParent: $modal.length ? $modal : $('body'),
    placeholder: placeholder || '—',
    allowClear: true,
    minimumInputLength: 0,
    ajax: {
      url: '/select2/' + entity + '/',
      dataType: 'json',
      delay: 250,
      data: function (params) {
        const extra = (typeof extraParams === 'function')
          ? extraParams()
          : (extraParams || {});
        return Object.assign({ q: params.term || '', page: params.page || 1 }, extra);
      },
      processResults: function (data) {
        return { results: data.results, pagination: data.pagination };
      },
      cache: true,
    },
  };

  /* Only set language when actually needed; avoids "undefined language" warnings */
  if (window.APP_LANG === 'ar') {
    opts.language = 'ar';
  }

  try {
    $el.select2(opts);
  } catch (err) {
    console.error('Select2 init error for entity "' + entity + '":', err);
  }
}

/**
 * Pre-select a value in an already-initialised Select2 element.
 * Creates the <option> if it doesn't exist yet (needed for AJAX selects).
 */
function setSelect2Value($el, id, text) {
  if (!window.jQuery || typeof $.fn.select2 === 'undefined') return;
  if (!$el || !$el.length) return;

  if (!id && id !== 0) {
    $el.val(null).trigger('change');
    return;
  }

  const sid = String(id);
  if ($el.find('option[value="' + sid + '"]').length === 0) {
    $el.append(new Option(String(text || ''), sid, false, false));
  }
  $el.val(sid).trigger('change');
}

/* ── Pagination ─────────────────────────────────────────────── */
/**
 * Render a Bootstrap pagination bar into the element with the given id.
 * @param {string}   containerId  - id of the container element
 * @param {number}   current      - current page number (1-based)
 * @param {number}   numPages     - total number of pages
 * @param {function} loadFn       - called with the new page number when clicked
 */
function renderPagination(containerId, current, numPages, loadFn) {
  const el = document.getElementById(containerId);
  if (!el) return;
  if (numPages <= 1) { el.innerHTML = ''; return; }

  // Build a compact list of page numbers with ellipsis gaps
  const show = new Set([1, 2, current - 1, current, current + 1, numPages - 1, numPages]);
  const pages = [...show].filter(p => p >= 1 && p <= numPages).sort((a, b) => a - b);

  const isRtl = window.APP_DIR === 'rtl';
  const prevArrow = isRtl ? '&rsaquo;' : '&lsaquo;';
  const nextArrow = isRtl ? '&lsaquo;' : '&rsaquo;';

  let html = '<nav><ul class="pagination pagination-sm mb-0 flex-wrap">';
  html += `<li class="page-item${current === 1 ? ' disabled' : ''}">
    <a class="page-link" href="#" data-page="${current - 1}">${prevArrow}</a></li>`;

  let prev = 0;
  for (const p of pages) {
    if (prev && p - prev > 1) html += '<li class="page-item disabled"><span class="page-link">…</span></li>';
    html += `<li class="page-item${p === current ? ' active' : ''}">
      <a class="page-link" href="#" data-page="${p}">${p}</a></li>`;
    prev = p;
  }

  html += `<li class="page-item${current === numPages ? ' disabled' : ''}">
    <a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a></li>`;
  html += '</ul></nav>';
  el.innerHTML = html;

  el.querySelectorAll('.page-link[data-page]').forEach(a => {
    a.addEventListener('click', e => {
      e.preventDefault();
      const p = parseInt(a.dataset.page);
      if (p >= 1 && p <= numPages && p !== current) loadFn(p);
    });
  });
}

/**
 * After form.reset(), sync all Select2 widgets so their visible UI
 * reflects the now-empty underlying <select> values.
 */
function resetFormSelects(form) {
  if (!window.jQuery || typeof $.fn.select2 === 'undefined') return;
  $(form).find('select').each(function () {
    if ($(this).data('select2')) {
      $(this).val(null).trigger('change');
    }
  });
}
