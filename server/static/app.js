/* Timbre web intake — a Typeform-style wizard. Pure intake: collects answers and
   autosaves them to data/intake.json via the local API. No model calls here. */
(() => {
  "use strict";

  const stage = document.getElementById("stage");
  const nav = document.getElementById("nav");
  const backBtn = document.getElementById("back");
  const nextBtn = document.getElementById("next");
  const hint = document.getElementById("hint");
  const progressFill = document.getElementById("progress-fill");

  const ENTER_HINT = "Enter ↵ to continue";

  // weekend/lunch/teach are the "fun" voice questions; the rest are "about you".
  const FUN = new Set(["weekend", "lunch", "teach"]);
  const SECTIONS = {
    about: {
      eyebrow: "A little about you",
      title: "First, let's get to know you.",
      subtitle: "",
    },
    fun: {
      eyebrow: "Now, the fun part",
      title: "A few quick ones.",
      subtitle:
        "Just be yourself. We recommend dictating your answers — a tool like Wispr Flow makes it effortless.",
    },
  };

  let flow = [];
  let idx = 0;
  const answers = {}; // writes_to -> value
  let nameValue = "";
  let resumeChars = 0;
  let pastedSample = "";
  const uploadedSamples = [];
  let introAnimated = false;

  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const api = {
    onboarding: () => fetch("/api/onboarding").then((r) => r.json()),
    begin: () => fetch("/api/intake/begin", { method: "POST" }),
    patch: (a) =>
      fetch("/api/intake", {
        method: "PATCH",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ answers: a }),
      }),
    complete: () => fetch("/api/intake/complete", { method: "POST" }),
    resume: (file) => {
      const fd = new FormData();
      fd.append("file", file);
      return fetch("/api/intake/resume", { method: "POST", body: fd }).then((r) => r.json());
    },
    sampleUpload: (file) => {
      const fd = new FormData();
      fd.append("file", file);
      return fetch("/api/intake/writing-sample", { method: "POST", body: fd }).then((r) => r.json());
    },
  };

  function esc(s) {
    return String(s == null ? "" : s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }
  const fillName = (s) => s.replace(/\{name\}/g, nameValue || "there");
  const asText = (v) => (Array.isArray(v) ? v.join("\n\n") : v || "");

  function buildFlow(data) {
    const f = [{ kind: "intro", welcome: data.welcome }];
    let prevGroup = null;
    let num = 0;
    data.questions.forEach((q) => {
      const group = FUN.has(q.id) ? "fun" : "about";
      if (group !== prevGroup) {
        f.push({ kind: "section", ...SECTIONS[group] });
        prevGroup = group;
      }
      num += 1;
      f.push({ kind: "question", q, num });
    });
    f.push({ kind: "done" });
    return f;
  }

  function isLastQuestion() {
    for (let i = idx + 1; i < flow.length; i++) if (flow[i].kind === "question") return false;
    return true;
  }

  function renderQuestion(screen) {
    const q = screen.q;
    const prompt = fillName(q.prompt);
    let body;
    if (q.id === "name") {
      body = `<input class="field" id="answer" type="text" autocomplete="off"
        placeholder="Type your name…" value="${esc(answers["name"])}">`;
    } else if (q.id === "background") {
      const up = resumeChars > 0;
      body = `
        <textarea class="field" id="answer" rows="3"
          placeholder="Paste a quick bio, or the short version…">${esc(answers["typed.background"])}</textarea>
        <div class="subfields">
          <div class="resume${up ? " uploaded" : ""}">
            <label for="resume-file">${up ? "✓ Resume added" : "↑ Upload resume"}</label>
            <input id="resume-file" type="file" accept=".pdf,.txt,.md,.markdown">
          </div>
        </div>`;
    } else if (q.id === "writing_samples") {
      const n = uploadedSamples.length;
      body = `<textarea class="field" id="answer" rows="4"
          placeholder="Paste a post or essay you're proud of…">${esc(pastedSample)}</textarea>
        <div class="subfields">
          <div class="resume sample-upload${n ? " uploaded" : ""}">
            <label for="sample-file">${n ? `✓ ${n} file${n > 1 ? "s" : ""} added` : "↑ Upload a post / essay (PDF / txt)"}</label>
            <input id="sample-file" type="file" accept=".pdf,.txt,.md,.markdown" multiple>
          </div>
        </div>
        <div class="skip-note">Optional — leave blank to skip.</div>`;
    } else {
      body = `<textarea class="field" id="answer" rows="3"
        placeholder="Type or dictate…">${esc(answers[q.writes_to])}</textarea>`;
    }
    const sub = q.subtext ? `<p class="desc">${esc(fillName(q.subtext))}</p>` : "";
    return `<div class="screen">
      <div class="marker">${screen.num} <span aria-hidden="true">→</span></div>
      <h1 class="question">${esc(prompt)}</h1>
      ${sub}
      ${body}
    </div>`;
  }

  function render() {
    const screen = flow[idx];
    progressFill.style.width = (idx / (flow.length - 1)) * 100 + "%";

    if (screen.kind === "question") {
      stage.innerHTML = renderQuestion(screen);
    } else if (screen.kind === "intro") {
      stage.innerHTML = `<div class="screen screen--center intro">
        <h1 class="title" id="intro-title"></h1>
        <p class="subtitle reveal">${esc(screen.welcome)}</p>
        <button id="get-started" class="cta reveal" type="button">Get started</button>
      </div>`;
    } else {
      const isDone = screen.kind === "done";
      const eyebrow = isDone ? "All set" : screen.eyebrow;
      const title = isDone ? "You're all set." : screen.title;
      const subtitle = isDone
        ? "Building your persona now — head back to Timbre in the terminal."
        : screen.subtitle;
      const cta = isDone
        ? `<button id="done-close" class="cta" type="button">I'm all done ✨</button>`
        : "";
      const sub = subtitle ? `<p class="subtitle">${esc(subtitle)}</p>` : "";
      stage.innerHTML = `<div class="screen screen--center">
        <div class="eyebrow">${esc(eyebrow)}</div>
        <h1 class="title">${esc(title)}</h1>
        ${sub}${cta}
      </div>`;
    }

    setupNav();
    wireInputs();
    if (screen.kind === "intro") playIntro();
    if (screen.kind === "done") fireConfetti();
  }

  function playIntro() {
    const titleEl = document.getElementById("intro-title");
    const reveals = document.querySelectorAll(".intro .reveal");
    if (!titleEl) return;
    if (introAnimated) {
      titleEl.textContent = "Let's find your voice.";
      reveals.forEach((r) => r.classList.add("show"));
      return;
    }
    introAnimated = true;
    runIntroAnimation(titleEl, reveals);
  }

  async function runIntroAnimation(titleEl, reveals) {
    const type = async (text, speed) => {
      for (let i = 1; i <= text.length; i++) {
        titleEl.textContent = text.slice(0, i);
        await sleep(speed);
      }
    };
    const erase = async (speed) => {
      while (titleEl.textContent.length) {
        titleEl.textContent = titleEl.textContent.slice(0, -1);
        await sleep(speed);
      }
    };
    titleEl.classList.add("typing");
    await sleep(350);
    await type("Welcome to Timbre", 58);
    await sleep(950);
    await erase(30);
    await sleep(180);
    await type("Let's find your voice.", 58);
    titleEl.classList.remove("typing");
    await sleep(120);
    reveals.forEach((r) => r.classList.add("show"));
  }

  function setupNav() {
    const screen = flow[idx];
    // intro & done have no bottom nav (their own CTA handles it)
    if (screen.kind === "intro" || screen.kind === "done") {
      nav.hidden = true;
      return;
    }
    nav.hidden = false;
    backBtn.hidden = idx === 0;

    let label = "Next →";
    if (screen.kind === "section") label = "Continue";
    else if (screen.kind === "question" && isLastQuestion()) label = "Done";
    nextBtn.textContent = label;

    hint.textContent = screen.kind === "question" ? ENTER_HINT : "";
    updateNextEnabled();
  }

  function updateNextEnabled() {
    const screen = flow[idx];
    if (screen.kind !== "question" || !screen.q.required) {
      nextBtn.disabled = false;
      return;
    }
    const el = document.getElementById("answer");
    const hasText = !!(el && el.value.trim());
    // on the background step, an uploaded resume is enough — no blurb required
    const hasResume = screen.q.id === "background" && resumeChars > 0;
    nextBtn.disabled = !(hasText || hasResume);
  }

  function autosize(el) {
    if (el && el.tagName === "TEXTAREA") {
      el.style.height = "auto";
      el.style.height = el.scrollHeight + "px";
    }
  }

  function wireInputs() {
    const el = document.getElementById("answer");
    if (el) {
      el.focus();
      autosize(el);
      el.addEventListener("input", () => {
        autosize(el);
        updateNextEnabled();
      });
    }
    const rf = document.getElementById("resume-file");
    if (rf) rf.addEventListener("change", onResume);
    const sf = document.getElementById("sample-file");
    if (sf) sf.addEventListener("change", onSampleUpload);
    const gs = document.getElementById("get-started");
    if (gs) gs.addEventListener("click", goNext);
    const done = document.getElementById("done-close");
    if (done)
      done.addEventListener("click", () => {
        try {
          window.close();
        } catch {
          /* browsers block closing tabs they didn't open */
        }
      });
  }

  // A single global handler so Enter works anywhere on the page, focused or not.
  function onGlobalKey(e) {
    if (e.key !== "Enter") return;
    const el = document.activeElement;
    if (e.metaKey || e.ctrlKey) {
      // ⌘/Ctrl + Enter = new line in a focused textarea (keep the mechanic)
      if (el && el.tagName === "TEXTAREA") {
        e.preventDefault();
        insertNewline(el);
      }
      return;
    }
    // plain Enter = continue, from anywhere
    e.preventDefault();
    const screen = flow[idx];
    if (screen.kind === "question") {
      if (!nextBtn.disabled) goNext();
    } else if (screen.kind === "intro" || screen.kind === "section") {
      goNext();
    }
  }

  function insertNewline(el) {
    const s = el.selectionStart;
    const end = el.selectionEnd;
    el.value = el.value.slice(0, s) + "\n" + el.value.slice(end);
    el.selectionStart = el.selectionEnd = s + 1;
    autosize(el);
    updateNextEnabled();
  }

  async function onResume(e) {
    const file = e.target.files[0];
    if (!file) return;
    const box = document.querySelector(".resume");
    const label = box ? box.querySelector("label") : null;
    if (label) label.textContent = "reading…";
    try {
      const res = await api.resume(file);
      resumeChars = res.chars || 0;
      if (res.ok) {
        if (box) box.classList.add("uploaded");
        if (label) label.textContent = "✓ Resume added";
        updateNextEnabled();
      } else {
        if (box) box.classList.remove("uploaded");
        if (label) label.textContent = "couldn't read — paste instead";
      }
    } catch {
      if (label) label.textContent = "upload failed — paste instead";
    }
  }

  async function onSampleUpload(e) {
    const files = Array.from(e.target.files || []);
    if (!files.length) return;
    const box = document.querySelector(".sample-upload");
    const label = box ? box.querySelector("label") : null;
    if (label) label.textContent = "reading…";
    for (const file of files) {
      try {
        const res = await api.sampleUpload(file);
        if (res.ok && res.text) uploadedSamples.push(res.text);
      } catch {
        /* skip this file, keep the others */
      }
    }
    const n = uploadedSamples.length;
    if (n) {
      if (box) box.classList.add("uploaded");
      if (label) label.textContent = `✓ ${n} file${n > 1 ? "s" : ""} added`;
      await saveCurrent();
    } else if (label) {
      label.textContent = "couldn't read — paste instead";
    }
    e.target.value = "";
  }

  async function saveCurrent() {
    const screen = flow[idx];
    if (screen.kind !== "question") return;
    const q = screen.q;
    const el = document.getElementById("answer");
    const val = el ? el.value.trim() : "";
    const patch = {};
    if (q.id === "name") {
      nameValue = val;
      answers["name"] = val;
      patch["name"] = val;
    } else if (q.id === "background") {
      answers["typed.background"] = val;
      patch["typed.background"] = val;
    } else if (q.id === "writing_samples") {
      pastedSample = val;
      const list = [...uploadedSamples];
      if (val) list.push(val);
      answers["voice.writing_samples"] = list;
      patch["voice.writing_samples"] = list;
    } else {
      answers[q.writes_to] = val;
      patch[q.writes_to] = val;
    }
    try {
      await api.patch(patch);
    } catch {
      /* keep going; the next save retries the whole intake */
    }
  }

  async function goNext() {
    const screen = flow[idx];
    if (screen.kind === "intro") {
      try {
        await api.begin();
      } catch {
        /* fresh-start best effort */
      }
    }
    if (screen.kind === "question") {
      await saveCurrent();
      if (isLastQuestion()) return finish();
    }
    idx += 1;
    render();
  }

  async function finish() {
    try {
      await api.complete();
    } catch {
      /* the terminal flow can still read intake.json */
    }
    idx = flow.length - 1;
    render();
  }

  function goBack() {
    if (idx > 0) {
      idx -= 1;
      render();
    }
  }

  // ---------- confetti (self-contained, brand colors) ----------
  function fireConfetti() {
    const canvas = document.createElement("canvas");
    canvas.style.cssText = "position:fixed;inset:0;pointer-events:none;z-index:50";
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    document.body.appendChild(canvas);
    const ctx = canvas.getContext("2d");
    const colors = ["#ffe500", "#ffffff", "#c9c9c0"];
    const parts = Array.from({ length: 240 }, () => ({
      x: canvas.width / 2 + (Math.random() - 0.5) * 380,
      y: canvas.height / 2.4,
      vx: (Math.random() - 0.5) * 16,
      vy: Math.random() * -15 - 4,
      g: 0.28 + Math.random() * 0.14,
      size: 9 + Math.random() * 12,
      color: colors[Math.floor(Math.random() * colors.length)],
      rot: Math.random() * Math.PI,
      vr: (Math.random() - 0.5) * 0.4,
    }));
    let frame = 0;
    (function tick() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of parts) {
        p.vy += p.g;
        p.x += p.vx;
        p.y += p.vy;
        p.rot += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate(p.rot);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.62);
        ctx.restore();
      }
      frame += 1;
      if (frame < 260) requestAnimationFrame(tick);
      else canvas.remove();
    })();
  }

  nextBtn.addEventListener("click", () => {
    if (!nextBtn.disabled) goNext();
  });
  backBtn.addEventListener("click", goBack);
  document.addEventListener("keydown", onGlobalKey);

  api
    .onboarding()
    .then((data) => {
      flow = buildFlow(data);
      idx = 0;
      render();
    })
    .catch(() => {
      stage.innerHTML = `<div class="screen screen--center">
        <h1 class="title">Couldn't load.</h1>
        <p class="subtitle">Is the Timbre intake server running? Try restarting <code>tb welcome</code>.</p>
      </div>`;
    });
})();
