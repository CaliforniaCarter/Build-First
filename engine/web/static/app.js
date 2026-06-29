// Post generation: POST the idea, then stream progress over SSE into the live panel.
// The server never publishes — this only renders the draft and offers copy/export.

(function () {
  const form = document.getElementById("ideaform");
  if (!form) return;

  const gen = document.getElementById("gen");
  const panel = document.getElementById("panel");
  const bar = document.getElementById("bar");
  const live = document.getElementById("live");
  const err = document.getElementById("err");
  const councillog = document.getElementById("councillog");
  const finalwrap = document.getElementById("finalwrap");
  const finalEl = document.getElementById("final");
  const headline = document.getElementById("headline");

  const stage = (id, cls) => { const el = document.getElementById(id); if (el) el.className = cls; };

  let inflight = false;

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (inflight) return; // single-flight: one claude run at a time
    inflight = true;
    gen.disabled = true;
    gen.textContent = "Generating…";
    err.style.display = "none";
    finalwrap.style.display = "none";
    live.textContent = "";
    live.className = "stream caret";
    councillog.textContent = "";
    form.style.display = "none"; // hand off from the question flow to the live panel
    panel.style.display = "block";
    bar.style.width = "8%";
    stage("s-draft", "active");
    panel.scrollIntoView({ behavior: "smooth" });

    let res;
    try {
      res = await fetch("/post/generate", { method: "POST", body: new FormData(form) }).then((r) => r.json());
    } catch (_) {
      return fail("Couldn’t reach the server.");
    }
    if (!res || !res.job_id) return fail((res && res.error) || "Couldn’t start generation.");

    const runId = res.run_id;
    const es = new EventSource("/post/stream/" + res.job_id);

    es.onmessage = (ev) => {
      const d = JSON.parse(ev.data);
      switch (d.event) {
        case "token":
          if (d.stage === "draft") { live.textContent += d.text; bar.style.width = "40%"; }
          break;
        case "draft":
          if (d.status === "start") { stage("s-draft", "active"); }
          if (d.status === "done") { live.textContent = d.text || live.textContent; stage("s-draft", "done"); bar.style.width = "55%"; }
          break;
        case "council":
          if (d.status === "start") { stage("s-council", "active"); bar.style.width = "65%"; }
          if (d.status === "done") { stage("s-council", "done"); bar.style.width = "85%"; }
          break;
        case "council_pass":
          councillog.textContent = "Council pass " + d.n + (d.reason ? " — " + d.reason : "");
          break;
        case "score":
          if (d.status === "start") { stage("s-score", "active"); bar.style.width = "92%"; }
          if (d.status === "done") { stage("s-score", "done"); if (headline) headline.textContent = d.headline || ""; }
          break;
        case "done":
          showFinal(d.draft, d.headline, runId);
          break;
        case "error":
          fail(d.message || "Something went wrong.");
          break;
      }
    };

    es.addEventListener("end", (ev) => {
      es.close();
      reset();
      const d = JSON.parse(ev.data);
      if (d.status !== "done" && err.style.display === "none") {
        fail("Generation didn’t finish. Check /status (is Claude logged in?) and try again.");
      }
    });
    es.onerror = () => { es.close(); reset(); };

    function showFinal(draft, hl, rid) {
      live.className = "stream";
      bar.style.width = "100%";
      finalEl.textContent = draft;
      if (headline) headline.textContent = hl || "";
      document.getElementById("export").href = "/post/draft/" + rid + "/export";
      document.getElementById("permalink").href = "/post/draft/" + rid;
      finalwrap.style.display = "block";
      finalwrap.scrollIntoView({ behavior: "smooth" });
    }
  });

  function reset() {
    inflight = false;
    gen.disabled = false;
    gen.textContent = "Generate post";
  }
  function fail(msg) {
    err.style.display = "block";
    err.textContent = msg;
    live.className = "stream";
    form.style.display = ""; // let them edit the idea and try again
    reset();
  }

  // Final-view buttons (delegated so they work after the panel appears)
  document.addEventListener("click", async (e) => {
    if (e.target.id === "copy") {
      await navigator.clipboard.writeText(finalEl.innerText);
      e.target.textContent = "Copied ✓";
      setTimeout(() => { e.target.textContent = "Copy"; }, 1500);
    }
    if (e.target.id === "again") {
      panel.style.display = "none";
      finalwrap.style.display = "none";
      form.style.display = "";
      if (form._wizardReset) form._wizardReset();
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  });
})();
