// Loading state on form submit + confirmation prompts.
document.addEventListener("submit", function (e) {
  const form = e.target;
  if (!form.checkValidity || !form.checkValidity()) return;
  const btn = form.querySelector('button[type="submit"]:not([data-no-loading])');
  if (btn && !btn.classList.contains("loading")) {
    btn.classList.add("loading");
    btn.dataset.label = btn.innerHTML;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Please wait…';
    setTimeout(function () { btn.classList.remove("loading"); btn.innerHTML = btn.dataset.label; }, 8000);
  }
});
document.addEventListener("click", function (e) {
  const el = e.target.closest("[data-confirm]");
  if (el && !window.confirm(el.dataset.confirm)) { e.preventDefault(); e.stopPropagation(); }
});
