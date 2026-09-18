// Sticky "Add Selected to Cart" bar — shows/hides based on checkbox count.
// This is the ONLY JS on this page; everything else is plain Django/HTML.
document.addEventListener('DOMContentLoaded', function () {
    const checkboxes = document.querySelectorAll('.lc-test-checkbox');
    const stickyBar = document.getElementById('stickyBar');
    const countLabel = document.getElementById('selectedCount');

    if (!checkboxes.length || !stickyBar) return;

    function updateBar() {
        const checkedCount = document.querySelectorAll('.lc-test-checkbox:checked').length;
        if (countLabel) countLabel.textContent = checkedCount;
        stickyBar.style.display = checkedCount > 0 ? 'block' : 'none';
    }

    checkboxes.forEach(cb => cb.addEventListener('change', updateBar));
});

// Toast notifications — converts Django's {% if messages %} block into
// auto-dismissing toasts. Runs only if toast containers exist on the page.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.lc-alert').forEach(function (alertEl, index) {
        alertEl.classList.add('lc-toast-item');
        alertEl.style.animationDelay = (index * 0.1) + 's';

        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '&times;';
        closeBtn.className = 'lc-toast-close';
        closeBtn.setAttribute('aria-label', 'Close notification');
        closeBtn.onclick = function () { dismissToast(alertEl); };
        alertEl.appendChild(closeBtn);

        setTimeout(function () { dismissToast(alertEl); }, 4000);
    });

    function dismissToast(el) {
        el.classList.add('lc-toast-hide');
        setTimeout(function () { el.remove(); }, 300);
    }
});

// Right-side mobile drawer
document.addEventListener('DOMContentLoaded', function () {
    const openBtn = document.getElementById('lcDrawerOpen');
    const closeBtn = document.getElementById('lcDrawerClose');
    const drawer = document.getElementById('lcDrawer');
    const backdrop = document.getElementById('lcDrawerBackdrop');
    if (!openBtn || !drawer || !backdrop) return;

    function openDrawer() {
        drawer.classList.add('show');
        backdrop.classList.add('show');
        document.body.classList.add('lc-drawer-open');
        drawer.setAttribute('aria-hidden', 'false');
    }
    function closeDrawer() {
        drawer.classList.remove('show');
        backdrop.classList.remove('show');
        document.body.classList.remove('lc-drawer-open');
        drawer.setAttribute('aria-hidden', 'true');
    }

    openBtn.addEventListener('click', openDrawer);
    closeBtn.addEventListener('click', closeDrawer);
    backdrop.addEventListener('click', closeDrawer);
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') closeDrawer();
    });
});

// Global premium Chart.js defaults — applies automatically to every chart
// on every dashboard, no per-chart edits required.
if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = "'Inter', sans-serif";
    Chart.defaults.color = '#5C6E6E';
    Chart.defaults.plugins.tooltip.backgroundColor = '#122d48';
    Chart.defaults.plugins.tooltip.titleFont = { weight: '600', family: "'Poppins', sans-serif" };
    Chart.defaults.plugins.tooltip.bodyFont = { family: "'Inter', sans-serif" };
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.legend.labels.font = { family: "'Inter', sans-serif", size: 12 };
    Chart.defaults.elements.bar.borderRadius = 6;
    Chart.defaults.elements.bar.borderSkipped = false;
    Chart.defaults.elements.line.borderWidth = 2.5;
    Chart.defaults.elements.point.radius = 3;
    Chart.defaults.elements.point.hoverRadius = 6;
    Chart.defaults.animation.duration = 700;
    Chart.defaults.animation.easing = 'easeOutQuart';

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        Chart.defaults.animation = false;
    }
}

// Test details modal — reads data-* attributes only, no DB queries in JS.
document.addEventListener('DOMContentLoaded', function () {
    const modal = document.getElementById('testDetailModal');
    if (!modal) return;

    const NOT_SPECIFIED = 'Not specified — please contact the lab for details.';

    document.querySelectorAll('.lc-view-details-btn').forEach(function (btn) {
        btn.addEventListener('click', function () {
            document.getElementById('modalName').textContent = btn.dataset.name;
            document.getElementById('modalCode').textContent = 'Code: ' + btn.dataset.code;
            document.getElementById('modalDept').textContent = btn.dataset.department;
            document.getElementById('modalPrice').textContent = '₹' + btn.dataset.price;
            document.getElementById('modalDescription').textContent = btn.dataset.description || NOT_SPECIFIED;
            document.getElementById('modalSample').textContent = btn.dataset.sample || NOT_SPECIFIED;
            document.getElementById('modalPrep').textContent = btn.dataset.prep || NOT_SPECIFIED;
            document.getElementById('modalTurnaround').textContent = btn.dataset.turnaround + ' hours';
            document.getElementById('modalFullPageLink').href = btn.dataset.detailUrl;

            const fastingBanner = document.getElementById('modalFastingBanner');
            if (btn.dataset.fasting === '1') {
                fastingBanner.style.display = 'block';
                document.getElementById('modalFastingText').textContent =
                    btn.dataset.fastingInstructions || 'Fasting required — duration not specified. Contact the lab.';
            } else {
                fastingBanner.style.display = 'none';
            }
        });
    });
});

// Password show/hide — two inline SVGs (eye-open / eye-closed) already
// present in the HTML at page load; JS only toggles which one is visible
// via CSS class, never injects emoji or text content. No dependency on
// any external icon font/CDN.
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.lc-password-toggle').forEach(function (btn) {
        btn.addEventListener('click', function () {
            const field = btn.closest('.lc-password-field').querySelector('input');
            if (!field) return;
            const isHidden = field.type === 'password';
            field.type = isHidden ? 'text' : 'password';
            btn.classList.toggle('lc-password-visible', isHidden);
            btn.setAttribute('aria-label', isHidden ? 'Hide password' : 'Show password');
        });
    });
});