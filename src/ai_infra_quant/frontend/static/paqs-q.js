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
  const valueText = (value) => value == null ? "未提供" : typeof value === "object"
    ? JSON.stringify(value) : String(value);
  const exact = (value) => node("pre", JSON.stringify(value, null, 2));
  const fact = (label, value) => {
    const row = node("div", "", "paqs-q-fact");
    row.append(node("strong", label), node("span", valueText(value)));
    return row;
  };
  const details = (title, value) => {
    const section = document.createElement("details");
    section.append(node("summary", title), exact(value));
    return section;
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
  function renderQ(record) {
    const root = $("q-result");
    if (!record) {
      root.replaceChildren(node("p", "运行分析或选择历史记录。", "note"));
      return;
    }
    const payload = record.payload;
    const snapshot = payload.market_snapshot;
    const summary = node("div", "");
    summary.append(
      fact("分析记录", record.analysis_id),
      fact("冻结快照", record.snapshot_hash),
      fact("分析状态", record.status),
      fact("分析时点", snapshot.as_of_timestamp),
      fact("行情质量", snapshot.data_quality),
      fact("产品规则版本", payload.product_version),
      fact("复权及历史安全性", snapshot.adjustment_metadata),
      fact("W1/D1/M30 覆盖", snapshot.timeframe_evidence_status),
    );
    for (const [key, title] of [
      ["context", "Context 与结构"], ["event", "Event"], ["setup", "Setup、失效位与目标"],
      ["entry", "Entry · 确认评估与独立下一开盘资格"],
      ["holder", "若已持有 · 条件式 Holder"], ["diagnostics", "缺少证据与限制"],
      ["evidence_guidance", "补证据操作"],
    ]) {
      const section = details(title, payload[key] ?? { status: "UNAVAILABLE", reason: `${title} 未提供` });
      section.open = ["entry", "diagnostics", "evidence_guidance"].includes(key);
      summary.append(section);
    }
    summary.append(details("输入来源与各周期身份", {
      capture_source: payload.capture_source, q_inputs: payload.q_inputs,
    }));
    summary.append(details("冻结输入及完整审计结果", record));
    root.replaceChildren(summary);
  }
  function setSelected(record) {
    selected = record;
    selection += 1;
    renderQ(record);
    $("q-e-result").replaceChildren();
    $("q-e-status").textContent = record
      ? "已选择 Q 冻结结果。可显式运行 E 或按已知 E Result UUID 读取对照。"
      : "请选择 Q 记录后显式发起 E 或读取已有 E 结果。";
    controls();
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
    $("q-status").textContent = "读取 Q 历史…";
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
        button.append(node("strong", `${item.status} · ${item.created_at}`),
          node("span", `快照 ${item.snapshot_hash}`));
        button.addEventListener("click", () => {
          const intent = ++selection;
          $("q-status").textContent = "读取所选 Q 冻结结果…";
          void readRecord(item.analysis_id, id, nav, intent).then(() => {
            if (intent === selection - 1 && nav === navigation) $("q-status").textContent = "已读取 Q 冻结结果；未重新分析。";
          }).catch((error) => {
            if (nav === navigation) $("q-status").textContent = `Q 历史不可用：${error.message}`;
          });
        });
        return button;
      });
      $("q-history").replaceChildren(...rows);
      $("q-status").textContent = rows.length ? `已读取 ${rows.length} 条 Q 历史；未重新分析。` : "尚无 Q 历史。";
    } catch (error) {
      if (token === historyVersion && nav === navigation) $("q-status").textContent = `Q 历史不可用：${error.message}`;
    }
  }
  async function compare(eResultId, qRecord, nav, intent) {
    const body = await api(`paqs-q/analyses/${encodeURIComponent(qRecord.analysis_id)}/compare/${encodeURIComponent(eResultId)}`);
    if (nav !== navigation || intent !== selection || selected?.analysis_id !== qRecord.analysis_id) return;
    const e = body.e_narrative || body.e || body.narrative_result;
    const q = body.q_analysis || body.q || qRecord;
    if (!e || e.narrative_result_id !== eResultId || typeof e.response_text !== "string"
      || !digest(e.snapshot_hash) || q.analysis_id !== qRecord.analysis_id
      || q.security_id !== qRecord.security_id || q.snapshot_hash !== qRecord.snapshot_hash
      || typeof body.same_snapshot !== "boolean") throw new Error("Q/E 对照身份不一致");
    const same = body.same_snapshot && e.snapshot_hash === qRecord.snapshot_hash;
    const banner = node("p", same ? "同一冻结快照 · 输出分别呈现" : "快照不同：不可直接比较；仅并排阅读", "note");
    const pair = node("div", "", "paqs-q-pair");
    const left = node("section", "");
    left.append(node("h3", "Q · 确定性规则事实"), fact("快照", qRecord.snapshot_hash),
      details("Q 原始结果", q.payload || qRecord.payload));
    const right = node("section", "");
    right.append(node("h3", "E · Narrative 原文"), fact("快照", e.snapshot_hash),
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
    $("q-status").textContent = "正在显式采集并分析 Q 当前快照…";
    try {
      const record = await api("paqs-q/analyses", { method: "POST", body: JSON.stringify({ security_id: id }) });
      if (!validRecord(record, id)) throw new Error("Q 分析响应身份不一致");
      if (nav === navigation && security?.id === id) {
        if (intent === selection) setSelected(record);
        $("q-status").textContent = `Q 分析已保存：${record.status}；快照 ${record.snapshot_hash}。`;
        void loadHistory();
      }
    } catch (error) {
      if (nav === navigation) $("q-status").textContent = `Q 分析未能确认：${error.message}。请检查历史，避免重复请求。`;
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
  $("q-e-known-form").addEventListener("submit", (event) => {
    event.preventDefault();
    if (!selected) { $("q-e-status").textContent = "请先选择 Q 记录。"; return; }
    const id = $("q-e-known-id").value.trim();
    if (!uuid(id)) { $("q-e-status").textContent = "请输入合法 E Narrative Result UUID。"; return; }
    const qRecord = selected, nav = navigation, intent = selection;
    $("q-e-status").textContent = "读取既有 E 与所选 Q 的对照；不会运行模型。";
    void compare(id, qRecord, nav, intent).catch((error) => {
      if (nav === navigation && intent === selection) $("q-e-status").textContent = `对照读取失败：${error.message}`;
    });
  });
  function onSecurity(item) {
    security = item;
    navigation += 1;
    historyVersion += 1;
    setSelected(null);
    $("q-history").replaceChildren();
    $("q-security").textContent = item ? `${item.display_symbol} · ${item.market}` : "请选择证券";
    $("q-status").textContent = item ? "读取当前证券的 Q 历史…" : "请选择证券";
    controls();
    if (item) void loadHistory();
  }
  document.addEventListener("security-selected", (event) => onSecurity(event.detail));
  if (security) onSecurity(security);
  else controls();
})();
