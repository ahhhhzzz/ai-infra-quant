/* TASK-006E-Q / TASK-007D: Q and E calls require separate explicit user actions. */
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const node = (tag, value, className = "") => {
    const item = document.createElement(tag);
    item.textContent = value;
    item.className = className;
    return item;
  };
  const uuid = (value) => typeof value === "string" &&
    /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(value);
  const digest = (value) => typeof value === "string" && /^[0-9a-f]{64}$/.test(value);
  const view = window.PaqsQView;
  const details = view.technical;
  const fact = (label, value) => node("p", `${label}：${value ?? "未提供"}`);
  const status = (text, error = false) => {
    $("q-status").textContent = text; $("q-status").dataset.error = String(error);
  };
  const api = async (path, options = {}) => {
    const response = await fetch(`/api/v1/${path}`, {
      headers: { Accept: "application/json", "Content-Type": "application/json" },
      ...options,
    });
    const body = await response.json();
    if (!response.ok) throw new Error(body.detail || body.code || `HTTP ${response.status}`);
    return body;
  };
  let security = selectedSecurity;
  let selected = null;
  let navigation = 0;
  let selection = 0;
  let historyVersion = 0;
  let busyQ = false;
  let busyE = false;

  function validRecord(record, expectedSecurity) {
    return record && uuid(record.analysis_id) && record.security_id === expectedSecurity
      && digest(record.snapshot_hash) && record.payload
      && record.payload.market_snapshot?.snapshot_hash === record.snapshot_hash
      && record.payload.market_snapshot?.security?.security_id === expectedSecurity;
  }
  function controls() {
    $("q-analyze").disabled = !security || busyQ;
    $("q-history-refresh").disabled = !security;
    $("q-e-analyze").disabled = !selected || busyE;
  }
  function renderQ(record, source) {
    if (!record) {
      const empty = node("div", "", "empty-state");
      empty.append(node("strong", "尚未选择分析结果"), node("p", "查看已保存历史，或显式分析当前快照。"));
      $("q-result").replaceChildren(empty);
      $("q-basis").replaceChildren(node("p", "选择 Q 记录后查看市场背景、价格事件、候选形态、入场资格及条件式持有依据。", "empty-state"));
      return;
    }
    $("q-result").replaceChildren(view.summary(record, source));
    $("q-basis").replaceChildren(view.basis(record));
  }
  let eHistoryVersion = 0, compareVersion = 0;
  function setSelected(record, source = "查看历史 · 已保存快照") {
    selected = record; selection += 1; compareVersion += 1; eHistoryVersion += 1;
    renderQ(record, source);
    $("q-e-result").replaceChildren();
    $("q-e-options").replaceChildren(node("option", record ? "读取同快照记录…" : "请先选择 Q 记录"));
    $("q-e-options").disabled = true;
    $("q-e-read").disabled = true;
    $("q-e-refresh").disabled = !record;
    $("q-e-list-status").textContent = "";
    $("q-e-status").textContent = record ? `对照基准：${record.payload.market_snapshot.security.display_symbol || record.payload.market_snapshot.security.symbol} · Q 快照 ${view.time(record.payload.market_snapshot.as_of_timestamp)}。读取历史不调用模型。` : "请选择 Q 记录后读取对照或显式运行 E。";
    document.querySelectorAll("[data-q-analysis-id]").forEach(b => b.setAttribute("aria-current", String(b.dataset.qAnalysisId === record?.analysis_id)));
    controls();
    if (record) {
      document.querySelector(".analysis-panel").scrollTop = 0;
      void loadEHistory();
    }
  }
  async function loadEHistory() {
    if (!selected) return;
    const record = selected, intent = selection, nav = navigation, token = ++eHistoryVersion;
    $("q-e-list-status").textContent = "读取 E 历史…";
    $("q-e-options").disabled = true; $("q-e-read").disabled = true;
    try {
      const body = await api(`paqs-e/securities/${encodeURIComponent(record.security_id)}/narrative-results?limit=20`);
      if (token !== eHistoryVersion || intent !== selection || nav !== navigation) return;
      if (!Array.isArray(body.items) || body.items.some(e => !uuid(e.narrative_result_id) || !digest(e.snapshot_hash) || e.security_id !== record.security_id)) throw new Error("E 历史身份不一致");
      const matches = body.items.filter(e => e.snapshot_hash === record.snapshot_hash);
      $("q-e-options").replaceChildren(...(matches.length ? matches.map(e => {
        const option = node("option", `${view.time(e.created_at)} · ${e.model_id} · ${e.strategy_id}`); option.value = e.narrative_result_id; return option;
      }) : [node("option", "最近 20 条中无匹配记录")]));
      $("q-e-options").disabled = !matches.length; $("q-e-read").disabled = !matches.length;
      $("q-e-list-status").textContent = `最近 20 条 E 成功记录中有 ${matches.length} 条快照摘要匹配；读取对照时再校验完整身份。更早记录可用高级 ID 入口读取。`;
    } catch (error) {
      if (token === eHistoryVersion && intent === selection && nav === navigation) {
        $("q-e-options").replaceChildren(node("option", "列表读取失败"));
        $("q-e-list-status").textContent = `E 列表不可用：${error.message}。可重试读取或使用高级 ID 入口。`;
      }
    }
  }
  async function readRecord(id, expectedSecurity, nav, intent) {
    const record = await api(`paqs-q/analyses/${encodeURIComponent(id)}`);
    if (!validRecord(record, expectedSecurity) || record.analysis_id !== id)
      throw new Error("Q 历史身份或冻结快照不一致");
    if (nav === navigation && security?.id === expectedSecurity && intent === selection)
      setSelected(record);
  }
  async function loadHistory() {
    const token = ++historyVersion;
    const nav = navigation;
    const id = security?.id;
    $("q-history").replaceChildren();
    if (!id) return;
    $("q-history-status").textContent = "读取 Q 历史…";
    try {
      const body = await api(`paqs-q/securities/${encodeURIComponent(id)}/analyses?limit=20`);
      if (token !== historyVersion || nav !== navigation) return;
      if (!Array.isArray(body.items) || body.items.length > 20 || body.items.some((item) =>
        !uuid(item.analysis_id) || item.security_id !== id || !digest(item.snapshot_hash)))
        throw new Error("Q 历史身份不一致");
      const rows = body.items.map((item) => {
        const button = node("button", "", "history-row");
        button.type = "button";
        button.dataset.qAnalysisId = item.analysis_id;
        button.append(node("strong", `${view.state(item.status)} · ${view.time(item.created_at)}`),
          node("span", `${security?.display_symbol || "所选证券"} · 已保存快照`));
        button.addEventListener("click", () => {
          const intent = ++selection;
          status("读取所选 Q 冻结结果…");
          void readRecord(item.analysis_id, id, nav, intent).then(() => {
            if (intent === selection - 1 && nav === navigation) status("已读取 Q 冻结结果；未重新分析。");
          }).catch((error) => {
            if (nav === navigation && intent === selection) status(`Q 历史读取失败：${error.message}`, true);
          });
        });
        return button;
      });
      $("q-history").replaceChildren(...rows);
      $("q-history-status").textContent = rows.length ? `已读取 ${rows.length} 条 Q 历史；未重新分析。` : "尚无 Q 历史。";
    } catch (error) {
      if (token === historyVersion && nav === navigation) $("q-history-status").textContent = `Q 历史不可用：${error.message}`;
    }
  }
  async function compare(eResultId, qRecord, nav, intent) {
    const comparison = ++compareVersion;
    const body = await api(`paqs-q/analyses/${encodeURIComponent(qRecord.analysis_id)}/compare/${encodeURIComponent(eResultId)}`);
    if (comparison !== compareVersion || nav !== navigation || intent !== selection || selected?.analysis_id !== qRecord.analysis_id) return;
    const e = body.e_narrative || body.e || body.narrative_result;
    const q = body.q_analysis || body.q || qRecord;
    if (!e || e.narrative_result_id !== eResultId || typeof e.response_text !== "string"
      || !digest(e.snapshot_hash) || q.analysis_id !== qRecord.analysis_id
      || q.security_id !== qRecord.security_id || q.snapshot_hash !== qRecord.snapshot_hash
      || typeof body.same_snapshot !== "boolean") throw new Error("Q/E 对照身份不一致");
    const same = body.same_snapshot && e.snapshot_hash === qRecord.snapshot_hash;
    const banner = node("p", same ? "同一冻结快照 · 输出分别呈现" : "快照不同：不可直接比较；仅并排阅读", "note");
    const pair = node("div", "", "q-e-pair");
    const left = node("section", "");
    left.append(node("h3", "Q · 确定性规则事实"), view.summary(qRecord), details("Q 冻结输入覆盖与原始结果", qRecord));
    const right = node("section", "");
    right.append(node("h3", "E · Narrative 原文"),
      fact("模型 / 主策略 / 联网研究", `${e.model_id} / ${e.strategy_id} / ${e.web_research}`),
      details("E 冻结输入覆盖与来源", {
        timeframe_evidence_status: e.market_snapshot?.timeframe_evidence_status,
        source_coverage: e.market_snapshot?.source_coverage,
        adjustment_metadata: e.market_snapshot?.adjustment_metadata,
        data_quality: e.market_snapshot?.data_quality,
      }),
      details("E 附加研究原始引用", e.auxiliary_context || []),
      node("pre", e.response_text, "narrative-text"));
    pair.append(left, right);
    $("q-e-result").replaceChildren(banner, pair);
    $("q-e-status").textContent = same
      ? "Q/E 快照身份一致；E 原文未经结构化 Entry/Holder 提取。"
      : "快照身份不一致，不标记规则一致或分歧。";
  }
  $("q-analyze").addEventListener("click", async () => {
    if (!security || busyQ) return;
    const id = security.id, nav = navigation, intent = selection;
    busyQ = true; controls();
    status("正在显式采集并分析 Q 当前快照…");
    try {
      const record = await api("paqs-q/analyses", { method: "POST", body: JSON.stringify({ security_id: id }) });
      if (!validRecord(record, id)) throw new Error("Q 分析响应身份不一致");
      if (nav === navigation && security?.id === id) {
        if (intent === selection) { setSelected(record, "新分析 · 已保存快照"); window.AIQWorkbench.workspace("details"); }
        status(`Q 分析已保存：${view.state(record.status)}。`);
        void loadHistory();
      }
    } catch (error) {
      if (nav === navigation) status(`请求失败，未能确认新结果：${error.message}。已显示的旧记录不变；请检查历史后再决定是否重试。`, true);
    } finally { busyQ = false; controls(); }
  });
  $("q-history-refresh").addEventListener("click", () => { void loadHistory(); });
  $("q-e-analyze").addEventListener("click", async () => {
    if (!selected || busyE) return;
    const qRecord = selected, nav = navigation, intent = selection;
    const model = $("model-id").value, strategy = $("strategy-id").value;
    if (!model || !strategy) { $("q-e-status").textContent = "请选择 E 模型和主策略。"; return; }
    busyE = true; controls();
    $("q-e-status").textContent = "正在显式运行 E；不会自动重试或改取新快照…";
    try {
      const e = await api("paqs-e/narrative-analyses/from-q", {
        method: "POST",
        body: JSON.stringify({ q_analysis_id: qRecord.analysis_id, model_key: model,
          strategy_id: strategy, web_research: $("web-research").checked }),
      });
      if (!uuid(e.narrative_result_id) || e.snapshot_hash !== qRecord.snapshot_hash)
        throw new Error("E 返回的快照身份与 Q 不一致");
      if (nav === navigation && intent === selection) await compare(e.narrative_result_id, qRecord, nav, intent);
    } catch (error) {
      if (nav === navigation && intent === selection) $("q-e-status").textContent = `E 对照未能确认：${error.message}。请检查 E 历史或已知 Run；不会自动重试。`;
    } finally { busyE = false; controls(); }
  });
  $("q-e-refresh").addEventListener("click", () => { void loadEHistory(); });
  $("q-e-read").addEventListener("click", () => {
    if (!selected || !uuid($("q-e-options").value)) return;
    readComparison($("q-e-options").value);
  });
  function readComparison(id) {
    const record = selected, nav = navigation, intent = selection;
    if (!record) return;
    $("q-e-status").textContent = "读取既有对照；不会运行模型。";
    $("q-e-result").replaceChildren();
    void compare(id, record, nav, intent).catch(error => {
      if (nav === navigation && intent === selection) $("q-e-status").textContent = `对照读取失败：${error.message}`;
    });
  }
  $("q-e-known-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!selected) { $("q-e-status").textContent = "请先选择 Q 记录。"; return; }
    const id = $("q-e-known-id").value.trim();
    if (!uuid(id)) { $("q-e-status").textContent = "请输入合法 E Narrative Result UUID。"; return; }
    readComparison(id);
  });
  function onSecurity(item) {
    security = item;
    navigation += 1;
    historyVersion += 1;
    setSelected(null);
    $("q-history").replaceChildren();
    $("q-security").textContent = item ? `${item.display_symbol} · ${item.market}` : "请选择证券";
    status(item ? "可查看历史，或显式分析当前快照。" : "请选择证券");
    controls();
    if (item) void loadHistory();
  }
  document.addEventListener("security-selected", (event) => onSecurity(event.detail));
  if (security) onSecurity(security);
  else controls();
})();
