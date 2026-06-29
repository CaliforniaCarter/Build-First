// One-question-at-a-time flow. Any <form data-wizard> with .step sections is paged through
// with Back/Next, a progress count, Enter-to-advance, and required-field validation per step.
// On the last step, Next calls requestSubmit() — so a normal POST (onboarding) or a JS submit
// handler (the Write page) takes over from there.

(function () {
  document.querySelectorAll("form[data-wizard]").forEach(initWizard);

  function initWizard(form) {
    const steps = Array.from(form.querySelectorAll(".step"));
    const nav = form.querySelector(".wizardnav");
    if (!steps.length || !nav) return;

    const back = nav.querySelector("[data-back]");
    const next = nav.querySelector("[data-next]");
    const prog = nav.querySelector("[data-progress]");
    const bar = nav.querySelector("[data-bar]");
    const nextLabel = next.dataset.nextLabel || "Next";
    const finishLabel = next.dataset.finishLabel || "Finish";
    let i = 0;

    function show(n) {
      i = Math.max(0, Math.min(n, steps.length - 1));
      steps.forEach((s, idx) => (s.style.display = idx === i ? "block" : "none"));
      back.disabled = i === 0;
      const last = i === steps.length - 1;
      next.textContent = last ? finishLabel : nextLabel;
      if (prog) prog.textContent = i + 1 + " / " + steps.length;
      if (bar) bar.style.width = ((i + 1) / steps.length) * 100 + "%";
      const focusable = steps[i].querySelector("input, textarea, select");
      if (focusable) setTimeout(() => focusable.focus(), 0);
    }

    function stepValid() {
      const fields = Array.from(steps[i].querySelectorAll("input, textarea, select"));
      return fields.every((el) => el.checkValidity());
    }

    function advance() {
      if (!stepValid()) {
        const bad = steps[i].querySelector(":invalid");
        if (bad) bad.reportValidity();
        return;
      }
      if (i === steps.length - 1) form.requestSubmit();
      else show(i + 1);
    }

    next.addEventListener("click", (e) => {
      e.preventDefault();
      advance();
    });
    back.addEventListener("click", (e) => {
      e.preventDefault();
      show(i - 1);
    });
    form.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && e.target.tagName !== "TEXTAREA") {
        e.preventDefault();
        advance();
      }
    });

    // expose a reset so a "write another" button can send the user back to step 1
    form._wizardReset = () => show(0);
    show(0);
  }
})();
