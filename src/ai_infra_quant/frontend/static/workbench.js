/* Layout controls only: no network requests and no implicit analysis. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  function workspace(name) {
    for (const button of document.querySelectorAll("[data-workspace]")) {
      const active = button.dataset.workspace === name;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      $(button.getAttribute("aria-controls")).hidden = !active;
    }
  }
  function branch(name) {
    const q = name === "q";
    for (const value of ["q", "e"]) {
      $("branch-" + value).setAttribute("aria-selected", String(name === value));
      $("branch-" + value).tabIndex = name === value ? 0 : -1;
    }
    $("paqs-q-workbench").hidden = !q;
    $("q-basis").hidden = !q;
    $("e-actions").hidden = q;
    $("e-basis").hidden = q;
  }
  for (const button of document.querySelectorAll("[data-workspace]"))
    button.addEventListener("click", () => workspace(button.dataset.workspace));
  for (const name of ["q", "e"])
    $("branch-" + name).addEventListener("click", () => branch(name));
  for (const tablist of document.querySelectorAll(".branch-tabs,.workspace-tabs")) {
    tablist.addEventListener("keydown", (event) => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      const tabs = [...tablist.querySelectorAll('[role="tab"]')];
      const current = tabs.indexOf(document.activeElement);
      if (current < 0) return;
      event.preventDefault();
      const index = event.key === "Home" ? 0 : event.key === "End" ? tabs.length - 1
        : (current + (event.key === "ArrowRight" ? 1 : -1) + tabs.length) % tabs.length;
      tabs[index].click(); tabs[index].focus();
    });
  }
  for (const button of document.querySelectorAll("[data-open-history]"))
    button.addEventListener("click", () => { workspace("history"); $("tab-history").focus(); });
  $("q-e-settings").addEventListener("click", () => { branch("e"); $("model-id").focus(); });
  $("analyze-form").addEventListener("submit", () => { branch("e"); workspace("details"); });
  $("pane-history").addEventListener("click", (event) => {
    const button = event.target.closest("[data-narrative-result-id],[data-decision-id],[data-q-analysis-id],#latest-decision");
    if (!button) return;
    branch(button.dataset.qAnalysisId ? "q" : "e");
    workspace("details");
    if (button.dataset.qAnalysisId) {
      document.querySelector(".analysis-panel").scrollTop = 0;
      window.scrollTo({top: 0, behavior: "instant"});
    }
  });
  const filter = () => {
    const query = $("watchlist-search").value.trim().toLocaleLowerCase();
    const choices = [...$("security-selector").querySelectorAll(".security-option")];
    for (const choice of choices) choice.hidden = !choice.textContent.toLocaleLowerCase().includes(query);
    $("watch-search-empty").hidden = !choices.length || choices.some(choice => !choice.hidden);
  };
  $("watchlist-search").addEventListener("input", filter);
  new MutationObserver(filter).observe($("security-selector"), {childList: true});
  const selection = () => {
    const model = $("model-id").selectedOptions[0]?.textContent || "尚未选择模型";
    const strategy = $("strategy-id").selectedOptions[0]?.textContent || "尚未选择策略";
    $("q-e-selection").textContent = `将使用：${model} · ${strategy} · 联网研究${$("web-research").checked ? "开启" : "关闭"}。运行可能产生模型费用。`;
  };
  for (const name of ["model-id", "strategy-id", "web-research"]) $(name).addEventListener("change", selection);
  new MutationObserver(selection).observe($("model-id"), {childList: true});
  new MutationObserver(selection).observe($("strategy-id"), {childList: true});
  document.addEventListener("security-selected", () => { workspace("details"); });
  window.AIQWorkbench = Object.freeze({workspace, branch});
  selection();
})();
